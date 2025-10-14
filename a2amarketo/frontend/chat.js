// API Configuration
// const API_BASE_URL = 'http://localhost:5000/api';
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api'  // Changed: Added /api
    : 'YOUR_BACKEND_CLOUD_RUN_URL/api';  // Changed: Added /api

// State Management
let currentUser = null;
let currentSessionId = generateSessionId();
let messageCount = 0;

// Utility Functions
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    const container = document.getElementById('notifications');
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

async function apiRequest(url, options = {}) {
    const accessToken = sessionStorage.getItem('accessToken');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(accessToken && { 'Authorization': `Bearer ${accessToken}` })
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (response.status === 401) {
            // Token expired, redirect to login
            sessionStorage.removeItem('accessToken');
            sessionStorage.removeItem('refreshToken');
            window.location.href = 'login.html';
            return null;
        }
        
        // 🆕 Handle 403 Permission Denied (RBAC)
        if (response.status === 403) {
            const error = await response.json();
            const errorMessage = error.detail || 'Permission denied';
            
            // Show prominent permission denied message
            showPermissionDeniedMessage(errorMessage);
            throw new Error(errorMessage);
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
        
        return response;
    } catch (error) {
        // Don't show duplicate notification for 403 errors
        if (!error.message.includes('Permission denied')) {
            showNotification('Request failed: ' + error.message, 'error');
        }
        throw error;
    }
}

// 🆕 UPDATED: Show permission denied message ONLY in chat (no popup notification)
function showPermissionDeniedMessage(message) {
    // REMOVED: showNotification(message, 'error');
    
    // Add to chat as a system message with special styling
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system permission-denied';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = `
        <strong>⚠️ Permission Denied</strong><br><br>
        ${message}<br><br>
        <em>Your current role: <strong>${currentUser?.role || 'analyst'}</strong></em><br>
        <em>Only admin users can perform write operations (create, update, trigger, delete).</em>
    `;
    
    contentDiv.appendChild(avatarDiv);
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Chat Functions
async function sendChatMessage(message) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/query`, {
            method: 'POST',
            body: JSON.stringify({
                query: message,
                session_id: currentSessionId,
                user_id: currentUser?.id?.toString() || 'default_user'
            })
        });
        
        if (response) {
            const data = await response.json();
            return data.response;
        }
    } catch (error) {
        // 🆕 UPDATED: Don't show popup notification for permission errors
        if (!error.message.includes('Permission denied')) {
            showNotification('Failed to send message: ' + error.message, 'error');
        }
        throw error;
    }
}

function addChatMessage(content, isUser = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'system'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = content.replace(/\n/g, '<br>');
    
    contentDiv.appendChild(avatarDiv);
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Update message count
    if (isUser) {
        messageCount++;
        document.getElementById('message-count').textContent = messageCount;
    }
    
    return messageDiv;
}

function updateSessionInfo() {
    document.getElementById('session-id').textContent = currentSessionId;
    document.getElementById('session-time').textContent = new Date().toLocaleTimeString();
}

async function loadAgentStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const health = await response.json();
        
        const statusContainer = document.getElementById('agent-status-list');
        statusContainer.innerHTML = `
            <div class="status-item">
                <span>Backend</span>
                <span class="status ${health.backend === 'healthy' ? 'healthy' : 'unhealthy'}">${health.backend}</span>
            </div>
            <div class="status-item">
                <span>Host Agent</span>
                <span class="status ${health.host_agent === 'healthy' ? 'healthy' : 'unhealthy'}">${health.host_agent}</span>
            </div>
            <div class="status-item">
                <span>Marketo Agent</span>
                <span class="status ${health.agents.marketo_agent === 'healthy' ? 'healthy' : health.agents.marketo_agent === 'down' ? 'down' : 'unhealthy'}">${health.agents.marketo_agent}</span>
            </div>
            <div class="status-item">
                <span>Web Search Agent</span>
                <span class="status ${health.agents.websearch_agent === 'healthy' ? 'healthy' : health.agents.websearch_agent === 'down' ? 'down' : 'unhealthy'}">${health.agents.websearch_agent}</span>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load agent status:', error);
    }
}

async function getUserInfo() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/auth/me`);
        if (response) {
            currentUser = await response.json();
            document.getElementById('user-name').textContent = currentUser.full_name || currentUser.username;
            
            // 🆕 Display user role
            const userRoleElement = document.getElementById('user-role');
            if (userRoleElement) {
                const roleDisplay = currentUser.role === 'admin' ? 'Admin' : 'Analyst';
                const roleClass = currentUser.role === 'admin' ? 'role-admin' : 'role-analyst';
                userRoleElement.innerHTML = `<span class="user-role-badge ${roleClass}">${roleDisplay}</span>`;
            }
        }
    } catch (error) {
        console.error('Failed to get user info:', error);
    }
}

function checkAuthStatus() {
    const accessToken = sessionStorage.getItem('accessToken');
    if (!accessToken) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function clearChat() {
    const messagesContainer = document.getElementById('chat-messages');
    // Keep only the welcome message
    const welcomeMessage = messagesContainer.querySelector('.welcome');
    messagesContainer.innerHTML = '';
    if (welcomeMessage) {
        messagesContainer.appendChild(welcomeMessage);
    }
    messageCount = 0;
    document.getElementById('message-count').textContent = messageCount;
    currentSessionId = generateSessionId();
    updateSessionInfo();
    showNotification('Chat cleared', 'success');
}

function exportChat() {
    const messages = document.querySelectorAll('.message-text');
    let chatText = `Marketo A2A Chat Export\nSession: ${currentSessionId}\nDate: ${new Date().toLocaleString()}\n\n`;
    
    messages.forEach(message => {
        const isUser = message.closest('.message').classList.contains('user');
        const sender = isUser ? 'User' : 'Agent';
        chatText += `${sender}: ${message.textContent}\n\n`;
    });
    
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `marketo-chat-${currentSessionId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Chat exported successfully', 'success');
}

function logout() {
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
    window.location.href = 'login.html';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    if (!checkAuthStatus()) return;
    
    // Initialize
    getUserInfo();
    updateSessionInfo();
    loadAgentStatus();
    
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Chat form
    document.getElementById('chat-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message
        addChatMessage(message, true);
        input.value = '';
        
        // Show loading message
        const loadingMessage = addChatMessage('<div class="loading"></div> Thinking...', false);
        
        try {
            const response = await sendChatMessage(message);
            // Remove loading message
            loadingMessage.remove();
            // Add actual response
            addChatMessage(response, false);
        } catch (error) {
            // Remove loading message
            loadingMessage.remove();
            
            // 🆕 UPDATED: Permission errors are already shown in chat by showPermissionDeniedMessage
            // Don't add any additional error message for permission errors
            if (!error.message.includes('Permission denied')) {
                addChatMessage('❌ Sorry, I encountered an error. Please try again.', false);
            }
            // If it's a permission error, the message is already in the chat
        }
    });
    
    // Suggestion buttons
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const query = this.dataset.query;
            document.getElementById('chat-input').value = query;
            document.getElementById('chat-input').focus();
        });
    });
    
    // Clear chat button
    document.getElementById('clear-chat').addEventListener('click', clearChat);
    
    // Export chat button
    document.getElementById('export-chat').addEventListener('click', exportChat);
    
    // Enter key to send message
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
        }
    });
});

console.log('Chat page initialized');