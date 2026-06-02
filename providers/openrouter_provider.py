import config
from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    def is_available(self) -> bool:
        key = config.OPENROUTER_API_KEY
        return bool(key and "your_" not in key.lower() and "REMOVED" not in key)

    def generate(self, messages: list[dict], timeout: int) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/Jasim-svg/wrisha.ai",
                "X-Title": "Wrisha AI",
            },
        )
        resp = client.chat.completions.create(
            model=config.OPENROUTER_MODEL,
            messages=messages,
            timeout=timeout,
        )
        text = resp.choices[0].message.content.strip()
        if not text:
            raise ValueError("OpenRouter returned empty response")
        return text
