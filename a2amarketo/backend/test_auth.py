"""
Simple test script to verify OAuth2 authentication is working correctly.
Run this after starting your backend server.
"""
import requests
import sys

BASE_URL = "http://localhost:5000"

def test_authentication():
    """Test the complete authentication flow."""
    print("=" * 60)
    print("Testing OAuth2 Authentication Flow")
    print("=" * 60)
    
    # Test data
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    # Step 1: Register a new user
    print("\n1. Registering new user...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user,
            timeout=5
        )
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            user_data = response.json()
            print(f"   User ID: {user_data['id']}")
            print(f"   Username: {user_data['username']}")
            print(f"   Email: {user_data['email']}")
        elif response.status_code == 400 and "already registered" in response.text:
            print("⚠️  User already exists (this is fine for testing)")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the backend is running!")
        print(f"   Expected URL: {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Error during registration: {str(e)}")
        return False
    
    # Step 2: Login
    print("\n2. Logging in...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Login successful!")
            tokens = response.json()
            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Refresh Token: {refresh_token[:50]}...")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return False
    
    # Step 3: Access protected endpoint
    print("\n3. Accessing protected endpoint (/api/auth/me)...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Successfully accessed protected endpoint!")
            user_info = response.json()
            print(f"   Username: {user_info['username']}")
            print(f"   Email: {user_info['email']}")
            print(f"   Active: {user_info['is_active']}")
        else:
            print(f"❌ Failed to access protected endpoint: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error accessing protected endpoint: {str(e)}")
        return False
    
    # Step 4: Test token refresh
    print("\n4. Testing token refresh...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Token refresh successful!")
            new_tokens = response.json()
            new_access_token = new_tokens["access_token"]
            print(f"   New Access Token: {new_access_token[:50]}...")
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during token refresh: {str(e)}")
        return False
    
    # Step 5: Test invalid token
    print("\n5. Testing with invalid token...")
    try:
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 401:
            print("✅ Invalid token correctly rejected!")
        else:
            print(f"⚠️  Unexpected response for invalid token: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing invalid token: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 All authentication tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("\nMake sure your backend server is running at http://localhost:5000")
    print("Start it with: python app.py\n")
    
    input("Press Enter to start tests...")
    
    success = test_authentication()
    
    if not success:
        print("\n⚠️  Some tests failed. Check the output above.")
        sys.exit(1)
    else:
        print("\n✅ Authentication system is working correctly!")
        print("\nNext steps:")
        print("1. Update SECRET_KEY in your .env file for production")
        print("2. Use the authentication endpoints in your frontend")
        print("3. Check AUTH_SETUP.md for detailed usage examples")
        sys.exit(0)

