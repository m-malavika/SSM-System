"""Direct API test - minimal version"""
import requests
import json

# Login first
print("Logging in...")
login_data = {"username": "admin", "password": "admin123"}
# Use form data for login endpoint
login_response = requests.post(
    "http://127.0.0.1:8000/api/v1/auth/login",
    data=login_data  # Use data instead of json for form submission
)
login_response.raise_for_status()
token = login_response.json()["access_token"]
print("✓ Logged in")

# Test with just 3 sentences
test_text = "The student showed improvement. Communication skills developed well. Social skills are better."

print(f"\nTranslating: {test_text}")

# Make translation request
headers = {"Authorization": f"Bearer {token}"}
translation_data = {
    "text": test_text,
    "target_language": "mal_Mlym",
    "source_language": "eng_Latn"
}

response = requests.post(
    "http://127.0.0.1:8000/api/v1/translate",
    json=translation_data,
    headers=headers
)

print(f"\nStatus: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Original: {test_text}")
    print(f"Translated: {result['translated_text']}")
    print(f"\nOriginal length: {len(test_text)}")
    print(f"Translated length: {len(result['translated_text'])}")
else:
    print(f"Error: {response.text}")
