import requests
import json

API_KEY = "sk-uqvPJsGfmldr2mXvA349YQRR2792eWAaWmtd7adD0kvyODx8"
BASE_URL = "https://agentrouter.org/api/v1" # Standard convention, trying this first

def test_api():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # payload for a generic model, hoping it routes to something default or standard like gpt-3.5 or gemini
    # agentrouter might require a specific model name. I'll try 'gpt-4o-mini' or just 'default'.
    payload = {
        "model": "gpt-4o-mini", 
        "messages": [{"role": "user", "content": "Hello, are you working?"}],
        "max_tokens": 10
    }
    
    print(f"Testing URL: {BASE_URL}/chat/completions")
    
    try:
        response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: API is working!")
        elif response.status_code == 404:
            # Try without /api/v1
            print("Retrying with root URL...")
            response = requests.post("https://agentrouter.org/v1/chat/completions", headers=headers, json=payload, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
