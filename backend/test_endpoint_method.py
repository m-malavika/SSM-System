"""Quick test to check if the endpoint accepts POST requests"""
import requests

API_URL = "http://localhost:8000/api/v1/students/upload-report"

# Test OPTIONS to see allowed methods
print("Testing OPTIONS request...")
try:
    response = requests.options(API_URL)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Allow header: {response.headers.get('Allow', 'Not specified')}")
except Exception as e:
    print(f"OPTIONS Error: {e}")

print("\n" + "="*50 + "\n")

# Test POST without file to see if method is allowed
print("Testing POST request (without file)...")
try:
    response = requests.post(API_URL)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"POST Error: {e}")

print("\n" + "="*50 + "\n")

# Test GET to confirm it's not allowed
print("Testing GET request...")
try:
    response = requests.get(API_URL)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"GET Error: {e}")
