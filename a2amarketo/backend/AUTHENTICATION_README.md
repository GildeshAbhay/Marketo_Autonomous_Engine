# OAuth2 Authentication - Quick Start

## What Was Implemented

✅ **JWT-based OAuth2 authentication** with access and refresh tokens  
✅ **User registration and login** endpoints  
✅ **Password hashing** with bcrypt for security  
✅ **Protected API endpoints** requiring authentication  
✅ **Token refresh mechanism** for extended sessions  
✅ **Comprehensive documentation** and test scripts  

## Quick Start

### 1. Install Dependencies
```bash
pip install -r ../../requirements.txt
```

### 2. Configure (Optional)
The app works out of the box, but for production:
- Copy `.env.example` to `.env`
- Generate a secure secret key: `openssl rand -hex 32`
- Update `SECRET_KEY` in `.env`

### 3. Run the Server
```bash
python app.py
```

### 4. Test Authentication
```bash
python test_auth.py
```

### 5. Access API Documentation
Open your browser: http://localhost:5000/docs

## Authentication Flow

```
1. Register User → POST /api/auth/register
2. Login → POST /api/auth/login (returns access_token + refresh_token)
3. Access Protected Endpoints → Add header: Authorization: Bearer <access_token>
4. Refresh Token (when expired) → POST /api/auth/refresh
```

## Example Usage

### Register
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "SecurePass123"}'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -d "username=john&password=SecurePass123"
```

### Use Protected Endpoint
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What campaigns are running?", "session_id": "123"}'
```

## Protected Endpoints

All these endpoints now require authentication:
- `POST /api/query` - Send queries
- `GET /api/reports/templates` - Get templates
- `POST /api/reports/generate` - Generate reports
- `GET /api/history/{session_id}` - Get history

## Files Created/Modified

### New Files:
- `auth.py` - Authentication logic (JWT, password hashing)
- `AUTH_SETUP.md` - Complete setup guide with examples
- `AUTHENTICATION_README.md` - This quick start guide
- `test_auth.py` - Automated test script
- `.env.example` - Environment configuration template

### Modified Files:
- `app.py` - Added auth endpoints + protected existing endpoints
- `models.py` - Added User, Token, and auth-related models
- `database.py` - Added User table
- `config.py` - Added JWT configuration
- `requirements.txt` - Added auth dependencies

## Security Features

✅ **Passwords are hashed** with bcrypt (never stored in plain text)  
✅ **JWT tokens** with expiration (30 min for access, 7 days for refresh)  
✅ **Token-based authentication** (no sessions, stateless)  
✅ **CORS protection** with configurable origins  
✅ **OAuth2 standard** compatibility  

## Documentation

- **Full Guide**: See `AUTH_SETUP.md` for detailed examples
- **API Docs**: http://localhost:5000/docs (Swagger UI)
- **Test Script**: Run `python test_auth.py` to verify setup

## Next Steps

1. ✅ Authentication is ready to use!
2. **Update your frontend** to use the login endpoint
3. **Store tokens securely** (HTTPOnly cookies recommended)
4. **Change SECRET_KEY** before deploying to production
5. **Add HTTPS** in production for secure token transmission

## Troubleshooting

**Can't login?**  
- Make sure you registered first
- Check username/password are correct

**401 Unauthorized?**  
- Token may have expired - use refresh endpoint
- Check Authorization header format: `Bearer <token>`

**CORS errors?**  
- Add your frontend URL to `ALLOWED_ORIGINS` in `config.py`

## Support

For detailed examples and more information, see:
- `AUTH_SETUP.md` - Complete documentation
- FastAPI docs: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

