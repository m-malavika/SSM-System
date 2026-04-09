"""
Test translation of full AI summary (multiple sentences)
"""
import requests

BASE_URL = "http://localhost:8000"

# Login
print("Logging in...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)

token = response.json()["access_token"]
print("✓ Logged in\n")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Longer AI summary (typical therapy report summary)
long_summary = """The student has demonstrated consistent progress across multiple therapy sessions during this evaluation period. 

Communication skills have shown significant improvement, with the student now able to express basic needs more clearly and respond appropriately to simple verbal cues. The student's receptive language abilities have developed notably, showing better comprehension of instructions and environmental sounds.

Social interaction skills continue to develop steadily. The student is beginning to show more interest in peer activities and demonstrates improved eye contact during structured sessions. Turn-taking behaviors have improved, particularly during preferred activities.

Fine motor skills show gradual progress. The student can now hold writing instruments with better grip control and complete simple drawing tasks with minimal assistance. Self-care activities like buttoning and zipping have also shown improvement.

Continued focus on maintaining and expanding communication abilities is recommended. Incorporating more peer interaction opportunities and practicing self-care routines in natural settings will support further development. The family is encouraged to continue reinforcement strategies at home for optimal progress."""

print("="*70)
print("TESTING FULL AI SUMMARY TRANSLATION")
print("="*70)
print(f"\nOriginal Summary Length: {len(long_summary)} characters")
print(f"Word count: {len(long_summary.split())} words")
print("\nFirst 150 characters:")
print(f"{long_summary[:150]}...")

print("\n" + "="*70)
print("TRANSLATING TO MALAYALAM...")
print("="*70)

translation_response = requests.post(
    f"{BASE_URL}/api/v1/translate",
    headers=headers,
    json={
        "text": long_summary,
        "target_language": "mal_Mlym",
        "source_language": "eng_Latn"
    }
)

if translation_response.status_code == 200:
    result = translation_response.json()
    translated = result['translated_text']
    
    print(f"\n✓ Translation successful!")
    print(f"\nTranslated Length: {len(translated)} characters")
    print(f"Length ratio: {len(translated)/len(long_summary):.2f}")
    
    # Check for Malayalam characters
    malayalam_count = sum(1 for c in translated if '\u0d00' <= c <= '\u0d7f')
    print(f"Malayalam characters: {malayalam_count}")
    
    # Count sentences
    original_sentences = long_summary.count('.') + long_summary.count('?') + long_summary.count('!')
    translated_sentences = translated.count('.') + translated.count('?') + translated.count('!') + translated.count('|')
    
    print(f"\nOriginal sentences (approx): {original_sentences}")
    print(f"Translated sentences (approx): {translated_sentences}")
    
    print("\n" + "="*70)
    print("ORIGINAL (English):")
    print("="*70)
    print(long_summary)
    
    print("\n" + "="*70)
    print("TRANSLATED (Malayalam):")
    print("="*70)
    print(translated)
    
    print("\n" + "="*70)
    if malayalam_count > 100 and len(translated) > len(long_summary) * 0.7:
        print("✓✓✓ FULL TRANSLATION WORKING!")
        print("    The entire summary has been translated!")
    else:
        print("⚠ WARNING: Translation may be truncated")
        print(f"    Expected length ratio: ~1.0, got: {len(translated)/len(long_summary):.2f}")
    print("="*70)
    
else:
    print(f"\n✗ Translation failed: {translation_response.status_code}")
    print(translation_response.json())
