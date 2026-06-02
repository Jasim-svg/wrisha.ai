"""
Tests the DeepSeek (OpenAI-compatible) API endpoint.
Requires DEEPSEEK_API_KEY in .env (or environment).
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config  # loads .env

BASE_URL = config.DEEPSEEK_BASE_URL


def test_api():
    from openai import OpenAI
    api_key = config.DEEPSEEK_API_KEY
    if not api_key or "your_" in api_key.lower():
        print("ERROR: DEEPSEEK_API_KEY not set in .env")
        return

    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    print(f"Testing DeepSeek at {BASE_URL} ...")

    try:
        resp = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=20,
            timeout=15,
        )
        print(f"Status: OK")
        print(f"Response: {resp.choices[0].message.content}")
        print("SUCCESS: DeepSeek API is working!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_api()
