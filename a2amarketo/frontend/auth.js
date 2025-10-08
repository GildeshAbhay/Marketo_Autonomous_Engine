
// API Configuration
// const API_BASE_URL = 'http://localhost:5000/api';
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000'
    : 'YOUR_BACKEND_CLOUD_RUN_URL';  // Will be set after deployment

// State Management
let accessToken = null;
let refreshToken = null;
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

function showScreen(screenId) {
    document.querySelectorAll('.auth-screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
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
        
        // Store tokens in sessionStorage for persistence across pages
        sessionStorage.setItem('accessToken', accessToken);
        sessionStorage.setItem('refreshToken', refreshToken);
        
        showNotification('Login successful! Redirecting...', 'success');
        
        // Redirect to dashboard after successful login
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1500);
        
        return tokens;
    } catch (error) {
        showNotification(error.message, 'error');
        throw error;
    }
}

// Check if user is already logged in
function checkAuthStatus() {
    const storedAccessToken = sessionStorage.getItem('accessToken');
    const storedRefreshToken = sessionStorage.getItem('refreshToken');
    
    if (storedAccessToken && storedRefreshToken) {
        // User is already logged in, redirect to dashboard
        window.location.href = 'dashboard.html';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already authenticated
    checkAuthStatus();
    
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
});

console.log('Auth page initialized');
