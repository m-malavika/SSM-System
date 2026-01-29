"""
Test that translation correctly translates AI-generated summary
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Login
print("=" * 70)
print("TESTING AI SUMMARY TRANSLATION")
print("=" * 70)

print("\n1. Logging in...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)

if response.status_code != 200:
    print(f"✗ Login failed: {response.status_code}")
    exit(1)

token = response.json()["access_token"]
print("✓ Login successful")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Sample AI summary (simulating what the AI would generate)
sample_summary = """The student has demonstrated consistent progress in therapy sessions. 
Communication skills have improved significantly over the past month. 
The student is now able to express needs more clearly and responds appropriately to verbal cues. 
Continued focus on social interaction and peer engagement is recommended."""

print(f"\n2. Testing translation of AI summary...")
print(f"   Summary length: {len(sample_summary)} characters")
print(f"   Summary preview: {sample_summary[:80]}...")

# Test Malayalam translation
print("\n3. Translating to Malayalam...")
translation_response = requests.post(
    f"{BASE_URL}/api/v1/translate",
    headers=headers,
    json={
        "text": sample_summary,
        "target_language": "mal_Mlym",
        "source_language": "eng_Latn"
    }
)

print(f"   Status: {translation_response.status_code}")

if translation_response.status_code == 200:
    result = translation_response.json()
    translated = result['translated_text']
    
    print("\n" + "=" * 70)
    print("ORIGINAL (English):")
    print("=" * 70)
    print(sample_summary)
    
    print("\n" + "=" * 70)
    print("TRANSLATED (Malayalam):")
    print("=" * 70)
    print(translated)
    
    # Check if translation actually happened
    print("\n" + "=" * 70)
    print("VALIDATION:")
    print("=" * 70)
    
    # Check for Malayalam characters (Unicode range for Malayalam: 0D00-0D7F)
    has_malayalam = any('\u0d00' <= c <= '\u0d7f' for c in translated)
    
    if has_malayalam:
        malayalam_chars = sum(1 for c in translated if '\u0d00' <= c <= '\u0d7f')
        print(f"✓✓✓ PROPER TRANSLATION DETECTED!")
        print(f"    Contains {malayalam_chars} Malayalam characters")
        print(f"    Translation is working correctly with IndicTrans2!")
    else:
        print(f"⚠ WARNING: No Malayalam characters detected")
        print(f"    Translation output: {translated[:100]}...")
        print(f"    This suggests IndicTrans2 is NOT loaded")
        print(f"\n    FIX: Restart the backend server:")
        print(f"    1. Go to uvicorn terminal")
        print(f"    2. Press Ctrl+C")
        print(f"    3. Run: uvicorn app.main:app --reload")
    
    # Check if text is actually different
    if translated != sample_summary:
        print(f"✓ Translation differs from original (expected)")
    else:
        print(f"✗ Translation is identical to original (problem!)")
    
    # Check length ratio (good translations are usually similar length)
    length_ratio = len(translated) / len(sample_summary)
    print(f"✓ Length ratio: {length_ratio:.2f} (original: {len(sample_summary)}, translated: {len(translated)})")
    
else:
    print(f"\n✗ Translation failed!")
    print(f"   Error: {translation_response.json()}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
