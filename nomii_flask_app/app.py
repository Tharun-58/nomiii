from flask import Flask, render_template, request, jsonify, session, send_file
from datetime import datetime, timedelta
import pandas as pd
import os
import json
import re

# Corrected: Use __name__ instead of _name_
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['EXCEL_BASE'] = 'excels'
os.makedirs(app.config['EXCEL_BASE'], exist_ok=True)

# Create role-specific folders
roles = {
    'R': 'retailers',
    'S': 'suppliers',
    'D': 'delivery',
    'F': 'farmers',
    'A': 'artisans'   # Artisan folder
}

for role_folder in roles.values():
    os.makedirs(os.path.join(app.config['EXCEL_BASE'], role_folder), exist_ok=True)

# In-memory "database" for demonstration
users = {
    # Sample retailer user
    "NOMII-R-20231015104532": {
        "password": "StrongPass123!",
        "role": "R",
        "mobile": "9876543210",
        "aadhaarLast4": "1234",
        "gst": "22ABCDE1234F1Z5",
        "shopName": "Super Mart",
        "created_at": "2023-10-15 10:45:32"
    },
    # Sample farmer user
    "NOMII-F-20231016092015": {
        "password": "FarmerPass456!",
        "role": "F",
        "fullName": "Rajesh Kumar",
        "mobile": "9123456780",
        "aadhaarLast4": "5678",
        "village": "Green Fields",
        "landSize": "5 acres",
        "produce": "Rice, Wheat",
        "experience": "10",
        "regId": "",
        "created_at": "2023-10-16 09:20:15"
    },
    # Sample artisan user
    "NOMII-A-20231017123045": {
        "password": "ArtisanPass789!",
        "role": "A",
        "mobile": "8765432109",
        "aadhaarLast4": "2468",
        "craftType": "Pottery",
        "region": "Jaipur",
        "groupId": "JAIPOT01",
        "created_at": "2023-10-17 12:30:45"
    }
}

# Track login attempts and lockouts
login_attempts = {}

def validate_mobile(mobile):
    """Validate Indian mobile number"""
    return re.match(r'^[6-9]\d{9}$', mobile)

def validate_aadhaar_last4(aadhaar):
    """Validate last 4 digits of Aadhaar"""
    if not re.match(r'^\d{4}$', aadhaar):
        return False
    # Common sequences to reject
    invalid_sequences = ['0000', '1111', '1234', '4321', '2222', '3333']
    return aadhaar not in invalid_sequences

def validate_password(password):
    """Validate password strength"""
    # Corrected: Added a dot before the special character class to match a single character
    return re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$', password)

@app.route('/')
def index():
    """Render the main index page"""
    # This function expects an 'index.html' template to be present in a 'templates' folder.
    # If you don't have one, you might want to return a simple string or JSON.
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    """Handle user signup with Excel generation"""
    data = request.json
    role = data.get('role')
    
    # Validate role
    if not role or role not in roles:
        return jsonify({"success": False, "message": "Invalid role"}), 400
    
    # Common validations
    mobile = data.get('mobile')
    if not mobile or not validate_mobile(mobile):
        return jsonify({"success": False, "message": "Invalid mobile number (10 digits starting with 6-9)"}), 400
    
    password = data.get('password')
    # Corrected: Password validation function was slightly off, fixed it above.
    if not password or not validate_password(password):
        return jsonify({"success": False, "message": "Password must include uppercase, lowercase, number & special char, and be at least 8 characters long"}), 400
    
    # Role-specific validations
    if role == 'R':  # Retailer
        aadhaar = data.get('aadhaarLast4')
        if not aadhaar or not validate_aadhaar_last4(aadhaar):
            return jsonify({"success": False, "message": "Invalid last 4 Aadhaar digits"}), 400
        
        gst = data.get('gst')
        if not gst or not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gst, re.I):
            return jsonify({"success": False, "message": "Invalid GST format (e.g., 22ABCDE1234F1Z5)"}), 400
        
        shop_name = data.get('shopName')
        if not shop_name or len(shop_name) < 3:
            return jsonify({"success": False, "message": "Shop name needs 3+ characters"}), 400
    
    elif role == 'S':  # Supplier
        gst = data.get('gst')
        if not gst or not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gst, re.I):
            return jsonify({"success": False, "message": "Invalid GSTIN format"}), 400
        
        location = data.get('location')
        if not location or len(location) < 3:
            return jsonify({"success": False, "message": "Location needs 3+ characters"}), 400
    
    elif role == 'D':  # Delivery
        license_num = data.get('license')
        if not license_num or not re.match(r'^[A-Z]{2}\d{2,4}-\d{4}-\d{6,7}$', license_num, re.I):
            return jsonify({"success": False, "message": "Invalid license format"}), 400
        
        area = data.get('area')
        if not area or len(area) < 3:
            return jsonify({"success": False, "message": "Area needs 3+ characters"}), 400
    
    elif role == 'F':  # Farmer
        aadhaar = data.get('aadhaarLast4')
        if not aadhaar or not validate_aadhaar_last4(aadhaar):
            return jsonify({"success": False, "message": "Invalid last 4 Aadhaar digits"}), 400
        
        full_name = data.get('fullName')
        if not full_name or len(full_name) < 3 or not re.match(r'^[a-zA-Z\s]+$', full_name):
            return jsonify({"success": False, "message": "Full name must be at least 3 alphabetic characters"}), 400
        
        village = data.get('village')
        if not village or len(village) < 3:
            return jsonify({"success": False, "message": "Village/Area must be at least 3 characters"}), 400
        
        land_size = data.get('landSize')
        if not land_size:
            return jsonify({"success": False, "message": "Landholding size is required"}), 400
        
        produce = data.get('produce')
        if not produce:
            return jsonify({"success": False, "message": "Produce is required"}), 400
        
        experience = data.get('experience')
        if not experience or not re.match(r'^\d{1,2}$', experience) or int(experience) < 0 or int(experience) > 99:
            return jsonify({"success": False, "message": "Experience must be a number between 0 and 99"}), 400
    
    elif role == 'A':  # Artisan
        aadhaar = data.get('aadhaarLast4')
        if not aadhaar or not validate_aadhaar_last4(aadhaar):
            return jsonify({"success": False, "message": "Invalid last 4 Aadhaar digits"}), 400
        
        craft_type = data.get('craftType')
        if not craft_type or len(craft_type) < 3:
            return jsonify({"success": False, "message": "Craft type needs 3+ characters"}), 400
        
        region = data.get('region')
        if not region or len(region) < 3:
            return jsonify({"success": False, "message": "Region needs 3+ characters"}), 400
        
        group_id = data.get('groupId')
        if group_id and not re.match(r'^[a-zA-Z0-9]+$', group_id):
            return jsonify({"success": False, "message": "Group ID must be alphanumeric"}), 400
    
    # Check for duplicate mobile
    for existing_id, user_data in users.items():
        if user_data.get('mobile') == mobile:
            return jsonify({"success": False, "message": "Mobile number already registered"}), 400
        
        # For artisans, check craft + aadhaar combination
        if role == 'A' and user_data.get('role') == 'A':
            if (user_data.get('aadhaarLast4') == aadhaar and 
                user_data.get('craftType') == craft_type):
                return jsonify({"success": False, 
                                "message": "Aadhaar + Craft Type combination already exists"}), 400
    
    # Generate unique login ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    login_id = f"NOMII-{role}-{timestamp}"
    
    # Create user object
    user = {
        "login_id": login_id,
        "password": password,
        "role": role,
        "mobile": mobile,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add role-specific fields
    if role == 'R':  # Retailer
        user.update({
            "aadhaarLast4": aadhaar,
            "gst": gst,
            "shopName": shop_name
        })
    elif role == 'S':  # Supplier
        user.update({
            "gst": gst,
            "location": location
        })
    elif role == 'D':  # Delivery
        user.update({
            "license": license_num,
            "area": area
        })
    elif role == 'F':  # Farmer
        user.update({
            "fullName": full_name,
            "aadhaarLast4": aadhaar,
            "village": village,
            "landSize": land_size,
            "produce": produce,
            "experience": experience,
            "regId": data.get('regId', "")
        })
    elif role == 'A':  # Artisan
        user.update({
            "aadhaarLast4": aadhaar,
            "craftType": craft_type,
            "region": region,
            "groupId": group_id or ""
        })
    
    # Generate Excel file in role-specific folder
    excel_filename = f"{login_id}.xlsx"
    excel_path = os.path.join(app.config['EXCEL_BASE'], roles[role], excel_filename)
    
    df = pd.DataFrame([user])
    df.to_excel(excel_path, index=False)
    
    # Save user to database
    users[login_id] = user
    
    return jsonify({
        "success": True,
        "loginId": login_id,
        "excelFile": f"{roles[role]}/{excel_filename}",
        "message": "Account created successfully!"
    })

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download generated Excel file"""
    return send_file(
        os.path.join(app.config['EXCEL_BASE'], filename),
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/login', methods=['POST'])
def login():
    """Handle user login with security features"""
    data = request.json
    login_id = data.get('loginId')
    password = data.get('password')
    ip = request.remote_addr
    
    # Initialize attempt tracking for IP
    if ip not in login_attempts:
        login_attempts[ip] = {"count": 0, "lockout": None}
    
    # Check lockout status
    if login_attempts[ip]["lockout"]:
        if datetime.now() < login_attempts[ip]["lockout"]:
            remaining = (login_attempts[ip]["lockout"] - datetime.now()).seconds // 60
            return jsonify({
                "success": False,
                "message": f"Account locked. Try again in {remaining} minutes."
            }), 403
        else:
            # Reset after lockout expires
            login_attempts[ip] = {"count": 0, "lockout": None}
    
    # Validate credentials
    if login_id in users and users[login_id]["password"] == password:
        # Successful login
        login_attempts[ip] = {"count": 0, "lockout": None}
        session['user'] = login_id
        session.permanent = True
        
        # Determine dashboard redirect based on role
        role = users[login_id]["role"]
        return jsonify({
            "success": True,
            "role": role,
            "redirect": f"/dashboard?role={role}"
        })
    
    # Failed login
    login_attempts[ip]["count"] += 1
    
    # Check for lockout
    if login_attempts[ip]["count"] >= 5:
        lockout_time = datetime.now() + timedelta(minutes=5)
        login_attempts[ip]["lockout"] = lockout_time
        return jsonify({
            "success": False,
            "message": "Too many attempts. Account locked for 5 minutes."
        }), 403
    
    attempts_left = 5 - login_attempts[ip]["count"]
    return jsonify({
        "success": False,
        "message": f"Invalid credentials. {attempts_left} attempts remaining."
    }), 401

@app.route('/dashboard')
def dashboard():
    """User dashboard after successful login"""
    if 'user' not in session or session['user'] not in users:
        return "Unauthorized", 401
    
    user_id = session['user']
    user = users[user_id]
    role = user['role']
    
    # Render different dashboards based on role
    if role == 'R':
        return jsonify({
            "role": "Retailer",
            "name": user.get('shopName', ''),
            "mobile": user.get('mobile', ''),
            "gst": user.get('gst', '')
        })
    elif role == 'S':
        return jsonify({
            "role": "Supplier",
            "location": user.get('location', ''),
            "gst": user.get('gst', '')
        })
    elif role == 'D':
        return jsonify({
            "role": "Delivery Partner",
            "area": user.get('area', ''),
            "license": user.get('license', '')
        })
    elif role == 'F':
        return jsonify({
            "role": "Farmer",
            "name": user.get('fullName', ''),
            "village": user.get('village', ''),
            "produce": user.get('produce', '')
        })
    elif role == 'A':
        return jsonify({
            "role": "Artisan",
            "craft": user.get('craftType', ''),
            "region": user.get('region', ''),
            "groupId": user.get('groupId', '')
        })
    
    return jsonify({"error": "Invalid role"}), 400

# Corrected: Use __name__ instead of _name_
if __name__ == '__main__':
    app.run(debug=True, port=5000)
