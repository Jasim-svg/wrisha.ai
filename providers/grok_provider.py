import config
from .base import BaseProvider


class GrokProvider(BaseProvider):
    name = "grok"

    def is_available(self) -> bool:
        key = config.GROK_API_KEY
        return bool(key and "your_" not in key.lower() and "REMOVED" not in key)

    def generate(self, messages: list[dict], timeout: int) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=config.GROK_API_KEY,
            base_url="https://api.x.ai/v1",
        )
        resp = client.chat.completions.create(
            model=config.GROK_MODEL,
            messages=messages,
            timeout=timeout,
        )
        text = resp.choices[0].message.content.strip()
        if not text:
            raise ValueError("Grok returned empty response")
        return text
