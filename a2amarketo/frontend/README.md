# Marketo A2A Frontend

A beautiful, modern web interface for the Marketo Autonomous Agent (A2A) framework.

## Features

- 🔐 **Authentication**: Secure login and registration with JWT tokens
- 💬 **Agent Chat**: Interactive chat interface with your Marketo agents
- 📊 **Reports**: Generate and view marketing reports using templates
- 📜 **History**: View conversation history by session ID
- 💓 **Health Monitoring**: Real-time system health status
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Prerequisites

1. Make sure your backend is running on `http://localhost:5000`
2. Ensure all agents (Marketo Agent, Web Search Agent) are running
3. Python 3.7+ installed

### Running the Frontend

#### Option 1: Using Python's built-in server
```bash
cd frontend
python server.py
```

#### Option 2: Using any other web server
```bash
# Using Node.js http-server (if installed)
npx http-server -p 8080

# Using Python's simple server
python -m http.server 8080

# Using PHP (if installed)
php -S localhost:8080
```

The frontend will be available at: http://localhost:8080

## Usage

1. **Register/Login**: Create an account or login with existing credentials
2. **Agent Chat**: Ask questions about your Marketo campaigns, leads, or marketing automation
3. **Generate Reports**: Use the Reports section to create structured marketing reports
4. **View History**: Search for past conversations using session IDs
5. **Monitor Health**: Check the status of all agents and the backend system

## API Integration

The frontend integrates with the following backend endpoints:

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/me` - Get user info
- `POST /api/query` - Send chat messages
- `GET /api/reports/templates` - Get report templates
- `POST /api/reports/generate` - Generate reports
- `GET /api/history/{session_id}` - Get conversation history
- `GET /api/health` - System health check

## Design Features

- **Modern UI**: Clean, professional interface with gradients and glassmorphism effects
- **Responsive**: Adapts to different screen sizes
- **Real-time Updates**: Live chat and status updates
- **Error Handling**: User-friendly error messages and notifications
- **Token Management**: Automatic token refresh and session management

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── styles.css          # CSS styles with modern design
├── app.js             # JavaScript application logic
├── server.py          # Simple HTTP server script
└── README.md          # This file
```

## Customization

### Styling
Edit `styles.css` to customize colors, fonts, and layout:
- Primary colors: `#667eea` and `#764ba2`
- Background: Gradient from blue to purple
- Cards: Glassmorphism effect with backdrop blur

### API Endpoints
Update the `API_BASE_URL` in `app.js` if your backend runs on a different port or host.

### Features
The frontend is modular and easy to extend. You can add new sections by:
1. Adding HTML structure in `index.html`
2. Adding CSS styles in `styles.css`
3. Adding JavaScript functionality in `app.js`

## Troubleshooting

**CORS Errors**: Make sure the frontend URL is added to `allowed_origins` in the backend config.

**Authentication Issues**: Check that the backend is running and accessible.

**Agent Connection Issues**: Verify all agents are running and check the Health section.

**Port Conflicts**: Change the PORT variable in `server.py` if port 8080 is already in use.

## Security Notes

- Tokens are stored in memory (not localStorage) for better security
- Automatic token refresh prevents session expiration
- CORS is properly configured for secure cross-origin requests
- All API calls include proper error handling

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

Modern browsers with ES6+ support required.