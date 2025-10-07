// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State Management
let currentUser = null;

// Utility Functions
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
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
        
        return response;
    } catch (error) {
        showNotification('Request failed: ' + error.message, 'error');
        throw error;
    }
}

async function getUserInfo() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/auth/me`);
        if (response) {
            currentUser = await response.json();
            document.getElementById('user-name').textContent = `Welcome, ${currentUser.full_name || currentUser.username}`;
        }
    } catch (error) {
        console.error('Failed to get user info:', error);
    }
}

function logout() {
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
    window.location.href = 'login.html';
}

// Check authentication status
function checkAuthStatus() {
    const accessToken = sessionStorage.getItem('accessToken');
    if (!accessToken) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    if (!checkAuthStatus()) return;
    
    // Get user info
    getUserInfo();
    
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Option cards
    document.getElementById('chat-option').addEventListener('click', function() {
        window.location.href = 'chat.html';
    });
    
    document.getElementById('reports-option').addEventListener('click', function() {
        showNotification('Report generation is coming soon! For now, try the chat feature.', 'info');
    });
    
    document.getElementById('history-option').addEventListener('click', function() {
        showNotification('History feature is coming soon! For now, try the chat feature.', 'info');
    });
    
    document.getElementById('health-option').addEventListener('click', async function() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            const health = await response.json();
            
            let statusMessage = 'System Status:\n';
            statusMessage += `Backend: ${health.backend}\n`;
            statusMessage += `Host Agent: ${health.host_agent}\n`;
            statusMessage += `Marketo Agent: ${health.agents.marketo_agent}\n`;
            statusMessage += `Web Search Agent: ${health.agents.websearch_agent}`;
            
            showNotification(statusMessage, 'info');
        } catch (error) {
            showNotification('Failed to check system health', 'error');
        }
    });
});

console.log('Dashboard page initialized');