"""
Force reload translation models and test with IndicTrans2
"""
import requests

BASE_URL = "http://localhost:8000"

# Login
print("Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
print("✓ Logged in")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Force reload models
print("\nForcing model reload...")
reload_response = requests.post(
    f"{BASE_URL}/api/v1/reload-models",
    headers=headers
)
print(f"Reload: {reload_response.json()}")

# Test Malayalam translation
print("\n" + "="*60)
print("TESTING MALAYALAM TRANSLATION")
print("="*60)

test_text = "The student showed significant improvement in communication skills during therapy sessions."
print(f"\nOriginal (English):\n{test_text}")

translation_response = requests.post(
    f"{BASE_URL}/api/v1/translate",
    headers=headers,
    json={
        "text": test_text,
        "target_language": "mal_Mlym",
        "source_language": "eng_Latn"
    }
)

print(f"\nStatus: {translation_response.status_code}")

if translation_response.status_code == 200:
    result = translation_response.json()
    print(f"\n✓ TRANSLATION SUCCESSFUL!")
    print(f"\nTranslated (Malayalam):\n{result['translated_text']}")
    print(f"\nLanguage: {result['source_language']} -> {result['target_language']}")
    
    # Check if it's actually Malayalam (should contain Malayalam characters)
    translated = result['translated_text']
    has_malayalam = any('\u0d00' <= c <= '\u0d7f' for c in translated)
    
    if has_malayalam:
        print("\n✓✓✓ CONTAINS MALAYALAM CHARACTERS - IndicTrans2 is working!")
    else:
        print("\n⚠ WARNING: Translation doesn't contain Malayalam characters")
        print("This might mean IndicTrans2 isn't loaded properly")
else:
    print(f"\n✗ Translation failed")
    print(f"Error: {translation_response.json()}")

# Test Hindi too
print("\n" + "="*60)
print("TESTING HINDI TRANSLATION")
print("="*60)

translation_response = requests.post(
    f"{BASE_URL}/api/v1/translate",
    headers=headers,
    json={
        "text": "The student is making good progress.",
        "target_language": "hin_Deva",
        "source_language": "eng_Latn"
    }
)

if translation_response.status_code == 200:
    result = translation_response.json()
    print(f"Hindi: {result['translated_text']}")
    has_hindi = any('\u0900' <= c <= '\u097f' for c in result['translated_text'])
    if has_hindi:
        print("✓ Contains Devanagari (Hindi) characters")
else:
    print(f"Failed: {translation_response.json()}")
