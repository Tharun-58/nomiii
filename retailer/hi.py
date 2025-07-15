import os
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

# Initialize Faker and create data directory
fake = Faker()
os.makedirs('data', exist_ok=True)

# Product categories
categories = ['Electronics', 'Clothing', 'Home & Kitchen', 'Books', 'Others']

# Generate products data
def generate_products(num=50):
    products = []
    for i in range(1, num+1):
        category = random.choice(categories)
        price = round(random.uniform(100, 2000), 2)
        stock = random.randint(0, 50)
        
        if stock == 0:
            status = 'Out of Stock'
        elif stock <= 10:
            status = 'Low Stock'
        else:
            status = 'In Stock'
            
        products.append({
            'product_id': f'PROD-{i:03d}',
            'name': f'Product {fake.random_letter().upper()}{i}',
            'category': category,
            'price': price,
            'stock': stock,
            'status': status
        })
    return products

# Generate customers data
def generate_customers(num=30):
    customers = []
    for i in range(1, num+1):
        customers.append({
            'customer_id': f'CUST-{i:03d}',
            'name': fake.name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'address': fake.address().replace('\n', ', '),
            'join_date': fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d'),
            'total_orders': random.randint(1, 15)
        })
    return customers

# Generate orders data
def generate_orders(num=100, products=None, customers=None):
    orders = []
    statuses = ['Completed', 'Processing', 'Cancelled', 'Shipped']
    
    for i in range(1, num+1):
        customer = random.choice(customers)
        order_date = fake.date_between(start_date='-3m', end_date='today')
        
        # Generate 1-5 products per order
        num_products = random.randint(1, 5)
        order_products = random.sample(products, num_products)
        
        # Calculate total amount
        amount = sum(p['price'] for p in order_products)
        amount = round(amount * (1 - random.uniform(0, 0.2)), 2)  # Apply random discount
        
        # Create order
        orders.append({
            'order_id': f'ORD-{1000 + i}',
            'customer_id': customer['customer_id'],
            'customer_name': customer['name'],
            'date': order_date.strftime('%Y-%m-%d'),
            'amount': amount,
            'status': random.choice(statuses),
            'products': ', '.join(p['name'] for p in order_products)
        })
    return orders

# Generate sales data (monthly)
def generate_sales(months=12):
    sales = []
    base_date = datetime.now() - timedelta(days=30*months)
    
    for i in range(months):
        month_date = base_date + timedelta(days=30*i)
        month_str = month_date.strftime('%Y-%m')
        
        for category in categories:
            amount = round(random.uniform(2000, 10000), 2)
            orders = random.randint(5, 25)
            
            sales.append({
                'month': month_str,
                'category': category,
                'amount': amount,
                'orders': orders
            })
    return sales

# Generate inventory data from products
def generate_inventory(products):
    inventory = []
    for p in products:
        inventory.append({
            'product_id': p['product_id'],
            'name': p['name'],
            'current_stock': p['stock'],
            'min_stock': 10 if p['category'] in ['Electronics', 'Home & Kitchen'] else 5,
            'status': p['status'],
            'last_updated': fake.date_between(start_date='-30d', end_date='today').strftime('%Y-%m-%d')
        })
    return inventory

# Generate category summary
def generate_categories(products, sales):
    category_data = []
    for category in categories:
        cat_products = [p for p in products if p['category'] == category]
        cat_sales = [s for s in sales if s['category'] == category]
        
        category_data.append({
            'category_id': f'CAT-{categories.index(category)+1:03d}',
            'name': category,
            'total_products': len(cat_products),
            'total_sales': round(sum(s['amount'] for s in cat_sales), 2),
            'avg_price': round(sum(p['price'] for p in cat_products)/len(cat_products), 2) if cat_products else 0
        })
    return category_data

# Main function to generate all data
def generate_all_data():
    print("Generating fake data...")
    
    # Generate products first as other data depends on it
    products = generate_products()
    pd.DataFrame(products).to_excel('data/products.xlsx', index=False)
    print("Generated products.xlsx")
    
    customers = generate_customers()
    pd.DataFrame(customers).to_excel('data/customers.xlsx', index=False)
    print("Generated customers.xlsx")
    
    orders = generate_orders(products=products, customers=customers)
    pd.DataFrame(orders).to_excel('data/orders.xlsx', index=False)
    print("Generated orders.xlsx")
    
    sales = generate_sales()
    pd.DataFrame(sales).to_excel('data/sales.xlsx', index=False)
    print("Generated sales.xlsx")
    
    inventory = generate_inventory(products)
    pd.DataFrame(inventory).to_excel('data/inventory.xlsx', index=False)
    print("Generated inventory.xlsx")
    
    categories = generate_categories(products, sales)
    pd.DataFrame(categories).to_excel('data/categories.xlsx', index=False)
    print("Generated categories.xlsx")
    
    print("All data files created in the 'data' folder!")

if __name__ == '__main__':
    generate_all_data()