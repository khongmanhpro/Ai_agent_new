// Configuration
const API_URL = '/api/chat';

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const statusIndicator = document.getElementById('statusIndicator');

// Auto-resize textarea
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Send message on Enter (Shift+Enter for new line)
chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Send button click
sendButton.addEventListener('click', sendMessage);

// Check API health on load
checkHealth();

// Remove empty state
function removeEmptyState() {
    const emptyState = chatMessages.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
}

// Add message to chat
function addMessage(text, isUser = false) {
    removeEmptyState();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString('vi-VN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show loading indicator
function showLoading() {
    removeEmptyState();
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot';
    loadingDiv.id = 'loadingIndicator';
    loadingDiv.innerHTML = `
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove loading indicator
function removeLoading() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) {
        loading.remove();
    }
}

// Show error message
function showError(message) {
    removeLoading();
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `❌ Lỗi: ${message}`;
    chatMessages.appendChild(errorDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update status indicator
function updateStatus(status) {
    statusIndicator.className = 'status-indicator';
    const statusText = statusIndicator.querySelector('.status-text');
    
    switch(status) {
        case 'connected':
            statusIndicator.classList.add('connected');
            statusText.textContent = 'Đã kết nối';
            break;
        case 'connecting':
            statusIndicator.classList.add('connecting');
            statusText.textContent = 'Đang kết nối...';
            break;
        case 'error':
            statusIndicator.classList.add('error');
            statusText.textContent = 'Lỗi kết nối';
            break;
    }
}

// Check API health
async function checkHealth() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            updateStatus('connected');
        } else {
            updateStatus('error');
        }
    } catch (error) {
        updateStatus('error');
    }
}

// Send message to API
async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }

    // Disable input and button
    chatInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message
    addMessage(message, true);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Show loading
    showLoading();
    updateStatus('connecting');

    try {
        console.log('📤 Sending message:', message);
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });

        console.log('📥 Response status:', response.status);

        if (!response.ok) {
            // Handle error response
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: { message: response.statusText } };
            }
            
            removeLoading();
            updateStatus('error');
            const errorMsg = errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`;
            showError(errorMsg);
            console.error('❌ Error response:', errorData);
            return;
        }

        const data = await response.json();
        console.log('✅ Response data:', data);

        removeLoading();
        updateStatus('connected');

        // Add bot response
        const botMessage = data.response || 'Xin lỗi, tôi không thể trả lời câu hỏi này.';
        addMessage(botMessage, false);
        
        // Show processing time if available
        if (data.processing_time) {
            console.log(`⏱️ Processing time: ${data.processing_time.toFixed(2)}s`);
        }
    } catch (error) {
        removeLoading();
        updateStatus('error');
        console.error('❌ Fetch error:', error);
        const errorMsg = error.message || 'Không thể kết nối đến server. Vui lòng kiểm tra lại.';
        showError(errorMsg);
    } finally {
        // Re-enable input and button
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

// Focus input on load
chatInput.focus();

