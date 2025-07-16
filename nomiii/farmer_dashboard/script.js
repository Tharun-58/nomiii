// Sample data arrays
let farmerData = [
    { id: 1, crop: "Tomato", qty: 100, price: 35, sowing: "2025-05-10", harvest: "2025-07-18", location: "Salem", status: "warning" },
    { id: 2, crop: "Onion", qty: 250, price: 32, sowing: "2025-05-01", harvest: "2025-07-25", location: "Chennai", status: "success" },
    { id: 3, crop: "Potato", qty: 300, price: 22, sowing: "2025-04-20", harvest: "2025-07-10", location: "Coimbatore", status: "danger" },
    { id: 4, crop: "Chili", qty: 80, price: 55, sowing: "2025-06-05", harvest: "2025-08-20", location: "Madurai", status: "success" },
    { id: 5, crop: "Wheat", qty: 500, price: 28, sowing: "2025-03-15", harvest: "2025-07-05", location: "Punjab", status: "danger" }
];

// Market data for AI suggestions
const marketRates = {
    "Tomato": 40,
    "Onion": 38,
    "Potato": 25,
    "Chili": 60,
    "Wheat": 30,
    "Rice": 35,
    "Corn": 22
};

const regionDemand = {
    "Tomato": +0.15,
    "Onion": -0.05,
    "Potato": +0.08,
    "Chili": +0.20,
    "Wheat": -0.02
};

// Buyers data
const buyers = [
    { name: "FreshBasket", crop: "Tomato", requiredQty: 150, location: "Chennai" },
    { name: "GreenGrocers", crop: "Onion", requiredQty: 200, location: "Bangalore" },
    { name: "SpiceMart", crop: "Chili", requiredQty: 100, location: "Coimbatore" },
    { name: "FarmToTable", crop: "Potato", requiredQty: 300, location: "Hyderabad" }
];

// DOM Elements
const produceTableBody = document.getElementById('produceTableBody');
const addCropBtn = document.getElementById('addCropBtn');
const suggestPriceBtn = document.getElementById('suggestPriceBtn');
const exportBtn = document.getElementById('exportBtn');
const searchCrop = document.getElementById('searchCrop');
const voiceCropBtn = document.getElementById('voiceCropBtn');
const voiceLocationBtn = document.getElementById('voiceLocationBtn');
const languageSelector = document.getElementById('languageSelector');
const aiAlertsContainer = document.getElementById('aiAlertsContainer');
const currentDateElement = document.getElementById('currentDate');

// Initialize Speech Recognition
let recognition;
let currentVoiceField;

// Set current date
function setCurrentDate() {
    const today = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    currentDateElement.textContent = `Today is ${today.toLocaleDateString('en-US', options)}`;
}

// Initialize the dashboard
function initDashboard() {
    setCurrentDate();
    renderProduceTable();
    setupEventListeners();
    checkHarvestAlerts();
    updateAIAlerts();
    updateStatsCards();
}

// Render produce table
function renderProduceTable() {
    produceTableBody.innerHTML = '';
    
    const searchTerm = searchCrop.value.toLowerCase();
    const filteredData = farmerData.filter(item => 
        item.crop.toLowerCase().includes(searchTerm) || 
        item.location.toLowerCase().includes(searchTerm)
    );
    
    filteredData.forEach(item => {
        const row = document.createElement('tr');
        
        // Add expiring soon class
        if (item.status === 'warning' || item.status === 'danger') {
            row.classList.add('expiring-soon');
        }
        
        // Calculate days until harvest
        const harvestDate = new Date(item.harvest);
        const today = new Date();
        const diffTime = harvestDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        let statusText, statusClass;
        if (diffDays <= 7 && diffDays > 0) {
            statusText = `Harvest in ${diffDays} days`;
            statusClass = 'status-warning';
        } else if (diffDays <= 0) {
            statusText = 'Harvest Now!';
            statusClass = 'status-danger';
        } else {
            statusText = 'Growing';
            statusClass = 'status-success';
        }
        
        row.innerHTML = `
            <td>${item.crop}</td>
            <td>${item.qty} kg</td>
            <td>₹${item.price}/kg</td>
            <td>${formatDate(item.sowing)}</td>
            <td>${formatDate(item.harvest)}</td>
            <td>${item.location}</td>
            <td><span class="status ${statusClass}">${statusText}</span></td>
            <td>
                <button class="action-btn edit-btn" data-id="${item.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn delete-btn" data-id="${item.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        
        produceTableBody.appendChild(row);
    });
    
    // Add edit/delete event listeners
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', () => editCrop(btn.dataset.id));
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteCrop(btn.dataset.id));
    });
}

// Format date for display
function formatDate(dateString) {
    const options = { day: 'numeric', month: 'short', year: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

// Setup event listeners
function setupEventListeners() {
    addCropBtn.addEventListener('click', addNewCrop);
    suggestPriceBtn.addEventListener('click', suggestPrice);
    exportBtn.addEventListener('click', exportToCSV);
    searchCrop.addEventListener('input', renderProduceTable);
    
    // Voice recognition setup
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            if (currentVoiceField) {
                currentVoiceField.value = transcript;
            }
            voiceCropBtn.classList.remove('listening');
            voiceLocationBtn.classList.remove('listening');
        };
        
        recognition.onerror = function() {
            voiceCropBtn.classList.remove('listening');
            voiceLocationBtn.classList.remove('listening');
        };
        
        voiceCropBtn.addEventListener('click', () => {
            recognition.lang = getLanguageCode();
            recognition.start();
            voiceCropBtn.classList.add('listening');
            currentVoiceField = document.getElementById('cropName');
        });
        
        voiceLocationBtn.addEventListener('click', () => {
            recognition.lang = getLanguageCode();
            recognition.start();
            voiceLocationBtn.classList.add('listening');
            currentVoiceField = document.getElementById('location');
        });
    } else {
        voiceCropBtn.style.display = 'none';
        voiceLocationBtn.style.display = 'none';
        showAlert("Voice recognition is not supported in this browser. Please use Chrome or Edge.", 'warning');
    }
    
    // Language change
    languageSelector.addEventListener('change', changeLanguage);
}

// Add new crop
function addNewCrop() {
    const cropName = document.getElementById('cropName').value.trim();
    const cropQty = document.getElementById('cropQuantity').value;
    const cropPrice = document.getElementById('cropPrice').value;
    const sowingDate = document.getElementById('sowingDate').value;
    const harvestDate = document.getElementById('harvestDate').value;
    const location = document.getElementById('location').value.trim();
    
    if (!cropName || !cropQty || !cropPrice || !sowingDate || !harvestDate || !location) {
        showAlert("Please fill in all fields", 'warning');
        return;
    }
    
    const newCrop = {
        id: Date.now(), // Generate unique ID
        crop: cropName,
        qty: parseInt(cropQty),
        price: parseInt(cropPrice),
        sowing: sowingDate,
        harvest: harvestDate,
        location: location,
        status: "success"
    };
    
    farmerData.push(newCrop);
    renderProduceTable();
    
    // Clear form
    document.getElementById('cropName').value = '';
    document.getElementById('cropQuantity').value = '';
    document.getElementById('cropPrice').value = '';
    document.getElementById('sowingDate').value = '';
    document.getElementById('harvestDate').value = '';
    document.getElementById('location').value = '';
    
    // Show success message
    showAlert(`${cropName} added successfully!`, 'success');
    
    // Update stats and alerts
    updateAIAlerts();
    updateStatsCards();
}

// Edit crop
function editCrop(id) {
    const crop = farmerData.find(item => item.id === parseInt(id));
    if (crop) {
        // Fill the form with the crop data
        document.getElementById('cropName').value = crop.crop;
        document.getElementById('cropQuantity').value = crop.qty;
        document.getElementById('cropPrice').value = crop.price;
        document.getElementById('sowingDate').value = crop.sowing;
        document.getElementById('harvestDate').value = crop.harvest;
        document.getElementById('location').value = crop.location;
        
        // Remove the crop from the list
        farmerData = farmerData.filter(item => item.id !== parseInt(id));
        renderProduceTable();
        
        showAlert(`Editing ${crop.crop}. Update the details and click "Add Crop" to save changes.`, 'info');
    }
}

// Delete crop
function deleteCrop(id) {
    const crop = farmerData.find(item => item.id === parseInt(id));
    if (crop && confirm(`Are you sure you want to delete ${crop.crop}?`)) {
        farmerData = farmerData.filter(item => item.id !== parseInt(id));
        renderProduceTable();
        showAlert("Crop deleted successfully", 'success');
        
        // Update stats and alerts
        updateAIAlerts();
        updateStatsCards();
    }
}

// Suggest price using AI
function suggestPrice() {
    const cropName = document.getElementById('cropName').value.trim();
    if (!cropName) {
        showAlert("Please enter a crop name first", 'warning');
        return;
    }
    
    const suggestedPrice = getSuggestedPrice(cropName);
    if (suggestedPrice) {
        document.getElementById('cropPrice').value = suggestedPrice;
        showAlert(`Suggested price for ${cropName}: ₹${suggestedPrice}/kg`, 'success');
    } else {
        showAlert(`No market data available for ${cropName}`, 'warning');
    }
}

// AI function to suggest price
function getSuggestedPrice(crop) {
    const basePrice = marketRates[crop];
    if (!basePrice) return null;
    
    const modifier = regionDemand[crop] || 0;
    return Math.round(basePrice * (1 + modifier));
}

// Check harvest alerts
function checkHarvestAlerts() {
    const today = new Date();
    let hasAlerts = false;
    
    farmerData.forEach(item => {
        const harvestDate = new Date(item.harvest);
        const diffTime = harvestDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays <= 7 && diffDays > 0) {
            item.status = "warning";
            hasAlerts = true;
        } else if (diffDays <= 0) {
            item.status = "danger";
            hasAlerts = true;
        } else {
            item.status = "success";
        }
    });
    
    if (hasAlerts) {
        renderProduceTable();
    }
}

// Update stats cards
function updateStatsCards() {
    // Crop count
    document.getElementById('cropCount').textContent = farmerData.length;
    
    // Harvest alert count
    const today = new Date();
    const alertCount = farmerData.filter(item => {
        const harvestDate = new Date(item.harvest);
        const diffTime = harvestDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= 7;
    }).length;
    document.getElementById('alertCount').textContent = alertCount;
    
    // Average price
    if (farmerData.length > 0) {
        const total = farmerData.reduce((sum, item) => sum + item.price, 0);
        const avg = Math.round(total / farmerData.length);
        document.getElementById('avgPrice').textContent = `₹${avg}/kg`;
    }
    
    // Buyer offers
    const buyerOffers = buyers.length;
    document.getElementById('buyerOffers').textContent = buyerOffers;
}

// Update AI alerts
function updateAIAlerts() {
    aiAlertsContainer.innerHTML = '';
    
    // Harvest alerts
    const today = new Date();
    farmerData.forEach(item => {
        const harvestDate = new Date(item.harvest);
        const diffTime = harvestDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays <= 7 && diffDays > 0) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'ai-alert alert-warning';
            alertDiv.innerHTML = `
                <div class="alert-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div>
                    <strong>Harvest Alert:</strong> Your ${item.crop} crop in ${item.location} is ready for harvest in ${diffDays} days. Contact buyers now!
                </div>
            `;
            aiAlertsContainer.appendChild(alertDiv);
        }
    });
    
    // Price suggestions
    farmerData.forEach(item => {
        const suggestedPrice = getSuggestedPrice(item.crop);
        if (suggestedPrice && suggestedPrice > item.price) {
            const increasePercent = Math.round(((suggestedPrice - item.price) / item.price) * 100);
            const alertDiv = document.createElement('div');
            alertDiv.className = 'ai-alert alert-success';
            alertDiv.innerHTML = `
                <div class="alert-icon">
                    <i class="fas fa-lightbulb"></i>
                </div>
                <div>
                    <strong>Smart Suggestion:</strong> Current market rate for ${item.crop} is ₹${suggestedPrice}/kg (${increasePercent}% higher than your listed price). Consider updating your price.
                </div>
            `;
            aiAlertsContainer.appendChild(alertDiv);
        }
    });
    
    // Buyer match suggestions
    if (farmerData.length > 0) {
        const potentialBuyers = buyers.filter(buyer => {
            return farmerData.some(item => 
                item.crop === buyer.crop && 
                item.qty <= buyer.requiredQty
            );
        });
        
        if (potentialBuyers.length > 0) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'ai-alert alert-info';
            alertDiv.innerHTML = `
                <div class="alert-icon">
                    <i class="fas fa-handshake"></i>
                </div>
                <div>
                    <strong>Buyer Match:</strong> Found ${potentialBuyers.length} potential buyers for your crops. Check the Buyers section for details.
                </div>
            `;
            aiAlertsContainer.appendChild(alertDiv);
        }
    }
    
    // Crop rotation suggestions
    if (farmerData.some(item => item.crop === "Wheat")) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'ai-alert alert-success';
        alertDiv.innerHTML = `
            <div class="alert-icon">
                <i class="fas fa-seedling"></i>
            </div>
            <div>
                <strong>Crop Rotation Tip:</strong> After harvesting Wheat, consider planting Legumes like Chickpeas or Lentils to improve soil nitrogen levels.
            </div>
        `;
        aiAlertsContainer.appendChild(alertDiv);
    }
}

// Export to CSV
function exportToCSV() {
    let csv = 'Crop Name,Quantity,Price (₹/kg),Sowing Date,Harvest Date,Market Location\n';
    
    farmerData.forEach(item => {
        csv += `${item.crop},${item.qty},${item.price},${item.sowing},${item.harvest},${item.location}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `farmers_data_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showAlert("Data exported to CSV successfully", 'success');
}

// Get language code for speech recognition
function getLanguageCode() {
    const lang = languageSelector.value;
    const codes = {
        'en': 'en-IN',
        'hi': 'hi-IN',
        'ta': 'ta-IN',
        'te': 'te-IN',
        'kn': 'kn-IN',
        'ml': 'ml-IN',
        'bn': 'bn-IN'
    };
    return codes[lang] || 'en-IN';
}

// Change language
function changeLanguage() {
    const lang = languageSelector.value;
    // In a real app, this would update the UI language
    showAlert(`Language changed to ${languageSelector.options[languageSelector.selectedIndex].text}`, 'info');
}

// Show alert message
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `ai-alert alert-${type}`;
    alertDiv.innerHTML = `
        <div class="alert-icon">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 
                             type === 'warning' ? 'fa-exclamation-triangle' : 
                             type === 'danger' ? 'fa-exclamation-circle' : 
                             'fa-info-circle'}"></i>
        </div>
        <div>${message}</div>
    `;
    
    // Add to document
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(alertDiv, document.querySelector('.section'));
    
    // Remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Initialize the dashboard when the page loads
window.addEventListener('DOMContentLoaded', initDashboard);