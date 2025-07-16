from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError
from datetime import datetime
from bson import ObjectId
import logging
import config

class CatalogManager:
    """Handles all database operations for product catalog"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.products_collection = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(
                config.MONGO_URI,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=30000
            )
            self.db = self.client[config.DB_NAME]
            self.products_collection = self.db.products
            
            # Create indexes
            self.products_collection.create_index([('seller_id', 1)])
            self.products_collection.create_index([('category', 1)])
            self.products_collection.create_index([('last_updated', -1)])
            
            logging.info("MongoDB connection established successfully")
        except PyMongoError as e:
            logging.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def check_connection(self):
        """Check if database connection is alive"""
        try:
            self.client.admin.command('ping')
            return True
        except PyMongoError:
            return False

    def add_product(self, product_data):
        """
        Add a new product to catalog
        
        Args:
            product_data (dict): Product information
            
        Returns:
            str: Inserted product ID
        """
        try:
            # Add timestamps
            product_data['created_at'] = datetime.utcnow()
            product_data['last_updated'] = datetime.utcnow()
            
            # Insert document
            result = self.products_collection.insert_one(product_data)
            
            logging.info(f"Product added with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except PyMongoError as e:
            logging.error(f"Failed to add product: {str(e)}")
            raise RuntimeError("Failed to add product to database")

    def get_products(self, seller_id=None, category=None):
        """
        Retrieve products from catalog
        
        Args:
            seller_id (str, optional): Filter by seller ID
            category (str, optional): Filter by category
            
        Returns:
            list: List of product dictionaries
        """
        try:
            query = {}
            if seller_id:
                query['seller_id'] = seller_id
            if category:
                query['category'] = category
                
            products = list(self.products_collection.find(
                query,
                projection={
                    '_id': 0,
                    'id': {'$toString': '$_id'},
                    'name': 1,
                    'category': 1,
                    'description': 1,
                    'price': 1,
                    'stock': 1,
                    'color': 1,
                    'material': 1,
                    'created_at': 1,
                    'last_updated': 1
                }
            ))
            
            # Add inventory alerts
            for product in products:
                product['alerts'] = self._check_product_alerts(product)
                
            logging.info(f"Retrieved {len(products)} products")
            return products
            
        except PyMongoError as e:
            logging.error(f"Failed to get products: {str(e)}")
            raise RuntimeError("Failed to retrieve products")

    def get_product(self, product_id):
        """
        Get single product by ID
        
        Args:
            product_id (str): Product ID
            
        Returns:
            dict: Product data or None if not found
        """
        try:
            product = self.products_collection.find_one(
                {'_id': ObjectId(product_id)},
                projection={
                    '_id': 0,
                    'id': {'$toString': '$_id'},
                    'name': 1,
                    'category': 1,
                    'description': 1,
                    'price': 1,
                    'stock': 1,
                    'color': 1,
                    'material': 1,
                    'created_at': 1,
                    'last_updated': 1
                }
            )
            
            if product:
                product['alerts'] = self._check_product_alerts(product)
                
            return product
            
        except PyMongoError as e:
            logging.error(f"Failed to get product {product_id}: {str(e)}")
            raise RuntimeError("Failed to retrieve product")

    def update_product(self, product_id, update_data):
        """
        Update product information
        
        Args:
            product_id (str): Product ID to update
            update_data (dict): Fields to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Add update timestamp
            update_data['last_updated'] = datetime.utcnow()
            
            result = self.products_collection.find_one_and_update(
                {'_id': ObjectId(product_id)},
                {'$set': update_data},
                return_document=ReturnDocument.AFTER
            )
            
            if result:
                logging.info(f"Product {product_id} updated successfully")
                return True
            return False
            
        except PyMongoError as e:
            logging.error(f"Failed to update product {product_id}: {str(e)}")
            raise RuntimeError("Failed to update product")

    def delete_product(self, product_id):
        """
        Delete product from catalog
        
        Args:
            product_id (str): Product ID to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            result = self.products_collection.delete_one(
                {'_id': ObjectId(product_id)}
            )
            
            if result.deleted_count > 0:
                logging.info(f"Product {product_id} deleted successfully")
                return True
            return False
            
        except PyMongoError as e:
            logging.error(f"Failed to delete product {product_id}: {str(e)}")
            raise RuntimeError("Failed to delete product")

    def _check_product_alerts(self, product):
        """
        Check product for inventory alerts
        
        Args:
            product (dict): Product data
            
        Returns:
            list: List of alert strings
        """
        alerts = []
        
        # Check stock level
        if product.get('stock', 0) < 5:
            alerts.append('low_stock')
            
        # Check price update age
        last_update = product.get('last_updated', datetime.min)
        if (datetime.utcnow() - last_update).days > 90:
            alerts.append('price_outdated')
            
        return alerts

# Singleton instance
catalog = CatalogManager()