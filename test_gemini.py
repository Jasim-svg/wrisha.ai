import google.generativeai as genai
import config
import os

print(f"API Key from config: {config.GEMINI_API_KEY[:5]}...{config.GEMINI_API_KEY[-3:] if config.GEMINI_API_KEY else 'None'}")

if "YOUR_API_KEY" in config.GEMINI_API_KEY:
    print("ERROR: You have not replaced the placeholder API key in config.py!")
else:
    genai.configure(api_key=config.GEMINI_API_KEY)
    
    print("Listing available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
        
        print("\nTesting Generation with gemini-1.5-flash...")
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Hello")
            print(f"Response (1.5-flash): {response.text}")
            print("SUCCESS with gemini-1.5-flash")
        except Exception as e:
            print(f"Failed 1.5-flash: {e}")

        print("\nTesting Generation with gemini-flash-latest...")
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content("Hello")
            print(f"Response (flash-latest): {response.text}")
            print("SUCCESS with gemini-flash-latest")
        except Exception as e:
            print(f"Failed flash-latest: {e}")
        
    except Exception as e:
        print(f"\nAPI Error: {e}")
