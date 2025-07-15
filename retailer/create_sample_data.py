import pandas as pd
import os
from datetime import datetime, timedelta
import random

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Create sample sales data
sales_data = []
for i in range(7):
    month = (datetime.now() - timedelta(days=30*i)).strftime('%Y-%m')
    amount = random.randint(5000, 15000)
    sales_data.append({
        'month': month,
        'amount': amount
    })

df_sales = pd.DataFrame(sales_data)
df_sales.to_excel('data/sales.xlsx', index=False)

# Create sample orders data
orders_data = []
customers = ['John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Wilson', 'David Brown']
products_list = ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones']
statuses = ['Completed', 'Processing', 'Cancelled', 'Pending']

for i in range(20):
    order_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
    orders_data.append({
        'order_id': f'ORD-{1000 + i}',
        'customer_name': random.choice(customers),
        'date': order_date,
        'amount': random.randint(500, 5000),
        'status': random.choice(statuses),
        'products': ', '.join(random.sample(products_list, random.randint(1, 3)))
    })

df_orders = pd.DataFrame(orders_data)
df_orders.to_excel('data/orders.xlsx', index=False)

# Create sample products data
products_data = []
for i, product in enumerate(products_list):
    products_data.append({
        'id': i + 1,
        'name': product,
        'category': 'Electronics',
        'price': random.randint(100, 2000),
        'stock': random.randint(10, 100)
    })

df_products = pd.DataFrame(products_data)
df_products.to_excel('data/products.xlsx', index=False)

# Create sample customers data
customers_data = []
for i, customer in enumerate(customers):
    customers_data.append({
        'id': i + 1,
        'name': customer,
        'email': f'{customer.lower().replace(" ", ".")}@example.com',
        'phone': f'+91 {random.randint(7000000000, 9999999999)}',
        'address': f'{random.randint(1, 999)} Main St, City'
    })

df_customers = pd.DataFrame(customers_data)
df_customers.to_excel('data/customers.xlsx', index=False)

# Create sample inventory data
inventory_data = []
statuses = ['In Stock', 'Low Stock', 'Out of Stock']
for i, product in enumerate(products_list):
    inventory_data.append({
        'id': i + 1,
        'product': product,
        'quantity': random.randint(0, 100),
        'status': random.choice(statuses),
        'location': f'Warehouse {random.choice(["A", "B", "C"])}'
    })

df_inventory = pd.DataFrame(inventory_data)
df_inventory.to_excel('data/inventory.xlsx', index=False)

print("Sample data files created successfully!")