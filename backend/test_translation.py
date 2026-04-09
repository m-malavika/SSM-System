"""
Test translation endpoint with IndicTrans2
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
TRANSLATE_URL = f"{BASE_URL}/api/v1/translate"

# Test credentials (update with your admin credentials)
USERNAME = "admin"
PASSWORD = "admin123"

def test_translation():
    # Login first to get token
    print("Logging in...")
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(LOGIN_URL, data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return
    
    token = response.json()["access_token"]
    print(f"Login successful! Token: {token[:20]}...")
    
    # Test translation
    print("\nTesting translation to Malayalam...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    translation_data = {
        "text": "The student showed significant improvement in communication skills during therapy sessions.",
        "target_language": "mal_Mlym",
        "source_language": "eng_Latn"
    }
    
    response = requests.post(TRANSLATE_URL, headers=headers, json=translation_data)
    
    if response.status_code == 200:
        result = response.json()
        print("Translation successful!")
        print(f"Original: {translation_data['text']}")
        print(f"Translated: {result['translated_text']}")
        print(f"Target Language: {result['target_language']}")
    else:
        print(f"Translation failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_translation()
