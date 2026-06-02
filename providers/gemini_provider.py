import config
from .base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "gemini"

    def is_available(self) -> bool:
        key = config.GEMINI_API_KEY
        return bool(key and "your_" not in key.lower() and "REMOVED" not in key)

    def generate(self, messages: list[dict], timeout: int) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)

        system_instruction = None
        contents = []
        for msg in messages:
            role = msg["role"]
            text = msg["content"]
            if role == "system":
                system_instruction = text
            elif role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=text)]))
            elif role == "assistant":
                contents.append(types.Content(role="model", parts=[types.Part(text=text)]))

        cfg = types.GenerateContentConfig(
            system_instruction=system_instruction,
        ) if system_instruction else None

        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            config=cfg,
            contents=contents,
        )

        text = response.text.strip() if response.text else ""
        if not text:
            raise ValueError("Gemini returned empty response")
        return text
