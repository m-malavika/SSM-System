"""
Test that translation preserves markdown formatting (headings, bullet points, structure)
"""
import requests
import os

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

def get_test_token():
    """Get authentication token"""
    try:
        response = requests.post(LOGIN_URL, data={"username": USERNAME, "password": PASSWORD})
        if response.status_code == 200:
            return response.json()["access_token"]
    except:
        pass
    return None

# Test summary with formatting (similar to therapy report)
FORMATTED_SUMMARY = """Speech Therapy – Progress Summary

**Receptive Language Skills (Comprehension)**
• The student has demonstrated significant improvement in comprehension and understanding, particularly when presented with information at a slower pace.
• However, there is still a need for continued repetition and practice to solidify these skills.
• Overall receptive language skills have shown consistent improvement across sessions.

**Expressive Language Skills**
• The student has made notable progress in expressing their current feelings and emotions.
• Despite this progress, the student still faces challenges in certain areas of expression.
• The student's ability to understand others' feelings has also improved.

**Oral Motor & Oral Placement Therapy (OPT) Goals**
• No documented data for this area

**Pragmatic Language Skills (Social Communication)**
• The student has shown improvement in social communication.
• The student's ability to understand and respond to social cues has improved.
• The therapist should aim to incorporate more opportunities for practice."""

def test_formatted_translation():
    """Test that translation preserves markdown structure"""
    
    # Get auth token
    print("Logging in...")
    token = get_test_token()
    if not token:
        print("❌ Login failed! Please check credentials or server status")
        return False
    
    print(f"✓ Login successful! Token: {token[:20]}...")
    
    base_url = BASE_URL
    
    print("\nTesting formatted translation (preserving structure)...")
    print("=" * 80)
    print("\nORIGINAL SUMMARY:")
    print("-" * 80)
    print(FORMATTED_SUMMARY)
    print("-" * 80)
    
    # Test translation
    response = requests.post(
        f"{base_url}/api/v1/translate",
        json={
            "text": FORMATTED_SUMMARY,
            "target_language": "mal_Mlym",
            "source_language": "eng_Latn"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code != 200:
        print(f"\n❌ Translation failed: {response.status_code}")
        print(response.json())
        return False
    
    data = response.json()
    translated = data["translated_text"]
    
    print("\nTRANSLATED SUMMARY:")
    print("-" * 80)
    print(translated)
    print("-" * 80)
    
    # Verify structure preservation
    original_lines = [l for l in FORMATTED_SUMMARY.split('\n') if l.strip()]
    translated_lines = [l for l in translated.split('\n') if l.strip()]
    
    print("\n📊 STRUCTURE ANALYSIS:")
    print(f"Original lines: {len(original_lines)}")
    print(f"Translated lines: {len(translated_lines)}")
    
    # Check for headings (should have similar count)
    original_headings = [l for l in original_lines if '**' in l]
    translated_headings = [l for l in translated_lines if '**' in l]
    print(f"\nOriginal headings (with **): {len(original_headings)}")
    print(f"Translated headings (with **): {len(translated_headings)}")
    
    # Check for bullet points
    original_bullets = [l for l in original_lines if l.strip().startswith('•')]
    translated_bullets = [l for l in translated_lines if l.strip().startswith('•')]
    print(f"\nOriginal bullet points (•): {len(original_bullets)}")
    print(f"Translated bullet points (•): {len(translated_bullets)}")
    
    # Verify Malayalam content
    malayalam_chars = sum(1 for c in translated if '\u0D00' <= c <= '\u0D7F')
    print(f"\nMalayalam characters: {malayalam_chars}")
    
    # Success criteria
    success = True
    issues = []
    
    if len(translated_lines) < len(original_lines) * 0.7:
        issues.append(f"Too few lines in translation ({len(translated_lines)} vs {len(original_lines)})")
        success = False
    
    if len(translated_headings) < len(original_headings):
        issues.append(f"Lost headings ({len(translated_headings)} vs {len(original_headings)})")
        success = False
    
    if len(translated_bullets) < len(original_bullets) * 0.8:
        issues.append(f"Lost bullet points ({len(translated_bullets)} vs {len(original_bullets)})")
        success = False
    
    if malayalam_chars < 50:
        issues.append(f"Not enough Malayalam characters ({malayalam_chars})")
        success = False
    
    print("\n" + "=" * 80)
    if success:
        print("✅ SUCCESS: Translation preserved formatting structure!")
        print("   - Headings preserved")
        print("   - Bullet points preserved")
        print("   - Line structure maintained")
        print("   - Content translated to Malayalam")
    else:
        print("❌ ISSUES DETECTED:")
        for issue in issues:
            print(f"   - {issue}")
    
    return success

if __name__ == "__main__":
    test_formatted_translation()
