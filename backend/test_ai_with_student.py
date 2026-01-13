"""
Test AI summarization with a specific student ID
Usage: python test_ai_with_student.py STU2025001
"""

import sys
import requests
import json

if len(sys.argv) < 2:
    print("❌ Please provide a student ID")
    print("Usage: python test_ai_with_student.py STU2025001")
    print("\nRun 'python check_database.py' to see available students")
    sys.exit(1)

student_id = sys.argv[1]

# Test endpoint (no auth required)
url = "http://localhost:8000/api/v1/therapy-reports/summary/ai/test"

payload = {
    "student_id": student_id,
    "model": "meta-llama/Llama-3.2-3B-Instruct",
}

print("🧪 Testing AI Summarization")
print("=" * 70)
print(f"Student ID: {student_id}")
print(f"Model: {payload['model']}")
print(f"Endpoint: {url}")
print("=" * 70)

try:
    print("\n⏳ Generating AI analysis (this may take 10-30 seconds)...")
    response = requests.post(url, json=payload, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS!\n")
        print("=" * 70)
        
        print(f"📊 Reports Analyzed: {data.get('used_reports', 0)}")
        print(f"🤖 Model Used: {data.get('model', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("📝 BRIEF OVERVIEW")
        print("=" * 70)
        print(data.get('brief_overview', 'N/A'))
        
        print("\n" + "=" * 70)
        print("📋 BASELINE ANALYSIS (Start Date)")
        print("=" * 70)
        print(data.get('start_date_analysis', 'N/A'))
        
        print("\n" + "=" * 70)
        print("📊 CURRENT STATUS (End Date)")
        print("=" * 70)
        print(data.get('end_date_analysis', 'N/A'))
        
        print("\n" + "=" * 70)
        print("💡 RECOMMENDATIONS")
        print("=" * 70)
        print(data.get('recommendations', 'N/A'))
        
        print("\n" + "=" * 70)
        print("📖 COMPREHENSIVE SUMMARY")
        print("=" * 70)
        print(data.get('summary', 'N/A'))
        
        print("\n" + "=" * 70)
        print("✅ AI Analysis Complete!")
        print("=" * 70)
        
        # Check format compliance
        print("\n🔍 Format Check:")
        has_dates = any(str(data.get(key, '')).count('2024') > 0 or str(data.get(key, '')).count('Session') > 0 
                       for key in ['brief_overview', 'start_date_analysis', 'end_date_analysis', 'summary'])
        if has_dates:
            print("  ⚠️  Warning: Output may contain dates/session numbers")
        else:
            print("  ✅ Good: No dates/session numbers in narrative")
        
    elif response.status_code == 404:
        print(f"\n❌ Error: {response.json().get('detail', 'Not found')}")
        print("\nPossible issues:")
        print("  1. Student ID doesn't exist")
        print("  2. Student has no therapy reports")
        print("\nRun 'python check_database.py' to see available students")
        
    elif response.status_code == 503:
        print(f"\n❌ Service Error: {response.json().get('detail', 'Service unavailable')}")
        print("\nPossible issues:")
        print("  1. HUGGINGFACE_API_TOKEN not set in .env")
        print("  2. huggingface_hub library not installed")
        
    else:
        print(f"\n❌ ERROR {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ Cannot connect to backend!")
    print("\nMake sure the backend is running:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")
    
except requests.exceptions.Timeout:
    print("\n⏰ Request timed out!")
    print("The AI model is taking longer than expected.")
    print("This can happen with Hugging Face free tier.")
    print("Try again in a moment.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
