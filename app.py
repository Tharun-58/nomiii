import os
import uuid
from datetime import datetime
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash
import plotly.express as px
from werkzeug.security import generate_password_hash, check_password_hash
import speech_recognition as sr
import re


app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['EXCEL_FOLDER'] = 'excel_data'
app.config['PASSWORD_FILE'] = 'passwords_backup.xlsx'

# Create Excel directory if not exists
os.makedirs(app.config['EXCEL_FOLDER'], exist_ok=True)

# Initialize Excel files with headers
def init_excel_files():
    files = {
        'products.xlsx': ['Product ID', 'User ID', 'Name', 'Category', 'Price', 'Stock', 
                         'Description', 'Image URL', 'Status', 'Created Date', 'Last Updated'],
        'orders.xlsx': ['Order ID', 'Retailer Name', 'Email', 'Product ID', 'Product Name', 
                       'Quantity', 'Price', 'Status', 'Ordered Date', 'Supplier ID'],
        'deliveries.xlsx': ['Delivery ID', 'Order ID', 'Delivery Partner', 
                           'Status', 'Dispatched Date', 'Delivered Date', 'Supplier ID'],
        'earnings.xlsx': ['Earning ID', 'Order ID', 'Amount', 'Paid', 'Date', 'Supplier ID'],
        'users.xlsx': ['User ID', 'Username', 'Password', 'Company', 'Email', 
                       'Address', 'Phone', 'Business Type', 'Registration Date', 'Role'],
        'passwords_backup.xlsx': ['User ID', 'Username', 'Plain Password']
    }
    
    for filename, columns in files.items():
        path = os.path.join(app.config['EXCEL_FOLDER'], filename)
        if not os.path.exists(path):
            pd.DataFrame(columns=columns).to_excel(path, index=False)
        else:
            # If file exists, check if all columns are present
            df = pd.read_excel(path)
            for col in columns:
                if col not in df.columns:
                    df[col] = '' if col != 'Role' else 'supplier'  # Default role
            df.to_excel(path, index=False)
init_excel_files()
def read_excel(filename):
    path = os.path.join(app.config['EXCEL_FOLDER'], filename)
    return pd.read_excel(path)

def write_excel(filename, df):
    path = os.path.join(app.config['EXCEL_FOLDER'], filename)
    df.to_excel(path, index=False)

# Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = read_excel('users.xlsx')
        user = users[users['Username'] == username]
        
        if not user.empty and check_password_hash(user.iloc[0]['Password'], password):
            session['user_id'] = user.iloc[0]['User ID']
            session['username'] = username
            session['company'] = user.iloc[0]['Company']
            # Safely get role with default 'supplier' if not exists
            session['role'] = user.iloc[0].get('Role', 'supplier')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')
def update_existing_users():
    users_path = os.path.join(app.config['EXCEL_FOLDER'], 'users.xlsx')
    if os.path.exists(users_path):
        users = pd.read_excel(users_path)
        if 'Role' not in users.columns:
            users['Role'] = 'supplier'  # Set default role for existing users
            # Set first user as admin (you can change the condition as needed)
            if not users.empty:
                users.at[0, 'Role'] = 'admin'
            users.to_excel(users_path, index=False)

# Run this once
update_existing_users()
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Registration with Role
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = read_excel('users.xlsx')
        passwords_backup = read_excel('passwords_backup.xlsx')
        
        if not users[users['Username'] == request.form['username']].empty:
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))
        
        user_id = str(uuid.uuid4())
        plain_password = request.form['password']
        
        new_user = {
            'User ID': user_id,
            'Username': request.form['username'],
            'Password': generate_password_hash(plain_password),
            'Company': request.form['company'],
            'Email': request.form['email'],
            'Address': request.form['address'],
            'Phone': request.form['phone'],
            'Business Type': request.form['business_type'],
            'Registration Date': datetime.now().strftime('%Y-%m-%d'),
            'Role': 'supplier'  # Default role
        }
        
        password_backup = {
            'User ID': user_id,
            'Username': request.form['username'],
            'Plain Password': plain_password
        }
        
        updated_users = pd.concat([users, pd.DataFrame([new_user])], ignore_index=True)
        write_excel('users.xlsx', updated_users)
        
        updated_passwords = pd.concat([passwords_backup, pd.DataFrame([password_backup])], ignore_index=True)
        write_excel('passwords_backup.xlsx', updated_passwords)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Dashboard with Role Check
@app.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role', 'supplier')

    products = read_excel('products.xlsx')
    orders = read_excel('orders.xlsx')
    earnings = read_excel('earnings.xlsx')
    deliveries = read_excel('deliveries.xlsx')

    # Products count - session/role based
    if role == 'admin':
        user_products = products
    else:
        user_products = products[products['User ID'] == user_id]
    total_products = len(user_products)

    # Orders count (global)
    total_orders = len(orders)
    pending_orders = len(orders[orders['Status'] == 'Pending']) if not orders.empty else 0

    # Total earnings (global)
    if not earnings.empty:
        earnings['Amount'] = pd.to_numeric(earnings['Amount'], errors='coerce').fillna(0)
        total_earnings = earnings['Amount'].sum()
    else:
        total_earnings = 0

    # Stock Alerts (global stock check)
     # Stock Alerts - comprehensive check
    committed_orders = orders[orders['Status'] == 'Pending']
    deliveries_merged = deliveries.merge(
        orders[['Order ID', 'Product ID', 'Quantity']],
        on='Order ID',
        how='left')

    committed_deliveries = deliveries_merged[deliveries_merged['Status'] != 'Delivered']
    orders_usage = committed_orders.groupby('Product ID')['Quantity'].sum()
    deliveries_usage = committed_deliveries.groupby('Product ID')['Quantity'].sum()
    earnings_merged = earnings.merge(orders[['Order ID', 'Product ID']], on='Order ID', how='left')
    earnings_usage = earnings_merged.groupby('Product ID')['Amount'].count()  # Or another logic if applicable

# Total stock usage (orders + deliveries + earnings if needed)
    stock_usage = orders_usage.add(deliveries_usage, fill_value=0).add(earnings_usage, fill_value=0)
    products = products.set_index('Product ID')
    products['Committed'] = stock_usage
    products['Committed'] = products['Committed'].fillna(0)
    products['Stock After Commitment'] = products['Stock'] - products['Committed']
    low_stock_alerts = products[products['Stock After Commitment'] <= 10].reset_index()


    top_products = orders.groupby('Product ID').agg({
    'Quantity': 'sum',
    'Product Name': 'first'
}).sort_values(by='Quantity', ascending=False).head(5).reset_index()


    # Order Trends (global)
    orders['Ordered Date'] = pd.to_datetime(orders['Ordered Date'], errors='coerce')
    recent_orders = orders[orders['Ordered Date'] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
    daily_orders = recent_orders.groupby(recent_orders['Ordered Date'].dt.date).size().reset_index(name='Orders')

    import plotly.express as px
    orders_graph = None
    if not daily_orders.empty:
        fig = px.line(daily_orders, x='Ordered Date', y='Orders', title='Order Trends (Last 30 Days)')
        orders_graph = fig.to_html(full_html=False)

    return render_template('dashboard.html',
                           total_products=total_products,
                           total_orders=total_orders,
                           pending_orders=pending_orders,
                           total_earnings=total_earnings,
                           low_stock_alerts=low_stock_alerts.to_dict('records'),
                           top_products=top_products.to_dict('records'),
                           orders_graph=orders_graph)

# Product Management with Role Check
@app.route('/products')
def view_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    role = session.get('role', 'supplier')
    products = read_excel('products.xlsx')
    
    if role == 'admin':
        user_products = products
    else:
        user_products = products[products['User ID'] == user_id]
    
    return render_template('view_products.html', products=user_products.to_dict('records'), role=role)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role', 'supplier')
    if role not in ['admin', 'supplier']:
        flash('You do not have permission to add products', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        products = read_excel('products.xlsx')
        
        new_product = {
            'Product ID': str(uuid.uuid4()),
            'User ID': user_id,
            'Name': request.form['name'],
            'Category': request.form['category'],
            'Price': float(request.form['price']),
            'Stock': int(request.form['stock']),
            'Description': request.form['description'],
            'Image URL': request.form['image_url'] or 'https://via.placeholder.com/150',
            'Status': 'Active',
            'Created Date': datetime.now().strftime('%Y-%m-%d'),
            'Last Updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        updated_products = pd.concat([products, pd.DataFrame([new_product])], ignore_index=True)
        write_excel('products.xlsx', updated_products)
        flash('Product added successfully!', 'success')
        return redirect(url_for('view_products'))
    
    return render_template('add_product.html')

@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    role = session.get('role', 'supplier')
    products = read_excel('products.xlsx')
    
    if role == 'admin':
        product = products[products['Product ID'] == product_id]
    else:
        product = products[(products['Product ID'] == product_id) & (products['User ID'] == user_id)]
    
    if product.empty:
        flash('Product not found or no permission', 'danger')
        return redirect(url_for('view_products'))
    
    if request.method == 'POST':
        idx = product.index[0]
        products.at[idx, 'Name'] = request.form['name']
        products.at[idx, 'Category'] = request.form['category']
        products.at[idx, 'Price'] = float(request.form['price'])
        products.at[idx, 'Stock'] = int(request.form['stock'])
        products.at[idx, 'Description'] = request.form['description']
        products.at[idx, 'Image URL'] = request.form['image_url']
        products.at[idx, 'Status'] = request.form['status']
        products.at[idx, 'Last Updated'] = datetime.now().strftime('%Y-%m-%d')
        
        write_excel('products.xlsx', products)
        flash('Product updated successfully!', 'success')
        return redirect(url_for('view_products'))
    
    return render_template('edit_product.html', product=product.iloc[0].to_dict())

@app.route('/delete_product/<product_id>')
def delete_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    role = session.get('role', 'supplier')
    products = read_excel('products.xlsx')
    
    if role == 'admin':
        product = products[products['Product ID'] == product_id]
    else:
        product = products[(products['Product ID'] == product_id) & (products['User ID'] == user_id)]
    
    if not product.empty:
        products = products.drop(product.index)
        write_excel('products.xlsx', products)
        flash('Product deleted successfully!', 'success')
    else:
        flash('Product not found or no permission', 'danger')
    
    return redirect(url_for('view_products'))

# Order Management
@app.route('/orders')
def view_orders():
    orders_df = read_excel('orders.xlsx')

    if orders_df.empty:
        flash('No orders found.', 'info')
        return render_template('view_orders.html', orders=[])

    # No filtering, display all data
    orders_data = []
    for _, row in orders_df.iterrows():
        order = {
            'Order ID': str(row.get('Order ID', 'N/A')),
            'Retailer Name': str(row.get('Retailer Name', 'N/A')),
            'Email': str(row.get('Email', 'N/A')),
            'Product Name': str(row.get('Product Name', 'N/A')),
            'Quantity': int(row['Quantity']) if pd.notna(row.get('Quantity')) else 0,
            'Price': float(row['Price']) if pd.notna(row.get('Price')) else 0.0,
            'Status': str(row.get('Status', 'Pending')).capitalize(),
            'Ordered Date': str(row.get('Ordered Date', 'N/A')),
            'Supplier ID': str(row.get('Supplier ID', 'N/A')),
            'Product ID': str(row.get('Product ID', 'N/A'))
        }
        orders_data.append(order)

    return render_template('view_orders.html', orders=orders_data)


@app.route('/update_order_status/<order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    orders = read_excel('orders.xlsx')
    order = orders[(orders['Order ID'] == order_id) & (orders['Supplier ID'] == user_id)]
    
    if not order.empty:
        idx = order.index[0]
        orders.at[idx, 'Status'] = request.form['status']
        write_excel('orders.xlsx', orders)
        flash('Order status updated!', 'success')
    
    return redirect(url_for('view_orders'))

# Delivery Management
from datetime import datetime

# Add this function to create datetime formatting filter
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value is None or str(value).lower() == 'nan' or str(value).lower() == 'nat':
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(format)

# Delivery Management
@app.route('/view_deliveries')
def view_deliveries():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    deliveries = read_excel('deliveries.xlsx')
    
    if not deliveries.empty:
        orders = read_excel('orders.xlsx')
        deliveries = deliveries.merge(
            orders[['Order ID', 'Retailer Name', 'Product Name', 'Quantity']], 
            on='Order ID', 
            how='left'
        )
    
    return render_template('view_deliveries.html', deliveries=deliveries.to_dict('records'))


@app.route('/update_delivery/<delivery_id>', methods=['POST'])
def update_delivery(delivery_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    deliveries = read_excel('deliveries.xlsx')
    delivery = deliveries[deliveries['Delivery ID'] == delivery_id]
    
    if not delivery.empty:
        idx = delivery.index[0]
        deliveries.at[idx, 'Status'] = request.form['status']
        deliveries.at[idx, 'Delivery Partner'] = request.form['partner']
        if request.form['status'] == 'Delivered':
            deliveries.at[idx, 'Delivered Date'] = datetime.now().strftime('%Y-%m-%d')
        write_excel('deliveries.xlsx', deliveries)
        flash('Delivery updated!', 'success')
    else:
        flash('Delivery not found!', 'danger')
    
    return redirect(url_for('view_deliveries'))

@app.route('/earnings')
def view_earnings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    earnings = read_excel('earnings.xlsx')
    
    if not earnings.empty:
        orders = read_excel('orders.xlsx')
        earnings = earnings.merge(
            orders[['Order ID', 'Retailer Name', 'Product Name']], 
            on='Order ID', 
            how='left'
        )
    
    if not earnings.empty:
        earnings['Date'] = pd.to_datetime(earnings['Date'], errors='coerce')
        earnings = earnings.dropna(subset=['Date'])  # Drop rows where Date conversion failed
        daily_earnings = earnings.resample('D', on='Date')['Amount'].sum().reset_index()
        fig = px.line(daily_earnings, x='Date', y='Amount', 
                     title='Daily Earnings Trend', markers=True)
        earnings_graph = fig.to_html(full_html=False)
    else:
        earnings_graph = "<p>No earnings data available</p>"

    total_earnings = earnings['Amount'].sum() if not earnings.empty else 0
    paid_earnings = earnings[earnings['Paid'] == 'Yes']['Amount'].sum() if not earnings.empty else 0

    return render_template('view_earnings.html', 
                          earnings=earnings.to_dict('records'),
                          total_earnings=total_earnings,
                          paid_earnings=paid_earnings,
                          earnings_graph=earnings_graph)

# Analytics
@app.route('/analytics')
def view_analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    products = read_excel('products.xlsx')
    orders = read_excel('orders.xlsx')
    
    user_products = products[products['User ID'] == user_id]
    user_orders = orders[orders['Supplier ID'] == user_id]

    # Calculate summary statistics
    summary_stats = {
        'total_products': len(user_products),
        'low_stock_items': len(user_products[user_products['Stock'] < 10]),  # Assuming low stock is < 10
        'monthly_sales': user_orders['Quantity'].sum() * user_orders['Price'].mean() if not user_orders.empty else 0,
        'top_category': user_products['Category'].value_counts().idxmax() if not user_products.empty else 'N/A'
    }

    # Generate charts
    category_chart = "<p>No product data available</p>"
    if not user_products.empty:
        category_fig = px.pie(user_products, names='Category', title='Product Categories')
        category_chart = category_fig.to_html(full_html=False)
    
    stock_chart = "<p>No product data available</p>"
    if not user_products.empty:
        stock_fig = px.line(user_products.sort_values('Stock'), 
                         x='Name', y='Stock', 
                         title='Product Stock Levels', markers=True)
        stock_chart = stock_fig.to_html(full_html=False)
    
    sales_chart = "<p>No order data available</p>"
    recent_activities = []
    top_products = []
    
    if not user_orders.empty:
        # Sales chart
        user_orders['Ordered Date'] = pd.to_datetime(user_orders['Ordered Date'])
        daily_sales = user_orders.resample('D', on='Ordered Date')['Quantity'].sum().reset_index()
        sales_fig = px.line(daily_sales, x='Ordered Date', y='Quantity', 
                         title='Daily Sales Trend', markers=True)
        sales_chart = sales_fig.to_html(full_html=False)
        
        # Recent activities (last 5 orders)
        recent_activities = [{
            'message': f"Order #{row['Order ID']} for {row['Quantity']} items",
            'timestamp': row['Ordered Date'],
            'user': 'Customer'
        } for _, row in user_orders.sort_values('Ordered Date', ascending=False).head(5).iterrows()]
        
        # Top selling products
        top_products_df = user_orders.groupby('Product Name').agg({
            'Quantity': 'sum',
            'Price': 'mean'
        }).reset_index()
        top_products_df['Revenue'] = top_products_df['Quantity'] * top_products_df['Price']
        total_sales = top_products_df['Revenue'].sum()
        top_products = [{
            'name': row['Product Name'],
            'sales_count': row['Quantity'],
            'revenue': row['Revenue'],
            'percentage': round((row['Revenue'] / total_sales) * 100, 1) if total_sales > 0 else 0
        } for _, row in top_products_df.sort_values('Revenue', ascending=False).head(5).iterrows()]
    
    return render_template('analytics.html',
                         summary_stats=summary_stats,
                         category_chart=category_chart,
                         stock_chart=stock_chart,
                         sales_chart=sales_chart,
                         recent_activities=recent_activities,
                         top_products=top_products,
                         stock_status='warning' if summary_stats['low_stock_items'] > 0 else 'success',
                         stock_status_label='Low Stock' if summary_stats['low_stock_items'] > 0 else 'Good')
@app.route('/start_voice_command')
def start_voice_command():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for command...")
        try:
            # First ask for language
            language = ask_language(recognizer, source)
            
            # Then ask what they want to do
            action = ask_action(recognizer, source, language)
            
            # Process the action
            response = process_action(recognizer, source, action, language)
            
            return response

        except sr.WaitTimeoutError:
            return "Listening timed out. Please try again."
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError as e:
            return f"Could not request results; {e}"

def speak(text, language='en'):
    """Function to convert text to speech (implementation depends on your setup)"""
    # You can use gTTS or pyttsx3 here
    print(f"AI: {text}")

def ask_language(recognizer, source):
    """Ask user to select language"""
    speak("Please choose your language: Tamil, Hindi, or English")
    
    while True:
        try:
            audio = recognizer.listen(source, timeout=5)
            language = recognizer.recognize_google(audio).lower()
            
            if 'tamil' in language:
                return 'ta'
            elif 'hindi' in language:
                return 'hi'
            elif 'english' in language:
                return 'en'
            else:
                speak("Sorry, I didn't understand. Please say Tamil, Hindi, or English")
                
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please say Tamil, Hindi, or English")

def ask_action(recognizer, source, language):
    """Ask user what action they want to perform"""
    if language == 'ta':
        speak("நீங்கள் என்ன செய்ய விரும்புகிறீர்கள்? பொருட்களை சேர்க்க, பங்கு தகவல் பெற, வருவாய் தகவல் பெற, அல்லது ஆர்டர்கள் பற்றி தகவல் பெற?")
    elif language == 'hi':
        speak("आप क्या करना चाहते हैं? उत्पाद जोड़ें, स्टॉक जानकारी प्राप्त करें, आय जानकारी प्राप्त करें, या आदेशों के बारे में जानकारी प्राप्त करें?")
    else:
        speak("What would you like to do? Add products, get stock information, get earnings information, or get orders information?")
    
    while True:
        try:
            audio = recognizer.listen(source, timeout=5)
            action = recognizer.recognize_google(audio).lower()
            
            if any(word in action for word in ['add', 'insert', 'create']):
                return 'add'
            elif any(word in action for word in ['stock', 'inventory']):
                return 'stock'
            elif any(word in action for word in ['earn', 'income', 'revenue']):
                return 'earnings'
            elif any(word in action for word in ['order', 'purchase']):
                return 'orders'
            elif any(word in action for word in ['tell me', 'explain', 'describe']):
                return 'explain'
            else:
                if language == 'ta':
                    speak("மன்னிக்கவும், எனக்கு புரியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்")
                elif language == 'hi':
                    speak("क्षमा करें, मुझे समझ नहीं आया। कृपया पुनः प्रयास करें")
                else:
                    speak("Sorry, I didn't understand. Please try again")
                
        except sr.UnknownValueError:
            if language == 'ta':
                speak("மன்னிக்கவும், எனக்கு கேட்க முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்")
            elif language == 'hi':
                speak("क्षमा करें, मैं नहीं सुन सकता। कृपया पुनः प्रयास करें")
            else:
                speak("Sorry, I couldn't hear that. Please try again")

def process_action(recognizer, source, action, language):
    """Process the user's requested action"""
    if action == 'add':
        return add_product_voice(recognizer, source, language)
    elif action == 'stock':
        return get_stock_info(language)
    elif action == 'earnings':
        return get_earnings_info(language)
    elif action == 'orders':
        return get_orders_info(language)
    elif action == 'explain':
        return explain_data(language)
    else:
        if language == 'ta':
            return "செயலைச் செயல்படுத்த முடியவில்லை"
        elif language == 'hi':
            return "कार्रवाई को संसाधित नहीं कर सका"
        else:
            return "Could not process the action"

def add_product_voice(recognizer, source, language):
    """Handle adding products via voice"""
    if language == 'ta':
        speak("பொருளின் பெயர் என்ன?")
    elif language == 'hi':
        speak("उत्पाद का नाम क्या है?")
    else:
        speak("What is the product name?")
    
    audio = recognizer.listen(source, timeout=5)
    product_name = recognizer.recognize_google(audio)
    
    if language == 'ta':
        speak(f"{product_name} இன் அளவு எவ்வளவு? எடுத்துக்காட்டாக, 1 கிலோ அல்லது 500 கிராம்")
    elif language == 'hi':
        speak(f"{product_name} की मात्रा कितनी है? उदाहरण के लिए, 1 किलो या 500 ग्राम")
    else:
        speak(f"How much quantity for {product_name}? For example, 1 kg or 500 grams")
    
    audio = recognizer.listen(source, timeout=5)
    quantity_info = recognizer.recognize_google(audio)
    
    # Parse quantity and unit
    try:
        quantity, unit = parse_quantity(quantity_info)
    except ValueError:
        if language == 'ta':
            return "அளவை புரிந்து கொள்ள முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்"
        elif language == 'hi':
            return "मात्रा को समझ नहीं सका। कृपया पुनः प्रयास करें"
        else:
            return "Could not understand the quantity. Please try again"
    
    if language == 'ta':
        speak(f"{product_name} இன் விலை என்ன?")
    elif language == 'hi':
        speak(f"{product_name} की कीमत क्या है?")
    else:
        speak(f"What is the price for {product_name}?")
    
    audio = recognizer.listen(source, timeout=5)
    price = recognizer.recognize_google(audio)
    
    try:
        price = float(price)
    except ValueError:
        if language == 'ta':
            return "விலையை புரிந்து கொள்ள முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்"
        elif language == 'hi':
            return "कीमत समझ नहीं सका। कृपया पुनः प्रयास करें"
        else:
            return "Could not understand the price. Please try again"
    
    # Add product to database
    products = read_excel('products.xlsx')
    user_id = session.get('user_id', 'voice_user')
    
    new_product = {
        'Product ID': str(uuid.uuid4()),
        'User ID': user_id,
        'Name': product_name,
        'Category': 'General',
        'Price': price,
        'Stock': quantity,
        'Description': f'{quantity} {unit}',
        'Image URL': 'https://via.placeholder.com/150',
        'Status': 'Active',
        'Created Date': datetime.now().strftime('%Y-%m-%d'),
        'Last Updated': datetime.now().strftime('%Y-%m-%d')
    }
    
    updated_products = pd.concat([products, pd.DataFrame([new_product])], ignore_index=True)
    write_excel('products.xlsx', updated_products)
    
    if language == 'ta':
        return f"{quantity} {unit} {product_name} விலை ரூ.{price} வெற்றிகரமாக சேர்க்கப்பட்டது"
    elif language == 'hi':
        return f"{quantity} {unit} {product_name} कीमत ₹{price} सफलतापूर्वक जोड़ा गया"
    else:
        return f"{quantity} {unit} of {product_name} priced at ₹{price} added successfully"

def parse_quantity(text):
    """Parse quantity and unit from text"""
    # Match numbers followed by units
    match = re.search(r'(\d+)\s*(kg|g|gram|grams|kilo|kilograms|kilos)?', text.lower())
    if match:
        quantity = int(match.group(1))
        unit = match.group(2) or 'units'
        
        # Standardize units
        if unit in ['kg', 'kilo', 'kilos', 'kilograms']:
            unit = 'kg'
        elif unit in ['g', 'gram', 'grams']:
            unit = 'g'
            
        return quantity, unit
    raise ValueError("Could not parse quantity")

def get_stock_info(language):
    """Get stock information"""
    products = read_excel('products.xlsx')
    user_id = session.get('user_id')
    
    if user_id:
        user_products = products[products['User ID'] == user_id]
    else:
        user_products = products
    
    total_products = len(user_products)
    low_stock = user_products[user_products['Stock'] < 10]
    
    if language == 'ta':
        message = f"நீங்கள் {total_products} பொருட்களைக் கொண்டிருக்கிறீர்கள். "
        if len(low_stock) > 0:
            message += f"{len(low_stock)} பொருட்கள் குறைந்த பங்கில் உள்ளன. அவை: "
            message += ", ".join(low_stock['Name'].tolist())
        else:
            message += "எந்த பொருட்களும் குறைந்த பங்கில் இல்லை."
    elif language == 'hi':
        message = f"आपके पास {total_products} उत्पाद हैं। "
        if len(low_stock) > 0:
            message += f"{len(low_stock)} उत्पाद कम स्टॉक में हैं। वे हैं: "
            message += ", ".join(low_stock['Name'].tolist())
        else:
            message += "कोई भी उत्पाद कम स्टॉक में नहीं है।"
    else:
        message = f"You have {total_products} products. "
        if len(low_stock) > 0:
            message += f"{len(low_stock)} products are low in stock. They are: "
            message += ", ".join(low_stock['Name'].tolist())
        else:
            message += "No products are low in stock."
    
    return message

def get_earnings_info(language):
    """Get earnings information"""
    earnings = read_excel('earnings.xlsx')
    user_id = session.get('user_id')
    
    if user_id:
        user_earnings = earnings[earnings['Supplier ID'] == user_id]
    else:
        user_earnings = earnings
    
    total_earnings = user_earnings['Amount'].sum() if not user_earnings.empty else 0
    paid_earnings = user_earnings[user_earnings['Paid'] == 'Yes']['Amount'].sum() if not user_earnings.empty else 0
    
    if language == 'ta':
        message = f"உங்கள் மொத்த வருவாய் ரூ.{total_earnings:.2f}. இதில் ரூ.{paid_earnings:.2f} செலுத்தப்பட்டுள்ளது."
    elif language == 'hi':
        message = f"आपकी कुल आय ₹{total_earnings:.2f} है। इसमें से ₹{paid_earnings:.2f} का भुगतान किया गया है।"
    else:
        message = f"Your total earnings are ₹{total_earnings:.2f}. Out of this, ₹{paid_earnings:.2f} has been paid."
    
    return message

def get_orders_info(language):
    """Get orders information"""
    orders = read_excel('orders.xlsx')
    user_id = session.get('user_id')
    
    if user_id:
        user_orders = orders[orders['Supplier ID'] == user_id]
    else:
        user_orders = orders
    
    total_orders = len(user_orders)
    pending_orders = len(user_orders[user_orders['Status'] == 'Pending']) if not user_orders.empty else 0
    
    if language == 'ta':
        message = f"உங்களிடம் {total_orders} ஆர்டர்கள் உள்ளன. {pending_orders} ஆர்டர்கள் நிலுவையில் உள்ளன."
    elif language == 'hi':
        message = f"आपके पास {total_orders} आदेश हैं। {pending_orders} आदेश लंबित हैं।"
    else:
        message = f"You have {total_orders} orders. {pending_orders} orders are pending."
    
    return message

def explain_data(language):
    """Explain the data to the user"""
    if language == 'ta':
        return ("இந்த அமைப்பு உங்கள் தயாரிப்புகள், ஆர்டர்கள், விநியோகங்கள் மற்றும் வருவாயை நிர்வகிக்க உதவுகிறது. "
                "நீங்கள் பொருட்களைச் சேர்க்கலாம், பங்கு நிலுவைகளைப் பார்க்கலாம், ஆர்டர்களைப் பார்க்கலாம் மற்றும் "
                "உங்கள் வருவாய் பற்றிய தகவல்களைப் பெறலாம்.")
    elif language == 'hi':
        return ("यह प्रणाली आपके उत्पादों, आदेशों, डिलीवरी और आय को प्रबंधित करने में आपकी सहायता करती है। "
                "आप उत्पाद जोड़ सकते हैं, स्टॉक स्तर देख सकते हैं, ऑर्डर देख सकते हैं और "
                "अपनी आय के बारे में जानकारी प्राप्त कर सकते हैं।")
    else:
        return ("This system helps you manage your products, orders, deliveries and earnings. "
                "You can add products, view stock levels, check orders and "
                "get information about your earnings.")
def process_voice_command(command):
    pattern = r"add\s+(\w+)\s*(\d+)\s*(kg|g|gram|grams)?"
    match = re.search(pattern, command.lower())

    if match:
        product_name = match.group(1).capitalize()
        quantity = int(match.group(2))
        unit = match.group(3) if match.group(3) else 'kg'

        # Add product to products.xlsx
        products = read_excel('products.xlsx')
        user_id = session.get('user_id', 'voice_user')  # fallback if session not set

        new_product = {
            'Product ID': str(uuid.uuid4()),
            'User ID': user_id,
            'Name': product_name,
            'Category': 'General',
            'Price': 0,
            'Stock': quantity,
            'Description': f'{quantity} {unit}',
            'Image URL': 'https://via.placeholder.com/150',
            'Status': 'Active',
            'Created Date': datetime.now().strftime('%Y-%m-%d'),
            'Last Updated': datetime.now().strftime('%Y-%m-%d')
        }

        updated_products = pd.concat([products, pd.DataFrame([new_product])], ignore_index=True)
        write_excel('products.xlsx', updated_products)

        return f"Added {quantity} {unit} of {product_name} successfully."
    else:
        return "Sorry, I couldn't understand the command format. Please say 'add product_name quantity kg'."

if __name__ == '__main__':
    app.run(debug=True)
