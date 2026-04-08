"""
Test the AI summarization endpoint without authentication
"""

import requests
import json

# Test endpoint (no auth required)
url = "https://ssm-system-bveh.onrender.com/api/v1/therapy-reports/summary/ai/test"

# Payload - change student_id to match a student in your database
payload = {
    "student_id": "STU2025001",  # Change this to your student ID
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "from_date": None,
    "to_date": None,
    "therapy_type": None
}

print("🧪 Testing AI Summarization Endpoint")
print("=" * 70)
print(f"URL: {url}")
print(f"Student ID: {payload['student_id']}")
print(f"Model: {payload['model']}")
print("=" * 70)

try:
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS!")
        print("=" * 70)
        
        print(f"\n📊 Used Reports: {data.get('used_reports', 0)}")
        print(f"🤖 Model: {data.get('model', 'N/A')}")
        
        print("\n📝 BRIEF OVERVIEW:")
        print("-" * 70)
        print(data.get('brief_overview', 'N/A'))
        
        print("\n📋 START DATE ANALYSIS:")
        print("-" * 70)
        print(data.get('start_date_analysis', 'N/A'))
        
        print("\n📊 CURRENT STATUS:")
        print("-" * 70)
        print(data.get('end_date_analysis', 'N/A'))
        
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 70)
        print(data.get('recommendations', 'N/A'))
        
        print("\n📖 MAIN SUMMARY:")
        print("-" * 70)
        print(data.get('summary', 'N/A'))
        
        print("\n" + "=" * 70)
        print("✅ Test completed successfully!")
        
    else:
        print(f"\n❌ ERROR {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ Cannot connect to backend!")
    print("Make sure the backend is running:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
print("💡 TIP: Change 'student_id' in this script to test different students")
print("=" * 70)
