import streamlit as st
from voice_input import VoiceInput
import requests
import os
from datetime import datetime
import json

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati'
}

def init_session_state():
    """Initialize session state variables"""
    if 'products' not in st.session_state:
        st.session_state.products = []
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    if 'description' not in st.session_state:
        st.session_state.description = ''
    if 'edit_product' not in st.session_state:
        st.session_state.edit_product = None

def show_add_product_page():
    """Display the product addition form"""
    st.title("Add New Product")
    
    with st.form("product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basic Information")
            product_name = st.text_input("Product Name*", 
                value=st.session_state.edit_product['name'] if st.session_state.edit_product else '')
            
            # Voice input component
            if st.checkbox("Use Voice Input"):
                voice_text = VoiceInput(st.session_state.language).render()
                if voice_text:
                    product_name = voice_text
            
            category = st.selectbox(
                "Category*",
                ["Agriculture", "Handicraft", "Textiles", "Groceries", "Pottery"],
                index=0 if not st.session_state.edit_product else 
                    ["Agriculture", "Handicraft", "Textiles", "Groceries", "Pottery"].index(
                        st.session_state.edit_product['category'])
            )
            
            price = st.number_input("Price (₹)*", min_value=0.0, step=0.5,
                value=st.session_state.edit_product['price'] if st.session_state.edit_product else 0.0)
            stock = st.number_input("Stock Quantity*", min_value=0, step=1,
                value=st.session_state.edit_product['stock'] if st.session_state.edit_product else 0)
            
        with col2:
            st.subheader("Additional Details")
            color = st.text_input("Color",
                value=st.session_state.edit_product.get('color', '') if st.session_state.edit_product else '')
            material = st.text_input("Material",
                value=st.session_state.edit_product.get('material', '') if st.session_state.edit_product else '')
            
            # Description generation
            if st.button("Generate Description"):
                if not product_name or not category:
                    st.warning("Please provide product name and category first")
                else:
                    with st.spinner("Generating description..."):
                        try:
                            product_data = {
                                "name": product_name,
                                "category": category,
                                "color": color,
                                "material": material
                            }
                            response = requests.post(
                                f"{BACKEND_URL}/api/ai/generate-description",
                                json={
                                    "product": product_data,
                                    "language": st.session_state.language
                                }
                            )
                            st.session_state.description = response.json()['description']
                        except Exception as e:
                            st.error(f"Failed to generate description: {str(e)}")
            
            description = st.text_area(
                "Description*",
                value=st.session_state.edit_product['description'] if st.session_state.edit_product 
                    else st.session_state.description,
                height=200
            )
        
        # Form submission
        submitted = st.form_submit_button(
            "Update Product" if st.session_state.edit_product else "Save Product"
        )
        if submitted:
            if not all([product_name, category, price, stock, description]):
                st.error("Please fill all required fields (*)")
            else:
                product_data = {
                    "name": product_name,
                    "category": category,
                    "description": description,
                    "price": float(price),
                    "stock": int(stock),
                    "color": color,
                    "material": material,
                    "language": st.session_state.language
                }
                
                try:
                    if st.session_state.edit_product:
                        # Update existing product
                        response = requests.put(
                            f"{BACKEND_URL}/api/products/{st.session_state.edit_product['id']}",
                            json=product_data
                        )
                        if response.status_code == 200:
                            st.success("Product updated successfully!")
                            st.session_state.edit_product = None
                            st.session_state.description = ""
                            st.experimental_rerun()
                    else:
                        # Create new product
                        response = requests.post(
                            f"{BACKEND_URL}/api/products",
                            json=product_data
                        )
                        if response.status_code == 201:
                            st.success("Product saved successfully!")
                            st.session_state.description = ""
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def show_inventory_page():
    """Display the inventory management page"""
    st.title("Your Inventory")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/products")
        products = response.json()
        
        if not products:
            st.info("No products found. Add your first product!")
            return
            
        for product in products:
            with st.expander(f"{product['name']} - ₹{product['price']}"):
                cols = st.columns([3, 1])
                
                with cols[0]:
                    st.write(f"**Category:** {product['category']}")
                    st.write(f"**Stock:** {product['stock']}")
                    
                    if 'alerts' in product and product['alerts']:
                        st.warning("Alerts: " + ", ".join(product['alerts']))
                    
                    st.write("**Description:**")
                    st.write(product['description'])
                
                with cols[1]:
                    if st.button("Edit", key=f"edit_{product['id']}"):
                        st.session_state.edit_product = product
                        st.session_state.description = product['description']
                        st.experimental_rerun()
                    
                    if st.button("Delete", key=f"delete_{product['id']}"):
                        try:
                            response = requests.delete(
                                f"{BACKEND_URL}/api/products/{product['id']}"
                            )
                            if response.status_code == 200:
                                st.success("Product deleted")
                                st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
    except Exception as e:
        st.error(f"Failed to load inventory: {str(e)}")

def show_notifications_page():
    """Display the notifications page"""
    st.title("Notifications")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/products")
        products = response.json()
        
        notifications = []
        for product in products:
            if 'alerts' in product and product['alerts']:
                for alert in product['alerts']:
                    if alert == 'low_stock':
                        notifications.append({
                            'type': 'warning',
                            'message': f"Low stock for {product['name']} (only {product['stock']} left)",
                            'timestamp': product.get('last_updated', '')
                        })
                    elif alert == 'price_outdated':
                        notifications.append({
                            'type': 'info',
                            'message': f"Price outdated for {product['name']} (last updated: {product.get('last_updated', '')})",
                            'timestamp': product.get('last_updated', '')
                        })
        
        if not notifications:
            st.info("No notifications at this time")
            return
            
        for notification in sorted(notifications, key=lambda x: x['timestamp'], reverse=True):
            if notification['type'] == 'warning':
                st.warning(notification['message'])
            else:
                st.info(notification['message'])
    
    except Exception as e:
        st.error(f"Failed to load notifications: {str(e)}")

def main():
    # Initialize session state
    init_session_state()
    
    # Configure page
    st.set_page_config(
        page_title="AI Catalog Agent",
        layout="wide",
        menu_items={
            'Get Help': 'https://example.com/help',
            'Report a bug': "https://example.com/bug",
            'About': "# AI Catalog Agent for Small Businesses"
        }
    )
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Add Product", "View Inventory", "Notifications"])
    
    # Language selector
    st.session_state.language = st.sidebar.selectbox(
        "Language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda x: SUPPORTED_LANGUAGES[x],
        index=0
    )
    
    # Clear edit mode if navigating away
    if page != "Add Product" and st.session_state.edit_product:
        st.session_state.edit_product = None
        st.session_state.description = ""
    
    # Page routing
    if page == "Add Product":
        show_add_product_page()
    elif page == "View Inventory":
        show_inventory_page()
    else:
        show_notifications_page()

if __name__ == "__main__":
    main()