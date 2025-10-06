# OAuth2 Authentication Setup Guide

This guide explains how to use the OAuth2 authentication system implemented in the Marketo A2A Backend.

## Overview

The authentication system uses:
- **JWT (JSON Web Tokens)** for secure token-based authentication
- **OAuth2 Password Flow** for login
- **Bcrypt** for password hashing
- **Access tokens** (30 minutes expiry) and **Refresh tokens** (7 days expiry)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `a2amarketo/backend/` directory:

```bash
cp .env.example .env
```

**IMPORTANT:** Generate a secure secret key for production:

```bash
# Generate a secure random secret key
openssl rand -hex 32
```

Update your `.env` file with the generated key:

```env
SECRET_KEY=your-generated-secret-key-here
```

### 3. Run the Application

```bash
python app.py
```

The database will automatically create the `users` table on startup.

## API Endpoints

### Authentication Endpoints

#### 1. Register a New User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"  // Optional
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2025-10-06T12:00:00"
}
```

#### 2. Login (Get Tokens)
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=SecurePassword123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Refresh Access Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token-here"
}
```

**Response:**
```json
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer"
}
```

#### 4. Get Current User Info
```http
GET /api/auth/me
Authorization: Bearer your-access-token
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2025-10-06T12:00:00"
}
```

### Protected Endpoints

All the following endpoints now require authentication:

- `POST /api/query` - Send queries to the agent
- `GET /api/reports/templates` - Get report templates
- `POST /api/reports/generate` - Generate reports
- `GET /api/history/{session_id}` - Get conversation history

**Authentication Header:**
```http
Authorization: Bearer your-access-token
```

## Usage Examples

### Using cURL

#### Register:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123",
    "full_name": "John Doe"
  }'
```

#### Login:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=SecurePassword123"
```

#### Access Protected Endpoint:
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-access-token" \
  -d '{
    "query": "What campaigns are running?",
    "session_id": "session-123"
  }'
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:5000"

# Register
response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePassword123",
        "full_name": "John Doe"
    }
)
print(response.json())

# Login
response = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={
        "username": "john_doe",
        "password": "SecurePassword123"
    }
)
tokens = response.json()
access_token = tokens["access_token"]

# Access protected endpoint
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(
    f"{BASE_URL}/api/query",
    json={
        "query": "What campaigns are running?",
        "session_id": "session-123"
    },
    headers=headers
)
print(response.json())
```

### Using JavaScript (Frontend)

```javascript
const BASE_URL = 'http://localhost:5000';

// Login
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData
  });
  
  const tokens = await response.json();
  // Store tokens (localStorage, sessionStorage, or secure cookie)
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
  return tokens;
}

// Access protected endpoint
async function queryAgent(query, sessionId) {
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch(`${BASE_URL}/api/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      query: query,
      session_id: sessionId
    })
  });
  
  if (response.status === 401) {
    // Token expired, refresh it
    await refreshToken();
    // Retry the request
    return queryAgent(query, sessionId);
  }
  
  return response.json();
}

// Refresh token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch(`${BASE_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh_token: refreshToken
    })
  });
  
  const tokens = await response.json();
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
}
```

## Security Best Practices

1. **Never commit `.env` file to version control**
2. **Use strong, random secret keys in production** (32+ characters)
3. **Use HTTPS in production** to encrypt tokens in transit
4. **Store tokens securely** on the client side (HTTPOnly cookies preferred)
5. **Implement token rotation** for sensitive operations
6. **Set appropriate CORS origins** in production
7. **Consider adding rate limiting** for login endpoints
8. **Implement password strength requirements** in your frontend

## Token Lifetimes

- **Access Token:** 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token:** 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)

You can adjust these in your `.env` file or `config.py`.

## Testing with Swagger UI

FastAPI automatically generates interactive API documentation:

1. Start your server
2. Visit: http://localhost:5000/docs
3. Click "Authorize" button at the top right
4. Login to get your access token
5. Paste the token and click "Authorize"
6. Now you can test all protected endpoints

## Troubleshooting

### "Could not validate credentials"
- Your token may have expired. Use the refresh token endpoint to get a new access token.
- Check that you're sending the token in the correct format: `Bearer <token>`

### "Username already registered"
- The username must be unique. Choose a different username.

### "Incorrect username or password"
- Double-check your credentials. Passwords are case-sensitive.

### CORS errors in browser
- Add your frontend URL to `ALLOWED_ORIGINS` in config.py or .env file

## Advanced Configuration

### Custom Token Expiry

Edit `a2amarketo/backend/config.py`:

```python
class Settings(BaseSettings):
    # ...
    access_token_expire_minutes: int = 60  # 1 hour
    refresh_token_expire_days: int = 30    # 30 days
```

### Database Changes

The User table is automatically created when the app starts. If you need to modify it, update the `User` class in `database.py` and delete the existing database file to recreate it.

## Support

For issues or questions, please refer to the main project documentation or contact the development team.

