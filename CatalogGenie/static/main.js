// Global state
let currentRole = null;
let currentLanguage = 'en';
let isRecording = false;
let inventory = [];
let recognition = null;

// Localization data
const translations = {
    en: {
        addProduct: "Add Product",
        speakNow: "Speak Now",
        productPlaceholder: "Or type product details...",
        uploadImage: "Upload Image",
        generateListing: "Generate Listing",
        aiListing: "AI-Generated Listing",
        title: "Title",
        description: "Description",
        category: "Category",
        attributes: "Attributes",
        translate: "Translate",
        saveProduct: "Save Product",
        inventory: "Inventory",
        searchPlaceholder: "Search products...",
        exportCatalog: "Export Catalog",
        product: "Product",
        stock: "Stock",
        lastUpdate: "Last Updated",
        actions: "Actions",
        stockAlert: "Low stock alert:",
        help: "Help",
        privacy: "Privacy",
        terms: "Terms",
        farmerDashboard: "Farmer Dashboard",
        artisanDashboard: "Artisan Dashboard",
        retailerDashboard: "Retailer Dashboard"
    },
    ta: {
        addProduct: "தயாரிப்பைச் சேர்க்கவும்",
        speakNow: "பேசுங்கள்",
        productPlaceholder: "அல்லது தயாரிப்பு விவரங்களை தட்டச்சு செய்யவும்...",
        uploadImage: "படத்தை பதிவேற்று",
        generateListing: "பட்டியலை உருவாக்கு",
        aiListing: "AI உருவாக்கிய பட்டியல்",
        title: "தலைப்பு",
        description: "விளக்கம்",
        category: "வகை",
        attributes: "பண்புகள்",
        translate: "மொழிபெயர்",
        saveProduct: "தயாரிப்பை சேமி",
        inventory: "இருப்பு",
        searchPlaceholder: "தயாரிப்புகளைத் தேடுங்கள்...",
        exportCatalog: "அட்டவணையை ஏற்றுமதி செய்க",
        product: "தயாரிப்பு",
        stock: "பங்கு",
        lastUpdate: "கடைசியாக புதுப்பிக்கப்பட்டது",
        actions: "செயல்கள்",
        stockAlert: "குறைந்த பங்கு எச்சரிக்கை:",
        help: "உதவி",
        privacy: "தனியுரிமை",
        terms: "விதிமுறைகள்",
        farmerDashboard: "விவசாயி டாஷ்போர்டு",
        artisanDashboard: "கைவினைஞர் டாஷ்போர்டு",
        retailerDashboard: "சில்லறை விற்பனையாளர் டாஷ்போர்டு"
    }
};

// Role-specific data
const roleData = {
    farmer: {
        title: "Farmer Dashboard",
        sampleInput: "Organic tomatoes, harvested yesterday, 50kg available, pesticide-free",
        aiResponse: {
            title: "Premium Organic Tomatoes",
            description: "Freshly harvested organic tomatoes, grown without pesticides or synthetic fertilizers. Rich in flavor and nutrients, perfect for salads, sauces, and cooking. Harvested within the last 24 hours to ensure maximum freshness.",
            categories: ["Fresh Produce", "Vegetables", "Organic Foods"],
            attributes: ["Organic", "Pesticide-Free", "Fresh", "50kg", "Harvested Daily"]
        }
    },
    artisan: {
        title: "Artisan Dashboard",
        sampleInput: "Handmade ceramic coffee mug, blue glaze, 350ml capacity",
        aiResponse: {
            title: "Artisan Ceramic Coffee Mug",
            description: "Beautiful handmade ceramic mug with unique blue glaze finish. Each piece is individually crafted and glazed, making it a unique work of art. Microwave and dishwasher safe. Perfect for your morning coffee or tea ritual.",
            categories: ["Handmade Crafts", "Kitchenware", "Ceramics"],
            attributes: ["Handmade", "Ceramic", "350ml", "Microwave Safe", "Dishwasher Safe"]
        }
    },
    retailer: {
        title: "Retailer Dashboard",
        sampleInput: "Wireless Bluetooth headphones, noise canceling, 20hr battery",
        aiResponse: {
            title: "Premium Wireless Bluetooth Headphones",
            description: "High-quality wireless headphones with active noise cancellation technology. Features 20-hour battery life, comfortable over-ear design, and crystal-clear audio quality. Perfect for travel, work, or leisure listening.",
            categories: ["Electronics", "Audio", "Headphones"],
            attributes: ["Bluetooth 5.0", "Noise Cancelling", "20hr Battery", "Wireless", "Over-Ear"]
        }
    }
};

// DOM Elements
const elements = {
    roleSelection: document.getElementById('role-selection'),
    dashboard: document.getElementById('dashboard'),
    roleTitle: document.getElementById('role-title'),
    langButtons: document.querySelectorAll('.lang-btn'),
    voiceBtn: document.getElementById('voice-btn'),
    startRecord: document.getElementById('start-record'),
    voiceFeedback: document.getElementById('voice-feedback'),
    productInput: document.getElementById('product-input'),
    imageUpload: document.getElementById('image-upload'),
    imagePreview: document.getElementById('image-preview'),
    generateBtn: document.getElementById('generate-btn'),
    aiTitle: document.getElementById('ai-title'),
    aiDescription: document.getElementById('ai-description'),
    aiCategory: document.getElementById('ai-category'),
    aiAttributes: document.getElementById('ai-attributes'),
    translateBtn: document.getElementById('translate-btn'),
    saveBtn: document.getElementById('save-btn'),
    inventoryTable: document.getElementById('inventory-body'),
    searchInventory: document.getElementById('search-inventory'),
    exportBtn: document.getElementById('export-btn'),
    stockAlert: document.getElementById('stock-alert'),
    alertItems: document.getElementById('alert-items'),
    exportModal: document.getElementById('export-modal'),
    closeModal: document.querySelector('.close-modal'),
    exportOptions: document.querySelectorAll('.export-option')
};

// Initialize application
function init() {
    setupEventListeners();
    updateUI();
    loadSampleInventory();
}

// Set up event listeners
function setupEventListeners() {
    // Voice recording
    elements.startRecord.addEventListener('click', toggleRecording);
    
    // Image upload
    elements.imageUpload.addEventListener('change', handleImageUpload);
    
    // Generate listing
    elements.generateBtn.addEventListener('click', generateListing);
    
    // Save product
    elements.saveBtn.addEventListener('click', saveProduct);
    
    // Export catalog
    elements.exportBtn.addEventListener('click', () => {
        elements.exportModal.style.display = 'flex';
    });
    
    // Close modal
    elements.closeModal.addEventListener('click', () => {
        elements.exportModal.style.display = 'none';
    });
    
    // Export format selection
    elements.exportOptions.forEach(option => {
        option.addEventListener('click', (e) => {
            const format = e.currentTarget.dataset.format;
            exportCatalog(format);
        });
    });
    
    // Search inventory
    elements.searchInventory.addEventListener('input', filterInventory);
    
    // Initialize speech recognition if available
    initSpeechRecognition();
}

// Role selection
function selectRole(role) {
    currentRole = role;
    elements.roleSelection.classList.remove('active');
    elements.dashboard.classList.add('active');
    updateRoleDashboard();
    updateUI();
}

// Logout function
function logout() {
    currentRole = null;
    elements.dashboard.classList.remove('active');
    elements.roleSelection.classList.add('active');
    resetForm();
}

// Set language
function setLanguage(lang) {
    currentLanguage = lang;
    updateUI();
    
    // Update active language button
    elements.langButtons.forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(lang === 'en' ? 'EN' : 'TA'));
    });
}

// Update UI based on current language
function updateUI() {
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = translations[currentLanguage][key] || key;
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        const key = el.getAttribute('data-i18n-ph');
        el.placeholder = translations[currentLanguage][key] || key;
    });
}

// Update dashboard based on role
function updateRoleDashboard() {
    if (!currentRole) return;
    
    const role = roleData[currentRole];
    elements.roleTitle.textContent = translations[currentLanguage][`${currentRole}Dashboard`] || role.title;
}

// Initialize speech recognition
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        elements.voiceBtn.style.display = 'none';
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    
    if (currentLanguage === 'ta') {
        recognition.lang = 'ta-IN'; // Tamil India
    } else {
        recognition.lang = 'en-US'; // English US
    }
    
    recognition.onstart = () => {
        isRecording = true;
        elements.voiceFeedback.textContent = translations[currentLanguage].speakNow;
        elements.startRecord.innerHTML = `<i class="fas fa-microphone"></i> ${translations[currentLanguage].speakNow}`;
        elements.startRecord.classList.add('recording');
    };
    
    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');
        
        elements.voiceFeedback.textContent = transcript;
        elements.productInput.value = transcript;
    };
    
    recognition.onend = () => {
        isRecording = false;
        elements.startRecord.innerHTML = `<i class="fas fa-microphone"></i> ${translations[currentLanguage].speakNow}`;
        elements.startRecord.classList.remove('recording');
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        elements.voiceFeedback.textContent = translations[currentLanguage].error || 'Error: ' + event.error;
    };
}

// Toggle voice recording
function toggleRecording() {
    if (!recognition) {
        alert('Speech recognition not supported in your browser');
        return;
    }
    
    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

// Handle image upload
function handleImageUpload(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    elements.imagePreview.innerHTML = '';
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (!file.type.match('image.*')) continue;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.classList.add('preview-image');
            elements.imagePreview.appendChild(img);
        };
        reader.readAsDataURL(file);
    }
}

// Generate AI listing
function generateListing() {
    const input = elements.productInput.value.trim();
    
    if (!input && elements.imagePreview.children.length === 0) {
        alert(translations[currentLanguage].inputRequired || 'Please provide product details or upload an image');
        return;
    }
    
    // Simulate AI processing
    setTimeout(() => {
        const response = roleData[currentRole].aiResponse;
        
        // Update UI with AI response
        elements.aiTitle.textContent = response.title;
        elements.aiDescription.textContent = response.description;
        
        // Clear and add categories
        elements.aiCategory.innerHTML = '';
        response.categories.forEach(category => {
            const tag = document.createElement('span');
            tag.textContent = category;
            tag.classList.add('tag');
            elements.aiCategory.appendChild(tag);
        });
        
        // Clear and add attributes
        elements.aiAttributes.innerHTML = '';
        response.attributes.forEach(attr => {
            const tag = document.createElement('span');
            tag.textContent = attr;
            tag.classList.add('tag');
            elements.aiAttributes.appendChild(tag);
        });
        
        // Scroll to AI section
        document.querySelector('.ai-section').scrollIntoView({ behavior: 'smooth' });
    }, 1500);
}

// Save product to inventory
function saveProduct() {
    const title = elements.aiTitle.textContent;
    if (!title) {
        alert(translations[currentLanguage].saveError || 'Please generate a listing before saving');
        return;
    }
    
    // Create inventory item
    const newItem = {
        id: Date.now(),
        title: title,
        description: elements.aiDescription.textContent,
        categories: Array.from(elements.aiCategory.querySelectorAll('.tag')).map(tag => tag.textContent),
        attributes: Array.from(elements.aiAttributes.querySelectorAll('.tag')).map(tag => tag.textContent),
        stock: Math.floor(Math.random() * 100) + 1,
        lastUpdated: new Date().toLocaleDateString()
    };
    
    // Add to inventory
    inventory.push(newItem);
    
    // Update inventory display
    updateInventory();
    
    // Show confirmation
    alert(`${title} ${translations[currentLanguage].saved || 'saved to inventory!'}`);
    
    // Reset form
    resetForm();
}

// Update inventory display
function updateInventory() {
    elements.inventoryTable.innerHTML = '';
    
    inventory.forEach(item => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${item.title}</td>
            <td>${item.stock}</td>
            <td>${item.lastUpdated}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editItem(${item.id})">
                    <i class="fas fa-edit"></i> ${translations[currentLanguage].edit || 'Edit'}
                </button>
                <button class="action-btn delete-btn" onclick="deleteItem(${item.id})">
                    <i class="fas fa-trash"></i> ${translations[currentLanguage].delete || 'Delete'}
                </button>
            </td>
        `;
        
        elements.inventoryTable.appendChild(row);
    });
    
    // Update low stock alert
    updateStockAlert();
}

// Filter inventory
function filterInventory() {
    const searchTerm = elements.searchInventory.value.toLowerCase();
    const rows = elements.inventoryTable.querySelectorAll('tr');
    
    rows.forEach(row => {
        const title = row.querySelector('td:first-child').textContent.toLowerCase();
        row.style.display = title.includes(searchTerm) ? '' : 'none';
    });
}

// Update low stock alert
function updateStockAlert() {
    const lowStockItems = inventory.filter(item => item.stock < 10);
    
    if (lowStockItems.length > 0) {
        elements.stockAlert.style.display = 'flex';
        elements.alertItems.textContent = lowStockItems.map(item => item.title).join(', ');
    } else {
        elements.stockAlert.style.display = 'none';
    }
}

// Edit inventory item
function editItem(id) {
    const item = inventory.find(i => i.id === id);
    if (!item) return;
    
    // Pre-fill form with item data
    elements.productInput.value = `${item.title}. ${item.description}`;
    
    // Simulate image upload (in a real app, you would show actual images)
    elements.imagePreview.innerHTML = `<div>${translations[currentLanguage].imagePlaceholder || 'Product image would appear here'}</div>`;
    
    // Generate listing
    generateListing();
    
    // Scroll to input section
    document.querySelector('.input-section').scrollIntoView({ behavior: 'smooth' });
}

// Delete inventory item
function deleteItem(id) {
    if (confirm(translations[currentLanguage].confirmDelete || 'Are you sure you want to delete this item?')) {
        inventory = inventory.filter(item => item.id !== id);
        updateInventory();
    }
}

// Export catalog
function exportCatalog(format) {
    // In a real app, this would generate and download a file
    alert(`${translations[currentLanguage].exporting || 'Exporting'} ${format.toUpperCase()} ${translations[currentLanguage].catalog || 'catalog'}...`);
    elements.exportModal.style.display = 'none';
    
    // Simulate download
    setTimeout(() => {
        alert(`${format.toUpperCase()} ${translations[currentLanguage].exportSuccess || 'catalog exported successfully!'}`);
    }, 1500);
}

// Reset form
function resetForm() {
    elements.productInput.value = '';
    elements.imageUpload.value = '';
    elements.imagePreview.innerHTML = '';
    elements.voiceFeedback.textContent = '';
    elements.aiTitle.textContent = '';
    elements.aiDescription.textContent = '';
    elements.aiCategory.innerHTML = '';
    elements.aiAttributes.innerHTML = '';
}

// Load sample inventory
function loadSampleInventory() {
    inventory = [
        {
            id: 1,
            title: "Organic Apples",
            description: "Fresh organic apples from our farm",
            categories: ["Fruits", "Organic"],
            attributes: ["Fresh", "Pesticide-Free"],
            stock: 8,
            lastUpdated: "2023-10-15"
        },
        {
            id: 2,
            title: "Handmade Pottery Mug",
            description: "Artisan-crafted ceramic mug",
            categories: ["Kitchenware", "Handmade"],
            attributes: ["Ceramic", "Microwave Safe"],
            stock: 15,
            lastUpdated: "2023-10-18"
        },
        {
            id: 3,
            title: "Wireless Earbuds",
            description: "Premium Bluetooth earbuds with charging case",
            categories: ["Electronics", "Audio"],
            attributes: ["Bluetooth", "Noise Cancelling"],
            stock: 22,
            lastUpdated: "2023-10-20"
        }
    ];
    
    updateInventory();
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', init);

// Make functions available globally for HTML onclick attributes
window.selectRole = selectRole;
window.setLanguage = setLanguage;
window.logout = logout;
window.editItem = editItem;
window.deleteItem = deleteItem;