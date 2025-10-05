import requests
import json

# Test the backend
url = "http://localhost:8000/analyze"

# Test with sample file
with open("../file-cleanser/data/input/sample.png", "rb") as f:
    files = {"files": ("sample.png", f, "image/png")}
    
    try:
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Backend is working!")
            print("Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"ERROR: Connection error: {e}")
        print("Make sure the backend is running on http://localhost:8000")
