import pandas as pd
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.security import generate_password_hash

def create_sample_data():
    # Create directory if not exists
    os.makedirs('excel_data', exist_ok=True)
    
    # Sample Users Data with Roles
    users_data = {
        'User ID': ['supp-001', 'supp-002', 'admin-001'],
        'Username': ['supplier1', 'supplier2', 'admin'],
        'Password': [
            generate_password_hash('supplier123'),
            generate_password_hash('supplier456'),
            generate_password_hash('admin123')
        ],
        'Company': ['Fresh Foods Inc.', 'Quality Goods Ltd.', 'Admin Corp'],
        'Email': ['supplier1@example.com', 'supplier2@example.com', 'admin@example.com'],
        'Address': ['123 Supplier St', '456 Vendor Ave', '789 Admin Blvd'],
        'Phone': ['555-1234', '555-5678', '555-0000'],
        'Business Type': ['Grocery', 'Electronics', 'Administration'],
        'Registration Date': ['2023-01-15', '2023-02-20', '2023-01-01'],
        'Role': ['supplier', 'supplier', 'admin']
    }
    
    # Sample Products Data
    products_data = {
        'Product ID': ['prod-001', 'prod-002', 'prod-003', 'prod-004', 'prod-005'],
        'User ID': ['supp-001', 'supp-001', 'supp-002', 'supp-002', 'supp-001'],
        'Name': ['Organic Apples', 'Fresh Milk', 'Smartphone X', 'Wireless Earbuds', 'Organic Bananas'],
        'Category': ['Fruits', 'Dairy', 'Electronics', 'Accessories', 'Fruits'],
        'Price': [1.99, 2.49, 599.99, 79.99, 0.99],
        'Stock': [5, 15, 8, 20, 3],  # Some low stock items for alerts
        'Description': [
            'Fresh organic apples', 
            'Whole milk 1L', 
            'Latest smartphone', 
            'Noise cancelling',
            'Organic fair-trade bananas'
        ],
        'Image URL': [
            'https://example.com/apples.jpg', 
            'https://example.com/milk.jpg', 
            'https://example.com/phone.jpg', 
            'https://example.com/earbuds.jpg',
            'https://example.com/bananas.jpg'
        ],
        'Status': ['Active', 'Active', 'Active', 'Active', 'Active'],
        'Created Date': ['2023-03-01', '2023-03-05', '2023-04-10', '2023-04-15', '2023-05-01'],
        'Last Updated': ['2023-10-01', '2023-10-05', '2023-10-10', '2023-10-15', '2023-10-20']
    }
    
    # Sample Orders Data (last 30 days)
    orders = []
    products = pd.DataFrame(products_data)
    for i in range(1, 31):
        days_ago = 30 - (i % 30)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # Alternate between suppliers
        supplier_id = 'supp-001' if i % 2 else 'supp-002'
        supplier_products = products[products['User ID'] == supplier_id]
        
        if not supplier_products.empty:
            product = supplier_products.sample(1).iloc[0]
            
            orders.append({
                'Order ID': f'ord-{1000+i}',
                'Retailer Name': f'Retailer {i}',
                'Email': f'retailer{i}@example.com',
                'Product ID': product['Product ID'],
                'Product Name': product['Name'],
                'Quantity': i % 5 + 1,  # Random quantity 1-5
                'Price': product['Price'],
                'Status': ['Pending', 'Shipped', 'Delivered'][i % 3],
                'Ordered Date': order_date,
                'Supplier ID': supplier_id
            })
    
    # Create sample deliveries for some orders
    deliveries = []
    for i, order in enumerate(orders[:15]):  # Create deliveries for first 15 orders
        status = ['Pending', 'In Transit', 'Delivered'][i % 3]
        dispatched_date = (datetime.strptime(order['Ordered Date'], '%Y-%m-%d') + 
                         timedelta(days=1)).strftime('%Y-%m-%d')
        
        delivered_date = None
        if status == 'Delivered':
            delivered_date = (datetime.strptime(dispatched_date, '%Y-%m-%d') + 
                            timedelta(days=2)).strftime('%Y-%m-%d')
        
        deliveries.append({
            'Delivery ID': f'del-{2000+i}',
            'Order ID': order['Order ID'],
            'Delivery Partner': ['FastShip', 'QuickDeliver', 'GlobalLogistics'][i % 3],
            'Status': status,
            'Dispatched Date': dispatched_date,
            'Delivered Date': delivered_date,
            'Supplier ID': order['Supplier ID']
        })
    
    # Create sample earnings
    earnings = []
    for i, order in enumerate(orders):
        if order['Status'] == 'Delivered':
            earnings.append({
                'Earning ID': f'earn-{3000+i}',
                'Order ID': order['Order ID'],
                'Amount': order['Price'] * order['Quantity'],
                'Paid': ['Yes', 'No'][i % 2],
                'Date': order['Ordered Date'],
                'Supplier ID': order['Supplier ID']
            })
    
    # Create DataFrames and save to Excel
    pd.DataFrame(users_data).to_excel('excel_data/users.xlsx', index=False)
    pd.DataFrame(products_data).to_excel('excel_data/products.xlsx', index=False)
    pd.DataFrame(orders).to_excel('excel_data/orders.xlsx', index=False)
    pd.DataFrame(deliveries).to_excel('excel_data/deliveries.xlsx', index=False)
    pd.DataFrame(earnings).to_excel('excel_data/earnings.xlsx', index=False)
    
    # Create passwords backup
    passwords_backup = {
        'User ID': users_data['User ID'],
        'Username': users_data['Username'],
        'Plain Password': ['supplier123', 'supplier456', 'admin123']
    }
    pd.DataFrame(passwords_backup).to_excel('excel_data/passwords_backup.xlsx', index=False)

if __name__ == '__main__':
    create_sample_data()
    print("Sample data created successfully!")