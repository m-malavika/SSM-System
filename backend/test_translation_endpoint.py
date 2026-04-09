"""
Quick diagnostic to test translation endpoint
Run this to verify the endpoint is working
"""
import requests

BASE_URL = "http://localhost:8000"

# Test 1: Check if endpoint exists
print("=" * 50)
print("TEST 1: Checking if backend is running...")
print("=" * 50)
try:
    response = requests.get(f"{BASE_URL}/docs")
    if response.status_code == 200:
        print("✓ Backend is running!")
        print(f"  API docs available at: {BASE_URL}/docs")
    else:
        print(f"✗ Backend returned status: {response.status_code}")
except Exception as e:
    print(f"✗ Backend is NOT running: {e}")
    print("\nTo start backend:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")
    exit(1)

# Test 2: Try to access translate endpoint without auth
print("\n" + "=" * 50)
print("TEST 2: Checking translation endpoint (no auth)...")
print("=" * 50)
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/translate",
        json={"text": "Hello", "target_language": "mal_Mlym"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 401:
        print("✓ Endpoint exists but requires authentication (expected)")
    elif response.status_code == 403:
        print("⚠ Got 403 - endpoint exists but credentials invalid")
    elif response.status_code == 404:
        print("✗ Endpoint NOT found - backend needs restart!")
        print("\nRestart backend:")
        print("  1. Stop the backend (Ctrl+C in backend terminal)")
        print("  2. cd backend")
        print("  3. uvicorn app.main:app --reload")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Login and test with auth
print("\n" + "=" * 50)
print("TEST 3: Testing with authentication...")
print("=" * 50)

# Try to login
print("Attempting login with admin/admin123...")
try:
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        print("✓ Login successful!")
        
        # Now try translation
        print("\nTrying translation to Malayalam with auth token...")
        translation_response = requests.post(
            f"{BASE_URL}/api/v1/translate",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "text": "The student showed significant improvement in communication skills.",
                "target_language": "mal_Mlym"
            }
        )
        
        print(f"Status: {translation_response.status_code}")
        if translation_response.status_code == 200:
            print("✓ TRANSLATION WORKS!")
            result = translation_response.json()
            print(f"\nOriginal: The student showed significant improvement in communication skills.")
            print(f"Translated (Malayalam): {result['translated_text']}")
            print(f"Target Language: {result['target_language']}")
        else:
            print(f"✗ Translation failed: {translation_response.json()}")
    else:
        print(f"✗ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.json()}")
        print("\nNote: Update credentials in this script if needed")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 50)
print("DIAGNOSTIC COMPLETE")
print("=" * 50)
print("\nIf you're still getting 403 errors:")
print("1. Make sure you're logged in to the web app")
print("2. Check browser console for token issues")
print("3. Try logging out and back in")
print("4. Restart the backend server")
