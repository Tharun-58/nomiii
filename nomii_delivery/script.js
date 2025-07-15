// script.js
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const deliveryForm = document.getElementById('delivery-form');
    const micButton = document.getElementById('mic-button');
    const voiceStatus = document.getElementById('voice-status');
    const generateOTP = document.getElementById('generate-otp');
    const otpDisplay = document.getElementById('otp-display');
    const langEn = document.getElementById('lang-en');
    const langTa = document.getElementById('lang-ta');
    const deliveryIdField = document.getElementById('delivery-id');
    const productField = document.getElementById('product');
    const supplierField = document.getElementById('supplier');
    const zoneField = document.getElementById('zone');
    const scheduledTimeField = document.getElementById('scheduled-time');
    const otpInput = document.getElementById('otp-input');
    
    // State variables
    let currentLanguage = 'en-IN';
    let recognition = null;
    let generatedOTP = null;
    let deliveryChart = null;
    
    // Initialize dashboard
    initDashboard();
    
    // Language switching
    langEn.addEventListener('click', () => {
        currentLanguage = 'en-IN';
        voiceStatus.textContent = 'Click mic to speak (English)';
    });
    
    langTa.addEventListener('click', () => {
        currentLanguage = 'ta-IN';
        voiceStatus.textContent = 'மைக்ரோஃபோனைக் கிளிக் செய்து பேசுங்கள் (தமிழ்)';
    });
    
    // OTP Generation
    generateOTP.addEventListener('click', () => {
        generatedOTP = Math.floor(1000 + Math.random() * 9000);
        otpDisplay.value = generatedOTP;
    });
    
    // Form Submission
    deliveryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const product = productField.value;
        const supplier = supplierField.value;
        const zone = zoneField.value;
        const scheduledTime = scheduledTimeField.value;
        const enteredOTP = otpInput.value;
        
        // Validate required fields
        if (!product || !supplier || !zone || !scheduledTime) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Validate OTP
        if (!generatedOTP || enteredOTP !== String(generatedOTP)) {
            alert('Please generate and enter a valid OTP');
            return;
        }
        
        // Create delivery object
        const deliveryData = {
            product,
            supplier,
            zone,
            scheduled_time: scheduledTime,
            otp: generatedOTP
        };
        
        try {
            // Send to backend
            const response = await fetch('/submit_delivery', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(deliveryData)
            });
            
            if (response.ok) {
                const result = await response.json();
                showNotification(`Delivery ${result.delivery_id} recorded successfully!`, 'success');
                
                // Reset form
                deliveryForm.reset();
                generatedOTP = null;
                otpDisplay.value = '';
                deliveryIdField.value = generateDeliveryId();
                
                // Update dashboard
                updateDashboard();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to submit delivery');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification(`Error: ${error.message}`, 'error');
        }
    });
    
    // Initialize dashboard
    function initDashboard() {
        // Initialize chart
        initChart();
        
        // Set current time as default for scheduled delivery
        const now = new Date();
        const timeString = now.toISOString().slice(0, 16);
        scheduledTimeField.value = timeString;
        
        // Auto-generate delivery ID
        deliveryIdField.value = generateDeliveryId();
        
        // Update dashboard with real data
        updateDashboard();
        
        // Set up periodic updates
        setInterval(updateDashboard, 30000); // Update every 30 seconds
    }
    
    // Generate a delivery ID
    function generateDeliveryId() {
        const timestamp = new Date().getTime().toString().slice(-6);
        return `NOMIID${timestamp}`;
    }
    
    // Initialize chart
    function initChart() {
        const ctx = document.getElementById('delivery-chart').getContext('2d');
        deliveryChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'On-Time Deliveries',
                    backgroundColor: 'rgba(46, 204, 113, 0.6)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 1
                }, {
                    label: 'Delayed Deliveries',
                    backgroundColor: 'rgba(243, 156, 18, 0.6)',
                    borderColor: 'rgba(243, 156, 18, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    // Update dashboard metrics
    async function updateDashboard() {
        try {
            // Get metrics from backend
            const response = await fetch('/metrics');
            if (!response.ok) throw new Error('Failed to fetch metrics');
            
            const metrics = await response.json();
            
            // Update metrics display
            document.getElementById('total-deliveries').textContent = metrics.total_deliveries;
            document.getElementById('success-rate').textContent = `${metrics.success_rate}%`;
            document.getElementById('on-time-rate').textContent = `${metrics.on_time_rate}%`;
            document.getElementById('avg-delay').textContent = `${metrics.avg_delay} min`;
            
            // Update delivery log
            updateDeliveryLog(metrics.recent_deliveries);
            
            // Update AI alerts
            updateAIAlerts(metrics.ai_alerts);
            
            // Update chart
            updateChart(metrics.delivery_trends);
        } catch (error) {
            console.error('Error updating dashboard:', error);
        }
    }
    
    // Update delivery log table
    function updateDeliveryLog(deliveries) {
        const tableBody = document.querySelector('#delivery-table tbody');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        deliveries.forEach(delivery => {
            const row = document.createElement('tr');
            
            // Format status badge
            let statusClass = '';
            if (delivery.status === 'On Time') statusClass = 'on-time';
            else if (delivery.status === 'Delayed') statusClass = 'delayed';
            else if (delivery.status === 'Failed') statusClass = 'failed';
            
            // Format timestamp
            const deliveryTime = new Date(delivery.actual_time);
            const timeString = deliveryTime.toLocaleString();
            
            row.innerHTML = `
                <td>${delivery.delivery_id}</td>
                <td>${delivery.product}</td>
                <td>${delivery.supplier}</td>
                <td>${delivery.zone}</td>
                <td>${timeString}</td>
                <td><span class="status ${statusClass}">${delivery.status}</span></td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    // Update AI alerts
    function updateAIAlerts(alerts) {
        const container = document.getElementById('ai-alerts-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${alert.type}`;
            
            alertDiv.innerHTML = `
                <div class="alert-icon">${alert.type === 'warning' ? '⚠️' : 'ℹ️'}</div>
                <div>
                    <strong>${alert.title}</strong>
                    <p>${alert.message}</p>
                </div>
            `;
            
            container.appendChild(alertDiv);
        });
    }
    
    // Update chart
    function updateChart(trends) {
        if (!deliveryChart) return;
        
        deliveryChart.data.labels = trends.labels;
        deliveryChart.data.datasets[0].data = trends.on_time;
        deliveryChart.data.datasets[1].data = trends.delayed;
        deliveryChart.update();
    }
    
    // Show notification
    function showNotification(message, type) {
        // In a real app, this would show a styled notification
        alert(`${type.toUpperCase()}: ${message}`);
    }
    
    // Voice Recognition Setup
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = () => {
            micButton.classList.add('listening');
            voiceStatus.textContent = currentLanguage === 'en-IN' 
                ? 'Listening...' 
                : 'கேட்கிறது...';
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            processVoiceCommand(transcript);
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            micButton.classList.remove('listening');
            voiceStatus.textContent = currentLanguage === 'en-IN' 
                ? 'Error: ' + event.error 
                : 'பிழை: ' + event.error;
        };
        
        recognition.onend = () => {
            micButton.classList.remove('listening');
            voiceStatus.textContent = currentLanguage === 'en-IN' 
                ? 'Click mic to speak' 
                : 'மைக்ரோஃபோனைக் கிளிக் செய்து பேசுங்கள்';
        };
        
        micButton.addEventListener('click', () => {
            try {
                recognition.lang = currentLanguage;
                recognition.start();
            } catch (error) {
                console.error('Error starting recognition:', error);
                voiceStatus.textContent = 'Error starting voice recognition';
            }
        });
    } else {
        micButton.disabled = true;
        voiceStatus.textContent = 'Voice input not supported in this browser';
    }
    
    // Process voice commands
    function processVoiceCommand(transcript) {
        console.log('Voice command:', transcript);
        
        // Tamil commands processing
        if (currentLanguage === 'ta-IN') {
            // Pattern for Tamil: "Delivery for [product] from [supplier]"
            const productMatch = transcript.match(/(?:பெட்டி|டெலிவரி|விநியோகம்) (?:க்கு|க்காக)? (.+?) (?:இலிருந்து|வழங்குநரிடமிருந்து)/i);
            const supplierMatch = transcript.match(/(?:இலிருந்து|வழங்குநரிடமிருந்து) (.+)/i);
            
            if (productMatch && supplierMatch) {
                productField.value = productMatch[1].trim();
                supplierField.value = supplierMatch[1].trim();
                generateOTP.click();
                showNotification('Voice command processed successfully!', 'success');
                return;
            }
        }
        
        // English commands processing
        const commandPattern = /(?:add|record) delivery (?:for )?(.+?) (?:from )?(.+)/i;
        const match = transcript.match(commandPattern);
        
        if (match) {
            productField.value = match[1].trim();
            supplierField.value = match[2].trim();
            generateOTP.click();
            showNotification('Voice command processed successfully!', 'success');
        } else {
            showNotification('Could not process voice command. Please try again.', 'warning');
        }
    }
});