// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
const FRONTEND_PORT = 8080;

// State Management
let currentUser = null;
let accessToken = null;
let refreshToken = null;
let currentSessionId = generateSessionId();

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

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.add('hidden');
    });
    document.getElementById(screenId).classList.remove('hidden');
}

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');
}

// Authentication Functions
async function register(userData) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        
        const user = await response.json();
        showNotification('Registration successful! Please login.', 'success');
        showScreen('login-screen');
        return user;
    } catch (error) {
        showNotification(error.message, 'error');
        throw error;
    }
}

async function login(username, password) {
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        const tokens = await response.json();
        accessToken = tokens.access_token;
        refreshToken = tokens.refresh_token;
        
        // Get user info
        await getUserInfo();
        
        showNotification('Login successful!', 'success');
        showScreen('dashboard');
        return tokens;
    } catch (error) {
        showNotification(error.message, 'error');
        throw error;
    }
}

async function getUserInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('user-name').textContent = `Welcome, ${currentUser.full_name || currentUser.username}`;
        }
    } catch (error) {
        console.error('Failed to get user info:', error);
    }
}

async function refreshAccessToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        if (response.ok) {
            const tokens = await response.json();
            accessToken = tokens.access_token;
            refreshToken = tokens.refresh_token;
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }
    return false;
}

async function apiRequest(url, options = {}) {
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
            // Try to refresh token
            if (await refreshAccessToken()) {
                finalOptions.headers['Authorization'] = `Bearer ${accessToken}`;
                return await fetch(url, finalOptions);
            } else {
                // Refresh failed, redirect to login
                logout();
                throw new Error('Session expired. Please login again.');
            }
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
        
        return response;
    } catch (error) {
        if (error.message.includes('Session expired')) {
            showNotification(error.message, 'error');
        }
        throw error;
    }
}

function logout() {
    currentUser = null;
    accessToken = null;
    refreshToken = null;
    currentSessionId = generateSessionId();
    showScreen('login-screen');
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
        
        const data = await response.json();
        return data.response;
    } catch (error) {
        showNotification('Failed to send message: ' + error.message, 'error');
        throw error;
    }
}

function addChatMessage(content, isUser = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'system'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (!isUser) {
        contentDiv.innerHTML = `<i class="fas fa-robot"></i>`;
    }
    
    const textNode = document.createElement('div');
    textNode.innerHTML = content.replace(/\n/g, '<br>');
    contentDiv.appendChild(textNode);
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Reports Functions
async function loadReportTemplates() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/reports/templates`);
        const data = await response.json();
        
        const templatesList = document.getElementById('report-templates-list');
        const templateSelect = document.getElementById('report-template');
        
        templatesList.innerHTML = '';
        templateSelect.innerHTML = '<option value="">Select a template...</option>';
        
        data.templates.forEach(template => {
            // Add to grid
            const templateCard = document.createElement('div');
            templateCard.className = 'template-card';
            templateCard.innerHTML = `
                <h4>${template.name}</h4>
                <p>${template.description}</p>
                <div class="example">${template.example_query}</div>
            `;
            templateCard.onclick = () => {
                document.getElementById('report-template').value = template.id;
                if (template.id === 'campaign_performance') {
                    document.getElementById('campaign-id').focus();
                } else if (template.id === 'lead_distribution') {
                    document.getElementById('smart-list-id').focus();
                }
            };
            templatesList.appendChild(templateCard);
            
            // Add to select
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        });
    } catch (error) {
        showNotification('Failed to load report templates: ' + error.message, 'error');
    }
}

async function generateReport(templateId, parameters) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/reports/generate`, {
            method: 'POST',
            body: JSON.stringify({
                template_id: templateId,
                parameters: parameters,
                session_id: currentSessionId,
                user_id: currentUser?.id?.toString() || 'default_user'
            })
        });
        
        const data = await response.json();
        return data.response;
    } catch (error) {
        showNotification('Failed to generate report: ' + error.message, 'error');
        throw error;
    }
}

// History Functions
async function loadHistory(sessionId) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/history/${sessionId}`);
        const data = await response.json();
        
        const resultsContainer = document.getElementById('history-results');
        
        if (data.messages && data.messages.length > 0) {
            resultsContainer.innerHTML = '<h3>Conversation History</h3>';
            
            data.messages.forEach(message => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'history-message';
                messageDiv.innerHTML = `
                    <div class="history-message-header">
                        <strong>${message.role === 'user' ? 'You' : 'Agent'}</strong>
                        <span class="timestamp">${new Date(message.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="history-message-content">${message.content}</div>
                `;
                resultsContainer.appendChild(messageDiv);
            });
        } else {
            resultsContainer.innerHTML = '<p class="no-history">No messages found for this session ID.</p>';
        }
    } catch (error) {
        showNotification('Failed to load history: ' + error.message, 'error');
    }
}

// Health Functions
async function loadHealthStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        const healthContainer = document.getElementById('health-status');
        healthContainer.innerHTML = `
            <h3>System Status</h3>
            <div class="health-item">
                <span>Backend</span>
                <span class="status ${data.backend === 'healthy' ? 'healthy' : 'unhealthy'}">${data.backend}</span>
            </div>
            <div class="health-item">
                <span>Host Agent</span>
                <span class="status ${data.host_agent === 'healthy' ? 'healthy' : 'unhealthy'}">${data.host_agent}</span>
            </div>
            <div class="health-item">
                <span>Marketo Agent</span>
                <span class="status ${data.agents.marketo_agent === 'healthy' ? 'healthy' : data.agents.marketo_agent === 'down' ? 'down' : 'unhealthy'}">${data.agents.marketo_agent}</span>
            </div>
            <div class="health-item">
                <span>Web Search Agent</span>
                <span class="status ${data.agents.websearch_agent === 'healthy' ? 'healthy' : data.agents.websearch_agent === 'down' ? 'down' : 'unhealthy'}">${data.agents.websearch_agent}</span>
            </div>
        `;
    } catch (error) {
        showNotification('Failed to load health status: ' + error.message, 'error');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Show loading screen initially
    showScreen('loading-screen');
    
    // Simulate loading time
    setTimeout(() => {
        showScreen('login-screen');
    }, 2000);
    
    // Login form
    document.getElementById('login-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            await login(username, password);
        } catch (error) {
            // Error already handled in login function
        }
    });
    
    // Register form
    document.getElementById('register-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = {
            username: document.getElementById('reg-username').value,
            email: document.getElementById('reg-email').value,
            full_name: document.getElementById('reg-fullname').value,
            password: document.getElementById('reg-password').value
        };
        
        try {
            await register(formData);
        } catch (error) {
            // Error already handled in register function
        }
    });
    
    // Show register screen
    document.getElementById('show-register').addEventListener('click', function(e) {
        e.preventDefault();
        showScreen('register-screen');
    });
    
    // Show login screen
    document.getElementById('show-login').addEventListener('click', function(e) {
        e.preventDefault();
        showScreen('login-screen');
    });
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            showSection(section + '-section');
            
            // Load section-specific data
            if (section === 'reports') {
                loadReportTemplates();
            } else if (section === 'health') {
                loadHealthStatus();
            }
        });
    });
    
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
        const loadingMessage = addChatMessage('Thinking...', false);
        
        try {
            const response = await sendChatMessage(message);
            // Remove loading message
            document.querySelector('.message:last-child').remove();
            // Add actual response
            addChatMessage(response, false);
        } catch (error) {
            // Remove loading message
            document.querySelector('.message:last-child').remove();
            addChatMessage('Sorry, I encountered an error. Please try again.', false);
        }
    });
    
    // Report form
    document.getElementById('report-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const templateId = document.getElementById('report-template').value;
        const campaignId = document.getElementById('campaign-id').value;
        const smartListId = document.getElementById('smart-list-id').value;
        
        const parameters = {};
        if (campaignId) parameters.campaign_id = campaignId;
        if (smartListId) parameters.smart_list_id = smartListId;
        
        try {
            showNotification('Generating report...', 'info');
            const response = await generateReport(templateId, parameters);
            
            // Show report in chat
            showSection('chat-section');
            addChatMessage(`<strong>Generated Report:</strong><br><br>${response}`, false);
        } catch (error) {
            // Error already handled in generateReport function
        }
    });
    
    // History search
    document.getElementById('search-history').addEventListener('click', function() {
        const sessionId = document.getElementById('session-search').value.trim();
        if (sessionId) {
            loadHistory(sessionId);
        } else {
            showNotification('Please enter a session ID', 'error');
        }
    });
    
    // Refresh health
    document.getElementById('refresh-health').addEventListener('click', loadHealthStatus);
});

// Initialize app
console.log('Marketo A2A Frontend initialized');