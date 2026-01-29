"""
Clear translation cache and force IndicTrans2 reload
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("FORCING INDICTRANS2 RELOAD")
print("=" * 70)

# Login
print("\n1. Logging in...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)

if response.status_code != 200:
    print(f"✗ Login failed")
    exit(1)

token = response.json()["access_token"]
print("✓ Logged in")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Clear cache
print("\n2. Clearing translation model cache...")
clear_response = requests.post(
    f"{BASE_URL}/api/v1/clear-translation-cache",
    headers=headers
)

if clear_response.status_code == 200:
    result = clear_response.json()
    print(f"✓ Cache cleared")
    print(f"   Previous model: {result.get('previous_model')}")
else:
    print(f"⚠ Clear cache failed: {clear_response.status_code}")

print("\n3. Waiting 2 seconds for reload to take effect...")
time.sleep(2)

# Test translation
print("\n4. Testing Malayalam translation (this will load IndicTrans2)...")
print("   Note: First load may take 2-5 minutes to download model...")

test_text = "The student showed significant improvement in communication skills."

translation_response = requests.post(
    f"{BASE_URL}/api/v1/translate",
    headers=headers,
    json={
        "text": test_text,
        "target_language": "mal_Mlym",
        "source_language": "eng_Latn"
    }
)

if translation_response.status_code == 200:
    result = translation_response.json()
    translated = result['translated_text']
    
    print(f"\n✓ Translation completed!")
    print(f"\n   Original:  {test_text}")
    print(f"   Translated: {translated}")
    
    # Check for Malayalam characters
    has_malayalam = any('\u0d00' <= c <= '\u0d7f' for c in translated)
    
    print("\n" + "=" * 70)
    if has_malayalam:
        malayalam_count = sum(1 for c in translated if '\u0d00' <= c <= '\u0d7f')
        print(f"✓✓✓ SUCCESS! IndicTrans2 is working!")
        print(f"    Found {malayalam_count} Malayalam characters")
        print(f"    Translation is now using the proper model!")
    else:
        print(f"✗ STILL NOT WORKING - No Malayalam characters detected")
        print(f"    Output: {translated[:80]}...")
        print(f"\n    The backend server needs a FULL RESTART:")
        print(f"    1. Go to uvicorn terminal")
        print(f"    2. Press Ctrl+C to stop it")
        print(f"    3. Run: uvicorn app.main:app --reload")
        print(f"    4. Wait for startup, then run this script again")
else:
    print(f"\n✗ Translation failed: {translation_response.status_code}")
    error = translation_response.json()
    print(f"   Error: {error.get('detail')}")
    
    if "gated repo" in str(error.get('detail', '')):
        print(f"\n   IndicTrans2 is gated - you need HuggingFace authentication")
        print(f"   Run: python setup_huggingface.py")

print("\n" + "=" * 70)
