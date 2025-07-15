// Global state
let currentLang = localStorage.getItem('artisanLang') || 'TA';
let isListening = false;
let recognition = null;
let products = [];
let userID = 'NOMII-A-' + Math.floor(1000 + Math.random() * 9000);

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Set user ID
    document.querySelector('.user-avatar').textContent = userID.charAt(0);
    document.querySelector('#user-id').textContent = userID;
    
    // Initialize language
    updateLanguage(currentLang);
    
    // Load initial data
    loadSampleData();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize charts
    initializeCharts();
    
    // Setup voice assistant
    initVoiceAssistant();
});

// Load sample data for demonstration
function loadSampleData() {
    products = [
        {
            id: 1,
            name: "காஞ்சிபுரம் பட்டுப் புடவை",
            category: "புடவைகள்",
            desc_ta: "தூய பட்டில் நெய்யப்பட்ட உயர்தர காஞ்சிபுரப் புடவை",
            desc_en: "Pure silk high-quality Kanchipuram saree",
            quantity: 14,
            price: 5250,
            timestamp: "2023-07-10"
        },
        {
            id: 2,
            name: "களிமண் கோப்பை",
            category: "மட்பாண்டம்",
            desc_ta: "பாரம்பரிய முறையில் செய்யப்பட்ட களிமண் கோப்பை",
            desc_en: "Traditionally crafted terracotta cup",
            quantity: 8,
            price: 350,
            timestamp: "2023-07-12"
        },
        {
            id: 3,
            name: "தஞ்சாவூர் பித்தளை குதிரை",
            category: "உலோகக் கைவினை",
            desc_ta: "பாரம்பரிய தஞ்சாவூர் பித்தளை குதிரை சிலை",
            desc_en: "Traditional Thanjavur brass horse statue",
            quantity: 3,
            price: 1850,
            timestamp: "2023-07-05"
        },
        {
            id: 4,
            name: "கரூர் கைத்தறி வேஷ்டி",
            category: "துணிகள்",
            desc_ta: "கரூர் பிராந்தியத்தின் பாரம்பரிய கைத்தறி வேஷ்டி",
            desc_en: "Traditional handloom veshti from Karur region",
            quantity: 22,
            price: 850,
            timestamp: "2023-07-15"
        },
        {
            id: 5,
            name: "செப்பு காப்பு",
            category: "நகைகள்",
            desc_ta: "பாரம்பரிய செப்பு கைக்காப்பு",
            desc_en: "Traditional copper bracelet",
            quantity: 5,
            price: 650,
            timestamp: "2023-07-08"
        }
    ];
    
    renderInventory();
    generateInsights();
}

// Initialize Charts
function initializeCharts() {
    // Sales Chart
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    window.salesChart = new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: ['ஜன', 'பிப்', 'மார்', 'ஏப்', 'மே', 'ஜூன்', 'ஜூலை'],
            datasets: [{
                label: currentLang === 'TA' ? 'மாத விற்பனை (₹)' : 'Monthly Sales (₹)',
                data: [85000, 102000, 98000, 115000, 124850, 110200, 132500],
                borderColor: '#8f94fb',
                backgroundColor: 'rgba(143, 148, 251, 0.1)',
                borderWidth: 3,
                pointBackgroundColor: '#ff7e5f',
                pointRadius: 5,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return currentLang === 'TA' ? 
                                `₹${context.parsed.y.toLocaleString()}` : 
                                `₹${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
    
    // Category Chart
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    window.categoryChart = new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
            labels: currentLang === 'TA' ? 
                ['புடவைகள்', 'மட்பாண்டம்', 'உலோகக் கைவினை', 'நகைகள்', 'பிற'] : 
                ['Sarees', 'Pottery', 'Metal Craft', 'Jewelry', 'Others'],
            datasets: [{
                data: [35, 20, 25, 15, 5],
                backgroundColor: [
                    '#4e54c8',
                    '#ff7e5f',
                    '#8f94fb',
                    '#4caf50',
                    '#ff9966'
                ],
                borderWidth: 0,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 15,
                        padding: 20
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// Initialize Voice Assistant
function initVoiceAssistant() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        document.getElementById('voice-status').textContent = currentLang === 'TA' ? 
            'உங்கள் உலாவி குரை அங்கீகரிப்பதை ஆதரிக்கவில்லை' : 
            'Your browser does not support speech recognition';
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 3;
    recognition.lang = currentLang === 'TA' ? 'ta-IN' : 'en-US';
    
    recognition.onstart = () => {
        isListening = true;
        document.querySelector('.voice-btn').classList.add('listening');
        document.getElementById('voice-status').innerHTML = currentLang === 'TA' ? 
            '<i class="fas fa-circle-notch fa-spin"></i> கேட்கிறது... உங்கள் கட்டளையைச் சொல்லுங்கள்' : 
            '<i class="fas fa-circle-notch fa-spin"></i> Listening... Speak now';
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        processVoiceCommand(transcript);
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        document.getElementById('voice-status').textContent = currentLang === 'TA' ? 
            'பிழை: ' + event.error : 
            'Error: ' + event.error;
        stopListening();
    };
    
    recognition.onend = () => {
        stopListening();
    };
}

// Stop listening and update UI
function stopListening() {
    isListening = false;
    document.querySelector('.voice-btn').classList.remove('listening');
}

// Process voice commands
function processVoiceCommand(transcript) {
    console.log('Voice command:', transcript);
    const voiceStatus = document.getElementById('voice-status');
    
    // Update status to show recognized command
    voiceStatus.textContent = currentLang === 'TA' ? 
        `அங்கீகரிக்கப்பட்டது: "${transcript}"` : 
        `Recognized: "${transcript}"`;
    
    // Simple command matching
    if (fuzzyMatch(transcript, 'புதிய பொருள் சேர்') || fuzzyMatch(transcript, 'add new product')) {
        setTimeout(() => {
            showAddProductModal();
            showToast(currentLang === 'TA' ? 'புதிய பொருள் பிரிவு திறக்கப்பட்டது' : 'Add product section opened');
        }, 1000);
    }
    else if (fuzzyMatch(transcript, 'குறைந்த சரக்கு காட்டு') || fuzzyMatch(transcript, 'show low stock')) {
        filterLowStock();
        showToast(currentLang === 'TA' ? 'குறைந்த சரக்கு பொருட்கள் காட்டப்படுகின்றன' : 'Showing low stock items');
    }
    else if (fuzzyMatch(transcript, 'விற்பனை அறிக்கை திற') || fuzzyMatch(transcript, 'open sales report')) {
        document.querySelector('.nav-item:nth-child(3)').click();
        showToast(currentLang === 'TA' ? 'விற்பனை பகுப்பாய்வு திறக்கப்பட்டது' : 'Sales analytics opened');
    }
    else if (transcript.includes('ரூபாய்') || transcript.includes('rupee')) {
        processProductCommand(transcript);
    }
    else {
        voiceStatus.textContent = currentLang === 'TA' ? 
            `கட்டளையை அங்கீகரிக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்` : 
            `Command not recognized. Please try again`;
    }
}

// Fuzzy matching for voice commands
function fuzzyMatch(input, target) {
    input = input.toLowerCase().replace(/[^\w\s]/gi, '');
    target = target.toLowerCase().replace(/[^\w\s]/gi, '');
    
    // Simple implementation for demonstration
    return input.includes(target) || target.includes(input);
}

// Process product addition command
function processProductCommand(transcript) {
    // Extract product details
    let productName = '';
    let quantity = 1;
    let price = 0;
    
    // Find numbers in the transcript
    const numbers = transcript.match(/\d+/g) || [];
    
    if (numbers.length >= 2) {
        quantity = parseInt(numbers[0]);
        price = parseInt(numbers[1]);
        
        // Extract product name by removing numbers and currency words
        productName = transcript
            .replace(/\d+/g, '')
            .replace(/ரூபாய்|rupees?|ரூ|rs|price/gi, '')
            .trim();
    } else if (numbers.length === 1) {
        price = parseInt(numbers[0]);
        productName = transcript
            .replace(/\d+/g, '')
            .replace(/ரூபாய்|rupees?|ரூ|rs|price/gi, '')
            .trim();
    } else {
        productName = transcript;
    }
    
    // Generate AI description
    const description = generateAIDescription(productName);
    
    // Create product object
    const newProduct = {
        id: products.length + 1,
        name: productName,
        category: predictCategory(productName),
        desc_ta: description.ta,
        desc_en: description.en,
        quantity: quantity,
        price: price,
        timestamp: new Date().toISOString().split('T')[0]
    };
    
    // Add to products array
    products.push(newProduct);
    
    // Update UI
    renderInventory();
    generateInsights();
    
    // Show success message
    const voiceStatus = document.getElementById('voice-status');
    voiceStatus.innerHTML += `<div style="margin-top: 10px; background: rgba(76, 175, 80, 0.2); padding: 10px; border-radius: 8px;">
        <i class="fas fa-check-circle"></i> ${currentLang === 'TA' ? 
            `"${productName}" வெற்றிகரமாக சேர்க்கப்பட்டது!` : 
            `"${productName}" added successfully!`}
    </div>`;
    
    showToast(currentLang === 'TA' ? 
        `புதிய பொருள் சேர்க்கப்பட்டது: ${productName}` : 
        `New product added: ${productName}`);
}

// Generate AI description
function generateAIDescription(productName) {
    const descriptions = {
        saree: {
            ta: "பாரம்பரியத் திறன்முறைகளால் உருவாக்கப்பட்ட அழகான பட்டுப் புடவை",
            en: "Beautiful silk saree crafted with traditional techniques"
        },
        cup: {
            ta: "பாரம்பரிய முறையில் செய்யப்பட்ட களிமண் கோப்பை",
            en: "Traditionally crafted terracotta cup"
        },
        statue: {
            ta: "சிக்கலான வடிவமைப்புகளுடன் பாரம்பரிய உலோக சிலை",
            en: "Traditional metal statue with intricate designs"
        },
        veshti: {
            ta: "கரூர் பிராந்தியத்தின் பாரம்பரிய கைத்தறி வேஷ்டி",
            en: "Traditional handloom veshti from Karur region"
        },
        jewelry: {
            ta: "பாரம்பரிய செப்பு நகை",
            en: "Traditional copper jewelry"
        },
        default: {
            ta: `அழகான கைவினை ${productName} உயர்தரப் பொருட்களால் செய்யப்பட்டது`,
            en: `Beautiful handmade ${productName} crafted with premium materials`
        }
    };
    
    // Simple matching for demo - in real app this would use an AI API
    if (productName.includes('புடவை') || productName.includes('saree')) {
        return descriptions.saree;
    } else if (productName.includes('கோப்பை') || productName.includes('cup')) {
        return descriptions.cup;
    } else if (productName.includes('சிலை') || productName.includes('statue')) {
        return descriptions.statue;
    } else if (productName.includes('வேஷ்டி') || productName.includes('veshti')) {
        return descriptions.veshti;
    } else if (productName.includes('நகை') || productName.includes('jewelry')) {
        return descriptions.jewelry;
    }
    
    return descriptions.default;
}

// Predict product category
function predictCategory(productName) {
    if (productName.includes('புடவை') || productName.includes('saree')) {
        return currentLang === 'TA' ? 'புடவைகள்' : 'Sarees';
    } else if (productName.includes('கோப்பை') || productName.includes('cup') || 
               productName.includes('பானை') || productName.includes('pot')) {
        return currentLang === 'TA' ? 'மட்பாண்டம்' : 'Pottery';
    } else if (productName.includes('சிலை') || productName.includes('statue') || 
               productName.includes('பிளேட்') || productName.includes('plate')) {
        return currentLang === 'TA' ? 'உலோகக் கைவினை' : 'Metal Craft';
    } else if (productName.includes('வேஷ்டி') || productName.includes('veshti') || 
               productName.includes('துணி') || productName.includes('cloth')) {
        return currentLang === 'TA' ? 'துணிகள்' : 'Textiles';
    } else if (productName.includes('நகை') || productName.includes('jewelry')) {
        return currentLang === 'TA' ? 'நகைகள்' : 'Jewelry';
    }
    
    return currentLang === 'TA' ? 'பிற' : 'Others';
}

// Setup event listeners
function setupEventListeners() {
    // Language toggle
    document.getElementById('lang-toggle').addEventListener('click', toggleLanguage);
    
    // Voice button
    document.querySelector('.voice-btn').addEventListener('click', toggleVoicePanel);
    document.getElementById('voice-close').addEventListener('click', closeVoicePanel);
    document.getElementById('start-listen').addEventListener('click', startVoiceRecognition);
    
    // Navigation
    document.querySelectorAll('.nav-item').forEach((item, index) => {
        item.addEventListener('click', () => {
            // Remove active class from all items
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            item.classList.add('active');
            
            // For demo purposes, show a toast
            const navText = item.querySelector('span').textContent;
            showToast(`${currentLang === 'TA' ? 'தேர்ந்தெடுக்கப்பட்டது:' : 'Selected:'} ${navText}`);
        });
    });
    
    // Add product button
    document.querySelector('.card-actions .btn-primary').addEventListener('click', showAddProductModal);
    
    // Filter button
    document.querySelector('.btn-outline').addEventListener('click', showFilterOptions);
    
    // Action buttons in table
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const productId = parseInt(e.target.closest('tr').dataset.id);
            editProduct(productId);
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const productId = parseInt(e.target.closest('tr').dataset.id);
            deleteProduct(productId);
        });
    });
}

// Toggle language
function toggleLanguage() {
    currentLang = currentLang === 'TA' ? 'EN' : 'TA';
    localStorage.setItem('artisanLang', currentLang);
    updateLanguage(currentLang);
    
    // Update charts
    if (window.salesChart) {
        window.salesChart.destroy();
    }
    if (window.categoryChart) {
        window.categoryChart.destroy();
    }
    initializeCharts();
    
    renderInventory();
    generateInsights();
    
    showToast(currentLang === 'TA' ? 
        'மொழி தமிழாக மாற்றப்பட்டது' : 
        'Language changed to English');
}

// Update UI language
function updateLanguage(lang) {
    // Update UI text elements
    const elements = {
        'welcome-title': lang === 'TA' ? 'வரவேற்கிறோம், தமிழன்!' : 'Welcome, Artisan!',
        'welcome-text': lang === 'TA' ? 'உங்கள் கைவினைப் பொருட்களை நிர்வகிக்க இந்த ஸ்மார்ட் டாஷ்போர்டு உதவும். குரல் உள்ளீடு, AI பரிந்துரைகள் மற்றும் எளிய நிர்வாகம் ஆகியவற்றைப் பயன்படுத்தி உங்கள் வணிகத்தை வளர்க்கவும்.' : 'This smart dashboard helps you manage your handicraft products. Use voice input, AI suggestions, and simple management to grow your business.',
        'video-guide': lang === 'TA' ? 'வழிகாட்டி வீடியோவைப் பார்க்கவும்' : 'View Guide Video',
        'products-title': lang === 'TA' ? 'உங்கள் பொருட்கள்' : 'Your Products',
        'insights-title': lang === 'TA' ? 'AI பரிந்துரைகள்' : 'AI Insights',
        'sales-title': lang === 'TA' ? 'விற்பனை பகுப்பாய்வு' : 'Sales Analytics',
        'category-title': lang === 'TA' ? 'வகை வாரியான விற்பனை' : 'Category Sales',
        'new-product': lang === 'TA' ? 'புதிய பொருள்' : 'New Product',
        'filter': lang === 'TA' ? 'வடிகட்டு' : 'Filter',
        'voice-title': lang === 'TA' ? 'குரை உதவியாளர்' : 'Voice Assistant',
        'voice-status': lang === 'TA' ? 'குரல் உள்ளீட்டிற்காக காத்திருக்கிறது...' : 'Waiting for voice input...',
        'start-listen': lang === 'TA' ? 'கேட்கத் தொடங்கு' : 'Start Listening',
        'commands-title': lang === 'TA' ? 'எடுத்துக்காட்டு கட்டளைகள்:' : 'Example Commands:'
    };
    
    Object.keys(elements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = elements[id];
        }
    });
    
    // Update button texts
    document.querySelector('#start-listen').innerHTML = lang === 'TA' ? 
        '<i class="fas fa-microphone"></i> கேட்கத் தொடங்கு' : 
        '<i class="fas fa-microphone"></i> Start Listening';
    
    // Update nav items
    const navItems = document.querySelectorAll('.nav-item span');
    if (lang === 'TA') {
        navItems[0].textContent = 'டாஷ்போர்டு';
        navItems[1].textContent = 'பொருட்கள்';
        navItems[2].textContent = 'பகுப்பாய்வு';
        navItems[3].textContent = 'AI பரிந்துரைகள்';
        navItems[4].textContent = 'அமைப்புகள்';
        navItems[5].textContent = 'பொருள் சேர்';
        navItems[6].textContent = 'தரவு ஏற்றுமதி';
        navItems[7].textContent = 'உதவி மையம்';
    } else {
        navItems[0].textContent = 'Dashboard';
        navItems[1].textContent = 'Products';
        navItems[2].textContent = 'Analytics';
        navItems[3].textContent = 'AI Insights';
        navItems[4].textContent = 'Settings';
        navItems[5].textContent = 'Add Product';
        navItems[6].textContent = 'Export Data';
        navItems[7].textContent = 'Help Center';
    }
    
    // Update table headers
    const tableHeaders = document.querySelectorAll('.inventory-table th');
    if (lang === 'TA') {
        tableHeaders[0].textContent = 'பொருள்';
        tableHeaders[1].textContent = 'வகை';
        tableHeaders[2].textContent = 'அளவு';
        tableHeaders[3].textContent = 'விலை';
        tableHeaders[4].textContent = 'நிலை';
        tableHeaders[5].textContent = 'செயல்கள்';
    } else {
        tableHeaders[0].textContent = 'Product';
        tableHeaders[1].textContent = 'Category';
        tableHeaders[2].textContent = 'Quantity';
        tableHeaders[3].textContent = 'Price';
        tableHeaders[4].textContent = 'Status';
        tableHeaders[5].textContent = 'Actions';
    }
}

// Toggle voice panel
function toggleVoicePanel() {
    const voicePanel = document.getElementById('voice-panel');
    if (voicePanel.style.display === 'block') {
        closeVoicePanel();
    } else {
        voicePanel.style.display = 'block';
    }
}

// Close voice panel
function closeVoicePanel() {
    document.getElementById('voice-panel').style.display = 'none';
    if (isListening && recognition) {
        recognition.stop();
    }
}

// Start voice recognition
function startVoiceRecognition() {
    if (recognition) {
        recognition.start();
    }
}

// Show add product modal
function showAddProductModal() {
    // For demo, show a toast
    showToast(currentLang === 'TA' ? 
        'புதிய பொருள் சேர்க்கும் படிவம் திறக்கப்பட்டது' : 
        'Add new product form opened');
}

// Show filter options
function showFilterOptions() {
    // For demo, show a toast
    showToast(currentLang === 'TA' ? 
        'வடிகட்டு விருப்பங்கள் காட்டப்படுகின்றன' : 
        'Showing filter options');
}

// Filter low stock items
function filterLowStock() {
    const lowStockProducts = products.filter(p => p.quantity < 5);
    renderInventory(lowStockProducts);
    
    // Show toast
    showToast(currentLang === 'TA' ? 
        `குறைந்த சரக்கு பொருட்கள் காட்டப்படுகின்றன (${lowStockProducts.length})` : 
        `Showing low stock items (${lowStockProducts.length})`);
}

// Render inventory
function renderInventory(productsToShow = products) {
    const tableBody = document.querySelector('.inventory-table tbody');
    tableBody.innerHTML = '';
    
    if (productsToShow.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 2rem;">
                    ${currentLang === 'TA' ? 
                        'பொருட்கள் எதுவும் கிடைக்கவில்லை' : 
                        'No products found'}
                </td>
            </tr>
        `;
        return;
    }
    
    productsToShow.forEach(product => {
        const row = document.createElement('tr');
        row.dataset.id = product.id;
        
        // Determine stock status
        let stockStatus = '';
        let stockClass = '';
        if (product.quantity < 5) {
            stockStatus = currentLang === 'TA' ? 'குறைவு' : 'Low';
            stockClass = 'stock-low';
        } else if (product.quantity < 10) {
            stockStatus = currentLang === 'TA' ? 'சராசரி' : 'Medium';
            stockClass = 'stock-medium';
        } else {
            stockStatus = currentLang === 'TA' ? 'போதுமானது' : 'Sufficient';
            stockClass = 'stock-high';
        }
        
        // Get icon based on category
        let icon = 'fa-box';
        if (product.category.includes('புடவை') || product.category.includes('Saree')) {
            icon = 'fa-tshirt';
        } else if (product.category.includes('மட்பாண்ட') || product.category.includes('Pottery')) {
            icon = 'fa-mug-hot';
        } else if (product.category.includes('உலோக') || product.category.includes('Metal')) {
            icon = 'fa-gem';
        } else if (product.category.includes('துணி') || product.category.includes('Textile')) {
            icon = 'fa-rug';
        } else if (product.category.includes('நகை') || product.category.includes('Jewelry')) {
            icon = 'fa-ring';
        }
        
        row.innerHTML = `
            <td>
                <div class="product-cell">
                    <div class="product-img">
                        <i class="fas ${icon}"></i>
                    </div>
                    <div class="product-info">
                        <div class="product-name">${product.name}</div>
                        <div class="product-category">${product.category}</div>
                    </div>
                </div>
            </td>
            <td>${product.category}</td>
            <td>${product.quantity}</td>
            <td>₹${product.price.toLocaleString()}</td>
            <td>
                <span class="stock-badge ${stockClass}">${stockStatus}</span>
            </td>
            <td>
                <div class="action-cell">
                    <div class="action-btn edit-btn">
                        <i class="fas fa-edit"></i>
                    </div>
                    <div class="action-btn delete-btn">
                        <i class="fas fa-trash"></i>
                    </div>
                </div>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners to action buttons
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const productId = parseInt(e.target.closest('tr').dataset.id);
            editProduct(productId);
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const productId = parseInt(e.target.closest('tr').dataset.id);
            deleteProduct(productId);
        });
    });
}

// Edit product
function editProduct(productId) {
    const product = products.find(p => p.id === productId);
    if (product) {
        showToast(currentLang === 'TA' ? 
            `திருத்தம்: ${product.name}` : 
            `Editing: ${product.name}`);
        
        // In a real app, this would open an edit modal
    }
}

// Delete product
function deleteProduct(productId) {
    const product = products.find(p => p.id === productId);
    if (product) {
        if (confirm(currentLang === 'TA' ? 
            `"${product.name}" நீக்க விரும்புகிறீர்களா?` : 
            `Are you sure you want to delete "${product.name}"?`)) {
            
            products = products.filter(p => p.id !== productId);
            renderInventory();
            generateInsights();
            
            showToast(currentLang === 'TA' ? 
                `"${product.name}" நீக்கப்பட்டது` : 
                `"${product.name}" deleted`);
        }
    }
}

// Generate AI insights
function generateInsights() {
    const insightsContainer = document.getElementById('insights-container');
    insightsContainer.innerHTML = '';
    
    // Low stock insight
    const lowStockProducts = products.filter(p => p.quantity < 5);
    if (lowStockProducts.length > 0) {
        const productNames = lowStockProducts.map(p => p.name).join(', ');
        insightsContainer.innerHTML += `
            <div class="insight-card warning">
                <div class="insight-header">
                    <div class="insight-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="insight-title">
                        ${currentLang === 'TA' ? 'குறைந்த சரக்கு எச்சரிக்கை' : 'Low Stock Warning'}
                    </div>
                </div>
                <div class="insight-content">
                    ${currentLang === 'TA' ? 
                        `${productNames} - இவற்றின் அளவு குறைவாக உள்ளது. உடனடியாக உற்பத்தி செய்ய பரிந்துரைக்கப்படுகிறது.` : 
                        `${productNames} - are running low. Consider restocking immediately.`}
                </div>
                <div class="insight-actions">
                    <button class="btn btn-outline">
                        ${currentLang === 'TA' ? 'விவரங்கள்' : 'Details'}
                    </button>
                </div>
            </div>
        `;
    }
    
    // High demand insight
    const highDemandProducts = products.filter(p => p.quantity < 10 && p.price < 1000);
    if (highDemandProducts.length > 0) {
        const productNames = highDemandProducts.map(p => p.name).join(', ');
        insightsContainer.innerHTML += `
            <div class="insight-card success">
                <div class="insight-header">
                    <div class="insight-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="insight-title">
                        ${currentLang === 'TA' ? 'அதிக தேவை உள்ள பொருள்' : 'High Demand Products'}
                    </div>
                </div>
                <div class="insight-content">
                    ${currentLang === 'TA' ? 
                        `${productNames} - இவற்றிற்கு சமீபத்தில் அதிக தேவை உள்ளது. உற்பத்தியை அதிகரிக்கலாம்.` : 
                        `${productNames} - have high recent demand. Consider increasing production.`}
                </div>
                <div class="insight-actions">
                    <button class="btn btn-outline">
                        ${currentLang === 'TA' ? 'பகுப்பாய்வு' : 'Analyze'}
                    </button>
                </div>
            </div>
        `;
    }
    
    // Pricing insight
    const expensiveProducts = products.filter(p => p.price > 5000);
    if (expensiveProducts.length > 0) {
        const productNames = expensiveProducts.map(p => p.name).join(', ');
        insightsContainer.innerHTML += `
            <div class="insight-card info">
                <div class="insight-header">
                    <div class="insight-icon">
                        <i class="fas fa-tags"></i>
                    </div>
                    <div class="insight-title">
                        ${currentLang === 'TA' ? 'விலை சரிசெய்தல்' : 'Pricing Adjustment'}
                    </div>
                </div>
                <div class="insight-content">
                    ${currentLang === 'TA' ? 
                        `${productNames} - இவற்றின் சராசரி சந்தை விலையுடன் ஒப்பிடும்போது உங்கள் விலை அதிகமாக உள்ளது.` : 
                        `${productNames} - your pricing is higher compared to market average.`}
                </div>
                <div class="insight-actions">
                    <button class="btn btn-outline">
                        ${currentLang === 'TA' ? 'சரிசெய்' : 'Adjust'}
                    </button>
                </div>
            </div>
        `;
    }
    
    // Festival insight
    insightsContainer.innerHTML += `
        <div class="insight-card info">
            <div class="insight-header">
                <div class="insight-icon">
                    <i class="fas fa-calendar-alt"></i>
                </div>
                <div class="insight-title">
                    ${currentLang === 'TA' ? 'திருவிழா தயாரிப்பு' : 'Festival Preparation'}
                </div>
            </div>
            <div class="insight-content">
                ${currentLang === 'TA' ? 
                    'தீபாவளிக்கு 45 நாட்கள் மீதமுள்ளன. இந்த காலகட்டத்தில் பட்டுப் புடவைகள் மற்றும் களிமண் விளக்குகளுக்கு அதிக தேவை உள்ளது.' : 
                    'Diwali is in 45 days. Sarees and terracotta lamps have high demand during this period.'}
            </div>
            <div class="insight-actions">
                <button class="btn btn-outline">
                    ${currentLang === 'TA' ? 'திட்டமிடு' : 'Plan'}
                </button>
            </div>
        </div>
    `;
    
    // Add event listeners to insight buttons
    document.querySelectorAll('.insight-actions .btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const insightTitle = btn.closest('.insight-card').querySelector('.insight-title').textContent;
            showToast(`${currentLang === 'TA' ? 'தேர்ந்தெடுக்கப்பட்டது:' : 'Selected:'} ${insightTitle}`);
        });
    });
}

// Show toast notification
function showToast(message, isError = false) {
    // Create toast container if not exists
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.bottom = '20px';
        toastContainer.style.left = '50%';
        toastContainer.style.transform = 'translateX(-50%)';
        toastContainer.style.zIndex = '1000';
        toastContainer.style.display = 'flex';
        toastContainer.style.flexDirection = 'column';
        toastContainer.style.alignItems = 'center';
        toastContainer.style.gap = '10px';
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast ' + (isError ? 'error' : '');
    toast.textContent = message;
    toast.style.padding = '12px 24px';
    toast.style.background = isError ? 'rgba(255, 126, 95, 0.9)' : 'rgba(78, 84, 200, 0.9)';
    toast.style.color = 'white';
    toast.style.borderRadius = '30px';
    toast.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s, bottom 0.3s';
    
    toastContainer.appendChild(toast);
    
    // Trigger reflow
    toast.offsetHeight;
    
    // Show toast
    toast.style.opacity = '1';
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}