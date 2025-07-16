from flask import Flask, request, jsonify
from flask_cors import CORS
from speech_processor import process_audio
from catalog_manager import CatalogManager
from ai_services import generate_description, translate_text
import config
import logging
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
catalog = CatalogManager()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/api/speech/process', methods=['POST'])
def handle_speech():
    """Endpoint for processing voice input"""
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            logger.warning("No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        language = request.form.get('language', 'en-IN')
        
        # Validate file
        if audio_file.filename == '':
            logger.warning("Empty audio file submitted")
            return jsonify({'error': 'No selected file'}), 400
            
        logger.info(f"Processing audio in language: {language}")
        
        # Process audio and get transcript
        text = process_audio(audio_file, language)
        logger.info(f"Speech processed successfully: {text[:50]}...")
        
        return jsonify({'text': text})
        
    except Exception as e:
        logger.error(f"Speech processing failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'Speech processing failed'}), 500

@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    """Endpoint for product CRUD operations"""
    try:
        if request.method == 'POST':
            # Add new product
            product_data = request.json
            
            # Validate required fields
            required_fields = ['name', 'category', 'price', 'stock', 'description']
            if not all(field in product_data for field in required_fields):
                missing = [f for f in required_fields if f not in product_data]
                logger.warning(f"Missing required fields: {missing}")
                return jsonify({'error': f'Missing required fields: {missing}'}), 400
                
            # Add metadata
            product_data['created_at'] = datetime.utcnow()
            product_data['last_updated'] = datetime.utcnow()
            
            # Insert product
            product_id = catalog.add_product(product_data)
            logger.info(f"Product added with ID: {product_id}")
            
            return jsonify({'product_id': product_id}), 201
            
        else:
            # Get all products
            seller_id = request.args.get('seller_id')
            products = catalog.get_products(seller_id)
            logger.info(f"Retrieved {len(products)} products")
            
            return jsonify(products)
            
    except Exception as e:
        logger.error(f"Product operation failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_product(product_id):
    """Endpoint for single product operations"""
    try:
        if request.method == 'GET':
            # Get single product
            product = catalog.get_product(product_id)
            if not product:
                logger.warning(f"Product not found: {product_id}")
                return jsonify({'error': 'Product not found'}), 404
                
            logger.info(f"Retrieved product: {product_id}")
            return jsonify(product)
            
        elif request.method == 'PUT':
            # Update product
            update_data = request.json
            update_data['last_updated'] = datetime.utcnow()
            
            updated = catalog.update_product(product_id, update_data)
            if not updated:
                logger.warning(f"Product update failed: {product_id}")
                return jsonify({'error': 'Product not found'}), 404
                
            logger.info(f"Product updated: {product_id}")
            return jsonify({'success': True})
            
        elif request.method == 'DELETE':
            # Delete product
            deleted = catalog.delete_product(product_id)
            if not deleted:
                logger.warning(f"Product delete failed: {product_id}")
                return jsonify({'error': 'Product not found'}), 404
                
            logger.info(f"Product deleted: {product_id}")
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Product operation failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/generate-description', methods=['POST'])
def handle_description_generation():
    """Endpoint for AI-generated product descriptions"""
    try:
        data = request.json
        
        # Validate input
        if 'product' not in data:
            logger.warning("No product data in description request")
            return jsonify({'error': 'Product data required'}), 400
            
        product_data = data['product']
        language = data.get('language', 'en')
        
        logger.info(f"Generating description for: {product_data.get('name', '')}")
        
        # Generate description
        description = generate_description(product_data, language)
        logger.info("Description generated successfully")
        
        return jsonify({'description': description})
        
    except Exception as e:
        logger.error(f"Description generation failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'Description generation failed'}), 500

@app.route('/api/ai/translate', methods=['POST'])
def handle_translation():
    """Endpoint for text translation"""
    try:
        data = request.json
        
        # Validate input
        required_fields = ['text', 'source_lang', 'target_lang']
        if not all(field in data for field in required_fields):
            missing = [f for f in required_fields if f not in data]
            logger.warning(f"Missing translation fields: {missing}")
            return jsonify({'error': f'Missing fields: {missing}'}), 400
            
        logger.info(
            f"Translating from {data['source_lang']} to {data['target_lang']}: "
            f"{data['text'][:30]}..."
        )
        
        # Perform translation
        translated = translate_text(
            data['text'],
            data['source_lang'],
            data['target_lang']
        )
        logger.info("Translation completed successfully")
        
        return jsonify({'translated_text': translated})
        
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'Translation failed'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': catalog.check_connection(),
            'speech': config.GOOGLE_CREDENTIALS_PATH is not None
        }
    })

if __name__ == '__main__':
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )