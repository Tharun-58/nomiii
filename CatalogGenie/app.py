import os
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from fpdf import FPDF
import replicate
from PIL import Image
import io
import base64

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['EXPORT_FOLDER'] = 'exports'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

# Initialize Firebase
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logging.info("Firebase initialized successfully")
except Exception as e:
    logging.error(f"Firebase initialization failed: {str(e)}")
    db = None

# API Keys (In production, use environment variables)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'your-google-api-key')
REPLICATE_API_KEY = os.getenv('REPLICATE_API_KEY', 'your-replicate-api-key')
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY', 'your-deepl-api-key')

# Supported languages and models
SUPPORTED_LANGUAGES = ['en', 'ta', 'es', 'fr', 'ar', 'hi', 'pt']
STT_MODELS = {
    'google': 'https://speech.googleapis.com/v1/speech:recognize',
    'whisper': 'https://api.openai.com/v1/audio/transcriptions'
}
LLM_MODELS = {
    'gpt-4': 'https://api.openai.com/v1/chat/completions',
    'mistral': 'https://api.mistral.ai/v1/chat/completions'
}
IMAGE_MODELS = {
    'blip2': 'salesforce/blip-2:4b32258c42e9efd4288bb9910bc532a69727f9acd26aa08e175713a0a857a608',
    'gemini': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent'
}
TRANSLATION_SERVICES = {
    'nllb': 'https://api.transformers.huggingface.co/models/facebook/nllb-200-distilled-600M',
    'deepl': 'https://api-free.deepl.com/v2/translate',
    'google': 'https://translation.googleapis.com/language/translate/v2'
}

# Role-based taxonomies
TAXONOMY_MAP = {
    'farmer': {
        'amazon': ['Produce', 'Dairy & Eggs', 'Meat & Seafood'],
        'flipkart': ['Fruits & Vegetables', 'Dairy & Bakery', 'Meat & Eggs'],
        'shopify': ['Food & Beverage', 'Fresh Produce'],
        'gs1': ['Fruits', 'Vegetables', 'Dairy Products']
    },
    'artisan': {
        'amazon': ['Handmade', 'Arts & Crafts', 'Home Decor'],
        'flipkart': ['Handicrafts', 'Home Decor', 'Jewellery'],
        'shopify': ['Handmade', 'Craft Supplies', 'Home Goods'],
        'gs1': ['Handicrafts', 'Artistic Goods']
    },
    'retailer': {
        'amazon': ['Electronics', 'Home & Kitchen', 'Health & Personal Care'],
        'flipkart': ['Electronics', 'Home & Furniture', 'Beauty & Personal Care'],
        'shopify': ['Electronics', 'Home & Garden', 'Health & Beauty'],
        'gs1': ['Consumer Electronics', 'Home Appliances', 'Personal Care']
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/process-input', methods=['POST'])
def process_input():
    """Process text, voice, or image input and generate product listing"""
    try:
        data = request.json
        files = request.files
        
        # Get input parameters
        input_type = data.get('type', 'text')
        language = data.get('language', 'en')
        role = data.get('role', 'farmer')
        text = data.get('text', '')
        image_data = None
        
        # Handle different input types
        if input_type == 'voice' and 'audio' in files:
            audio_file = files['audio']
            text = speech_to_text(audio_file, language)
        elif input_type == 'image' and 'image' in files:
            image_file = files['image']
            image_data = process_image(image_file)
            text = image_data.get('description', '')
        
        # Generate listing with AI
        listing = generate_listing(text, role, language, image_data)
        
        # Translate if requested
        if data.get('translate_to'):
            translation = translate_text(
                listing['description'], 
                source_lang=language, 
                target_lang=data['translate_to']
            )
            listing['translation'] = translation
        
        return jsonify({
            'success': True,
            'listing': listing,
            'processed_text': text
        })
    
    except Exception as e:
        logging.error(f"Processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def speech_to_text(audio_file, language='en'):
    """Convert speech to text using Google Cloud STT or Whisper"""
    try:
        # Convert audio to base64
        audio_content = audio_file.read()
        audio_b64 = base64.b64encode(audio_content).decode('utf-8')
        
        # Prepare request based on language
        if language in ['en', 'es', 'fr']:
            # Use Google Cloud STT for major languages
            payload = {
                'config': {
                    'encoding': 'WEBM_OPUS',
                    'sampleRateHertz': 48000,
                    'languageCode': language,
                    'model': 'default'
                },
                'audio': {
                    'content': audio_b64
                }
            }
            headers = {'Authorization': f'Bearer {GOOGLE_API_KEY}'}
            response = requests.post(STT_MODELS['google'], json=payload, headers=headers)
            results = response.json().get('results', [])
            return results[0]['alternatives'][0]['transcript'] if results else ''
        
        else:
            # Use Whisper for other languages
            files = {'file': audio_file}
            data = {'model': 'whisper-1', 'language': language}
            headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
            response = requests.post(STT_MODELS['whisper'], files=files, data=data, headers=headers)
            return response.json().get('text', '')
    
    except Exception as e:
        logging.error(f"Speech-to-text error: {str(e)}")
        return ""

def process_image(image_file):
    """Extract product information from image using BLIP2 or Gemini"""
    try:
        # Save image temporarily
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{uuid.uuid4()}.jpg')
        image_file.save(img_path)
        
        # Use BLIP2 via Replicate
        output = replicate.run(
            IMAGE_MODELS['blip2'],
            input={'image': open(img_path, 'rb')}
        )
        
        # Basic image analysis
        img = Image.open(img_path)
        width, height = img.size
        dominant_color = get_dominant_color(img)
        
        return {
            'description': output,
            'dimensions': f"{width}x{height}",
            'dominant_color': dominant_color,
            'format': img.format
        }
    
    except Exception as e:
        logging.error(f"Image processing error: {str(e)}")
        return {'description': 'Image processing failed'}

def get_dominant_color(img):
    """Get dominant color from image (simplified)"""
    img = img.convert('RGB')
    img = img.resize((1, 1))
    return img.getpixel((0, 0))

def generate_listing(text, role, language='en', image_data=None):
    """Generate product listing using LLM"""
    try:
        # Prepare taxonomy prompt
        taxonomy = "\n".join(
            f"- {platform}: {', '.join(categories)}"
            for platform, categories in TAXONOMY_MAP[role].items()
        )
        
        # Prepare prompt with role-specific instructions
        prompt = f"""
        You are CatalogGenie, an AI assistant helping {role}s create product listings. 
        Generate a comprehensive product listing based on the following input:
        
        USER INPUT: {text}
        
        ROLE: {role}
        LANGUAGE: {language}
        
        Include these elements in your response as JSON:
        1. title: SEO-optimized product title
        2. description: Detailed product description with benefits (150-250 words)
        3. categories: Array of 3-5 relevant categories from major taxonomies
        4. attributes: Array of key product attributes (size, weight, material, etc.)
        5. keywords: Array of 5-7 SEO keywords
        
        Use the following taxonomy standards as reference:
        {taxonomy}
        
        Important guidelines:
        - Use {language} language with appropriate cultural nuances
        - For farmers: Highlight freshness, organic status, certifications
        - For artisans: Emphasize craftsmanship, materials, uniqueness
        - For retailers: Focus on features, specifications, brand value
        - Make descriptions persuasive yet factual
        - Include relevant units (kg, g, cm, etc.) in attributes
        """
        
        # Add image context if available
        if image_data:
            prompt += f"\n\nIMAGE CONTEXT: {image_data['description']}"
        
        # Call LLM (GPT-4 as default)
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'gpt-4-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'response_format': {'type': 'json_object'},
            'temperature': 0.7
        }
        response = requests.post(LLM_MODELS['gpt-4'], json=payload, headers=headers)
        result = response.json()
        
        # Parse and return listing
        listing = json.loads(result['choices'][0]['message']['content'])
        return listing
    
    except Exception as e:
        logging.error(f"Listing generation error: {str(e)}")
        return {
            'title': 'Listing Generation Failed',
            'description': 'Please try again or provide more details',
            'categories': [],
            'attributes': [],
            'keywords': []
        }

def translate_text(text, source_lang='en', target_lang='es'):
    """Translate text between languages using DeepL or Google"""
    try:
        # Use DeepL for quality translation
        params = {
            'auth_key': DEEPL_API_KEY,
            'text': text,
            'source_lang': source_lang.upper(),
            'target_lang': target_lang.upper()
        }
        response = requests.post(TRANSLATION_SERVICES['deepl'], data=params)
        return response.json()['translations'][0]['text']
    
    except:
        # Fallback to Google Translate
        params = {
            'q': text,
            'source': source_lang,
            'target': target_lang,
            'key': GOOGLE_API_KEY
        }
        response = requests.post(TRANSLATION_SERVICES['google'], params=params)
        return response.json()['data']['translations'][0]['translatedText']

@app.route('/api/save-product', methods=['POST'])
def save_product():
    """Save product to inventory with cloud sync"""
    try:
        data = request.json
        user_id = data.get('user_id', 'demo-user')
        role = data.get('role', 'farmer')
        product = data['product']
        
        # Add metadata
        product['id'] = str(uuid.uuid4())
        product['created_at'] = datetime.utcnow().isoformat()
        product['last_updated'] = product['created_at']
        product['stock'] = data.get('stock', 100)
        product['role'] = role
        
        # Save to Firebase
        if db:
            doc_ref = db.collection('inventory').document(user_id)
            doc_ref.set({product['id']: product}, merge=True)
        
        return jsonify({'success': True, 'product_id': product['id']})
    
    except Exception as e:
        logging.error(f"Save product error: {str(e)}")
        return jsonify({'success': False}), 500

@app.route('/api/get-inventory', methods=['GET'])
def get_inventory():
    """Retrieve user's inventory from cloud or local cache"""
    try:
        user_id = request.args.get('user_id', 'demo-user')
        
        # Try to get from Firebase
        inventory = {}
        if db:
            doc = db.collection('inventory').document(user_id).get()
            if doc.exists:
                inventory = doc.to_dict()
        
        return jsonify({
            'success': True,
            'inventory': inventory
        })
    
    except Exception as e:
        logging.error(f"Inventory retrieval error: {str(e)}")
        return jsonify({'success': False}), 500

@app.route('/api/export-catalog', methods=['POST'])
def export_catalog():
    """Export catalog in specified format"""
    try:
        data = request.json
        format = data.get('format', 'pdf')
        products = data.get('products', [])
        role = data.get('role', 'farmer')
        
        if not products:
            return jsonify({'success': False, 'error': 'No products to export'}), 400
        
        filename = f"catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == 'pdf':
            # Generate PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Add title
            pdf.cell(200, 10, txt=f"{role.capitalize()} Product Catalog", ln=True, align='C')
            pdf.ln(10)
            
            # Add products
            for i, product in enumerate(products):
                pdf.set_font("Arial", 'B', size=12)
                pdf.cell(200, 10, txt=f"{i+1}. {product['title']}", ln=True)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 8, txt=product['description'])
                pdf.cell(0, 8, txt=f"Stock: {product.get('stock', 'N/A')}", ln=True)
                pdf.ln(5)
            
            filepath = os.path.join(app.config['EXPORT_FOLDER'], f"{filename}.pdf")
            pdf.output(filepath)
            return send_file(filepath, as_attachment=True)
        
        elif format == 'csv':
            # Prepare CSV data
            csv_data = []
            for product in products:
                csv_data.append({
                    'ID': product.get('id', ''),
                    'Title': product['title'],
                    'Description': product['description'],
                    'Categories': ', '.join(product.get('categories', [])),
                    'Attributes': ', '.join(product.get('attributes', [])),
                    'Stock': product.get('stock', ''),
                    'Created At': product.get('created_at', '')
                })
            
            df = pd.DataFrame(csv_data)
            filepath = os.path.join(app.config['EXPORT_FOLDER'], f"{filename}.csv")
            df.to_csv(filepath, index=False)
            return send_file(filepath, as_attachment=True)
        
        elif format == 'excel':
            # Prepare Excel data
            excel_data = []
            for product in products:
                excel_data.append({
                    'ID': product.get('id', ''),
                    'Title': product['title'],
                    'Description': product['description'],
                    'Categories': ', '.join(product.get('categories', [])),
                    'Attributes': ', '.join(product.get('attributes', [])),
                    'Stock': product.get('stock', ''),
                    'Created At': product.get('created_at', '')
                })
            
            df = pd.DataFrame(excel_data)
            filepath = os.path.join(app.config['EXPORT_FOLDER'], f"{filename}.xlsx")
            df.to_excel(filepath, index=False)
            return send_file(filepath, as_attachment=True)
        
        else:
            return jsonify({'success': False, 'error': 'Invalid format'}), 400
    
    except Exception as e:
        logging.error(f"Export error: {str(e)}")
        return jsonify({'success': False}), 500

@app.route('/api/update-inventory', methods=['POST'])
def update_inventory():
    """Update product stock levels"""
    try:
        data = request.json
        user_id = data.get('user_id', 'demo-user')
        updates = data.get('updates', {})
        
        # Update Firebase
        if db:
            doc_ref = db.collection('inventory').document(user_id)
            for product_id, stock in updates.items():
                doc_ref.update({f"{product_id}.stock": stock})
        
        return jsonify({'success': True})
    
    except Exception as e:
        logging.error(f"Inventory update error: {str(e)}")
        return jsonify({'success': False}), 500

@app.route('/api/check-stock-alerts', methods=['GET'])
def check_stock_alerts():
    """Check for low stock items"""
    try:
        user_id = request.args.get('user_id', 'demo-user')
        threshold = int(request.args.get('threshold', 10))
        
        # Get inventory
        inventory = {}
        if db:
            doc = db.collection('inventory').document(user_id).get()
            if doc.exists:
                inventory = doc.to_dict()
        
        # Find low stock items
        low_stock = []
        for product_id, product in inventory.items():
            if product.get('stock', 0) < threshold:
                low_stock.append({
                    'id': product_id,
                    'title': product['title'],
                    'current_stock': product.get('stock', 0)
                })
        
        return jsonify({
            'success': True,
            'low_stock': low_stock,
            'threshold': threshold
        })
    
    except Exception as e:
        logging.error(f"Stock alert error: {str(e)}")
        return jsonify({'success': False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)