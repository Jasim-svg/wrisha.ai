"""
Tests the Gemini API connection using the new google-genai SDK.
Requires GEMINI_API_KEY in secrets/.env or .env.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config  # loads .env


def test_gemini():
    from google import genai

    api_key = config.GEMINI_API_KEY
    if not api_key or "your_" in api_key.lower():
        print("ERROR: GEMINI_API_KEY not set in .env")
        return

    key_preview = f"{api_key[:5]}...{api_key[-3:]}"
    print(f"API Key from config: {key_preview}")
    print(f"Model: {config.GEMINI_MODEL}")

    client = genai.Client(api_key=api_key)

    print("\nListing available models...")
    try:
        for m in client.models.list():
            print(f"- {m.name}")
    except Exception as e:
        print(f"Could not list models: {e}")

    print(f"\nTesting generation with {config.GEMINI_MODEL}...")
    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents="Hello! Say hi back in one short sentence.",
        )
        print(f"Response: {response.text}")
        print("SUCCESS: Gemini API is working!")
    except Exception as e:
        print(f"API Error: {e}")


if __name__ == "__main__":
    test_gemini()
