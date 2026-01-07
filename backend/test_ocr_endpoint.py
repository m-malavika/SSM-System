"""
Test script for the OCR upload-report endpoint
"""
import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/v1/students/upload-report"

# Path to your test image
IMAGE_PATH = "path/to/your/report_image.jpg"  # Update this path

def test_upload_report():
    """Test the upload-report endpoint"""
    try:
        # Open and send the image file
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": (IMAGE_PATH.split("/")[-1], f, "image/jpeg")}
            
            print("Uploading image for OCR processing...")
            response = requests.post(API_URL, files=files)
            
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Success!")
                print(f"Method used: {data.get('method')}")
                print(f"Tables found: {data.get('tables', [])}")
                print(f"\nFull response:\n{json.dumps(data, indent=2)}")
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(response.json())
                
    except FileNotFoundError:
        print(f"❌ Image file not found: {IMAGE_PATH}")
        print("Please update IMAGE_PATH in the script")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    test_upload_report()
