from flask import Flask, render_template, request, jsonify, send_file
import openpyxl
from openpyxl import Workbook
import os
import datetime
import re
import random
import json

app = Flask(__name__)

# Initialize data files
def init_data_files():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Product data
    product_filepath = 'data/artisandata.xlsx'
    if not os.path.exists(product_filepath):
        wb = Workbook()
        ws = wb.active
        ws.append(['ID', 'Product Name', 'Category', 'Description_EN', 'Description_TA', 'Quantity', 'Price', 'Timestamp'])
        wb.save(product_filepath)
    
    # Materials data
    materials_filepath = 'data/materials.json'
    if not os.path.exists(materials_filepath):
        with open(materials_filepath, 'w') as f:
            json.dump([], f)
    
    # Study resources
    study_filepath = 'data/study.json'
    if not os.path.exists(study_filepath):
        with open(study_filepath, 'w') as f:
            json.dump([], f)
    
    # Settings
    settings_filepath = 'data/settings.json'
    if not os.path.exists(settings_filepath):
        with open(settings_filepath, 'w') as f:
            json.dump({'language': 'EN', 'theme': 'light'}, f)
    
    return {
        'products': product_filepath,
        'materials': materials_filepath,
        'study': study_filepath,
        'settings': settings_filepath
    }

# [Keep all the existing functions: generate_description, predict_category, extract_price, extract_quantity]

# Existing product routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    files = init_data_files()
    wb = openpyxl.load_workbook(files['products'])
    ws = wb.active
    
    data = request.json
    product_name = data['name']
    quantity = data['quantity']
    price = data['price']
    
    category = predict_category(product_name)
    desc_en = generate_description(product_name, 'EN')
    desc_ta = generate_description(product_name, 'TA')
    
    new_id = ws.max_row
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append([
        new_id, 
        product_name, 
        category, 
        desc_en, 
        desc_ta, 
        quantity, 
        price, 
        timestamp
    ])
    
    wb.save(files['products'])
    return jsonify(success=True, id=new_id)

@app.route('/get_products')
def get_products():
    files = init_data_files()
    wb = openpyxl.load_workbook(files['products'])
    ws = wb.active
    
    products = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is not None:
            products.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'desc_en': row[3],
                'desc_ta': row[4],
                'quantity': row[5],
                'price': row[6],
                'timestamp': row[7]
            })
    
    return jsonify(products)

@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    files = init_data_files()
    wb = openpyxl.load_workbook(files['products'])
    ws = wb.active
    
    for idx, row in enumerate(ws.iter_rows(min_row=2), 2):
        if row[0].value == product_id:
            ws.delete_rows(idx)
            break
    
    wb.save(files['products'])
    return jsonify(success=True)

@app.route('/download_excel')
def download_excel():
    files = init_data_files()
    return send_file(files['products'], as_attachment=True)

# New Materials Section
@app.route('/get_materials')
def get_materials():
    files = init_data_files()
    with open(files['materials'], 'r') as f:
        materials = json.load(f)
    return jsonify(materials)

@app.route('/add_material', methods=['POST'])
def add_material():
    files = init_data_files()
    data = request.json
    
    with open(files['materials'], 'r') as f:
        materials = json.load(f)
    
    new_id = len(materials) + 1
    materials.append({
        'id': new_id,
        'name': data['name'],
        'quantity': data['quantity'],
        'unit': data['unit'],
        'last_restocked': datetime.datetime.now().strftime("%Y-%m-%d")
    })
    
    with open(files['materials'], 'w') as f:
        json.dump(materials, f)
    
    return jsonify(success=True)

# New Study Section
@app.route('/get_study_resources')
def get_study_resources():
    files = init_data_files()
    with open(files['study'], 'r') as f:
        resources = json.load(f)
    return jsonify(resources)

@app.route('/add_study_resource', methods=['POST'])
def add_study_resource():
    files = init_data_files()
    data = request.json
    
    with open(files['study'], 'r') as f:
        resources = json.load(f)
    
    new_id = len(resources) + 1
    resources.append({
        'id': new_id,
        'title': data['title'],
        'description': data['description'],
        'language': data['language'],
        'url': data['url'],
        'type': data['type']
    })
    
    with open(files['study'], 'w') as f:
        json.dump(resources, f)
    
    return jsonify(success=True)

# New AI Recommendations
@app.route('/get_recommendations')
def get_recommendations():
    files = init_data_files()
    wb = openpyxl.load_workbook(files['products'])
    ws = wb.active
    
    # Simple recommendation logic based on inventory
    low_stock = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row and row[5] is not None and row[5] < 5:  # Quantity < 5
            low_stock.append({
                'product': row[1],
                'current_stock': row[5],
                'recommendation': f"Restock {row[1]} (only {row[5]} left)"
            })
    
    # Add some AI-generated recommendations
    if len(low_stock) < 3:
        low_stock.extend([
            {
                'product': 'General',
                'current_stock': None,
                'recommendation': "Consider adding new product variations for the upcoming festival season"
            },
            {
                'product': 'General',
                'current_stock': None,
                'recommendation': "Promote your best-selling products on social media"
            }
        ])
    
    return jsonify(low_stock)

# Settings Management
@app.route('/get_settings')
def get_settings():
    files = init_data_files()
    with open(files['settings'], 'r') as f:
        settings = json.load(f)
    return jsonify(settings)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    files = init_data_files()
    data = request.json
    
    with open(files['settings'], 'w') as f:
        json.dump(data, f)
    
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)