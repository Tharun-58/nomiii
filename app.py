import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'data'

# Helper function to load Excel data
def load_data(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return pd.read_excel(filepath).to_dict(orient='records')
    return []

# Authentication routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_data('users.xlsx')
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # In a real app, you'd save this to the Excel file
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Main application routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Sample data - replace with actual calculations
    metrics = {
        'total_sales': 12345,
        'new_orders': 24,
        'products': 156,
        'customers': 89
    }
    
    return render_template('dashboard.html', metrics=metrics)

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