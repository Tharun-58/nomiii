import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'data'

# Ensure data directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to load Excel data
def load_data(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        try:
            return pd.read_excel(filepath).to_dict(orient='records')
        except:
            return []
    return []

# Helper function to save data to Excel
def save_data(filename, data):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)

# Initialize users file if it doesn't exist
def init_users_file():
    users_file = os.path.join(app.config['UPLOAD_FOLDER'], 'users.xlsx')
    if not os.path.exists(users_file):
        # Create a default admin user
        default_user = {
            'id': 1,
            'name': 'Admin',
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'email': 'admin@example.com',
            'role': 'admin',
            'business': 'Nomi Retail',
            'created_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data('users.xlsx', [default_user])

# Call the initialization function when the app starts
init_users_file()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_data('users.xlsx')
        user = next((u for u in users if u['username'] == username), None)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        business = request.form.get('business')
        
        # Validate input
        if not all([name, username, password, email]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('register'))
        
        # Check if username already exists
        users = load_data('users.xlsx')
        if any(u['username'] == username for u in users):
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = {
            'id': len(users) + 1,
            'name': name,
            'username': username,
            'password': generate_password_hash(password),
            'email': email,
            'business': business,
            'role': 'retailer',
            'created_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save to Excel
        users.append(new_user)
        save_data('users.xlsx', users)
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# ... rest of your routes remain the same ...
# Authentication routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Main application routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Load all necessary data
    sales_data = load_data('sales.xlsx')
    orders_data = load_data('orders.xlsx')
    products_data = load_data('products.xlsx')
    customers_data = load_data('customers.xlsx')
    inventory_data = load_data('inventory.xlsx')
    
    # Calculate metrics
    total_sales = sum(order.get('amount', 0) for order in orders_data if order.get('amount'))
    
    # Get recent orders (last 7 days)
    recent_orders = []
    try:
        recent_orders = sorted(
            [order for order in orders_data if 
             order.get('date') and datetime.strptime(order['date'], '%Y-%m-%d') > datetime.now() - timedelta(days=7)],
            key=lambda x: x['date'], 
            reverse=True
        )[:4]
    except (ValueError, KeyError):
        # If date parsing fails, just take the first 4 orders
        recent_orders = orders_data[:4]
    
    # Get top products (by order frequency)
    product_counts = {}
    for order in orders_data:
        products_str = order.get('products', '')
        if products_str:
            for product in products_str.split(', '):
                if product.strip():
                    product_counts[product.strip()] = product_counts.get(product.strip(), 0) + 1
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Calculate dashboard metrics
    metrics = {
        'total_sales': total_sales,
        'new_orders': len(recent_orders),
        'products': len(products_data),
        'customers': len(customers_data),
        'low_stock': sum(1 for item in inventory_data if item.get('status') == 'Low Stock')
    }
    
    # Prepare sales chart data (monthly)
    monthly_sales = {}
    for sale in sales_data:
        month = sale.get('month', '')
        if month:
            monthly_sales[month] = monthly_sales.get(month, 0) + sale.get('amount', 0)
    
    # Sort by month and get last 7 months or provide default data
    if monthly_sales:
        sorted_months = sorted(monthly_sales.keys())[-7:]
        chart_labels = [datetime.strptime(m, '%Y-%m').strftime('%b') for m in sorted_months]
        chart_data = [monthly_sales[m] for m in sorted_months]
    else:
        # Default data when no sales data is available
        chart_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
        chart_data = [0, 0, 0, 0, 0, 0, 0]
    
    return render_template('dashboard.html', 
                        metrics=metrics,
                        recent_orders=recent_orders,
                        top_products=top_products,
                        chart_labels=chart_labels,
                        chart_data=chart_data)
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user data
    user = {
        'name': session.get('name', ''),
        'username': session.get('username', ''),
        'email': 'john@example.com',
        'phone': '+91 9876543210',
        'business': "John's Electronics",
        'location': 'Chennai, India',
        'joined': 'January 2022'
    }
    
    # Sample activity data
    activity = [
        {'date': '2023-07-15', 'activity': 'Login', 'details': 'Logged in from Chrome on Windows'},
        {'date': '2023-07-14', 'activity': 'Order', 'details': 'Created new order #ORD-1001'},
        {'date': '2023-07-12', 'activity': 'Product', 'details': 'Added new product Wireless Headphones'},
    ]
    
    return render_template('profile.html', user=user, activity=activity)

@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    products = load_data('products.xlsx')
    return render_template('products.html', products=products)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    orders = load_data('orders.xlsx')
    
    # Calculate order metrics
    metrics = {
        'total_orders': len(orders),
        'completed': sum(1 for o in orders if o['status'] == 'Completed'),
        'processing': sum(1 for o in orders if o['status'] == 'Processing'),
        'cancelled': sum(1 for o in orders if o['status'] == 'Cancelled')
    }
    
    return render_template('orders.html', orders=orders, metrics=metrics)

@app.route('/inventory')
def inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    inventory = load_data('inventory.xlsx')
    
    # Calculate inventory metrics
    metrics = {
        'total_products': len(inventory),
        'in_stock': sum(1 for i in inventory if i['status'] == 'In Stock'),
        'low_stock': sum(1 for i in inventory if i['status'] == 'Low Stock'),
        'out_of_stock': sum(1 for i in inventory if i['status'] == 'Out of Stock')
    }
    
    return render_template('inventory.html', inventory=inventory, metrics=metrics)

@app.route('/sales')
def sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sales = load_data('sales.xlsx')
    
    # Sample metrics - replace with actual calculations
    metrics = {
        'total_sales': 56789,
        'orders': 42,
        'avg_order': 1352,
        'refunds': 2150
    }
    
    return render_template('sales.html', sales=sales, metrics=metrics)

@app.route('/customers')
def customers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    customers = load_data('customers.xlsx')
    
    # Sample metrics - replace with actual calculations
    metrics = {
        'total_customers': len(customers),
        'active': 72,
        'new_this_month': 15,
        'repeat': 34
    }
    
    return render_template('customers.html', customers=customers, metrics=metrics)

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Sample report data
    summary = [
        {'metric': 'Total Sales', 'value': '₹56,789', 'change': '+12%', 'trend': 'up'},
        {'metric': 'Number of Orders', 'value': '42', 'change': '+8%', 'trend': 'up'},
        {'metric': 'Average Order Value', 'value': '₹1,352', 'change': '+4%', 'trend': 'up'},
        {'metric': 'New Customers', 'value': '15', 'change': '+3%', 'trend': 'up'},
        {'metric': 'Refunds', 'value': '₹2,150', 'change': '-2%', 'trend': 'down'}
    ]
    
    category_sales = [
        {'category': 'Electronics', 'sales': '₹25,600', 'percentage': '45.1%'},
        {'category': 'Clothing', 'sales': '₹11,400', 'percentage': '20.1%'},
        {'category': 'Home & Kitchen', 'sales': '₹8,500', 'percentage': '15.0%'},
        {'category': 'Books', 'sales': '₹5,700', 'percentage': '10.0%'},
        {'category': 'Others', 'sales': '₹5,589', 'percentage': '9.8%'}
    ]
    
    reports = [
        {'id': '#REP-1001', 'type': 'Sales Report', 'generated': '2023-07-15', 'period': 'Last 30 days'},
        {'id': '#REP-1000', 'type': 'Inventory Report', 'generated': '2023-07-10', 'period': 'Current'},
        {'id': '#REP-0999', 'type': 'Customer Report', 'generated': '2023-07-05', 'period': 'Last quarter'}
    ]
    
    return render_template('reports.html', 
                          summary=summary, 
                          category_sales=category_sales,
                          reports=reports)

if __name__ == '__main__':
    app.run(debug=True)