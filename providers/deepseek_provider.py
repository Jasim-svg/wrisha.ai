import config
from .base import BaseProvider


class DeepSeekProvider(BaseProvider):
    name = "deepseek"

    def is_available(self) -> bool:
        key = config.DEEPSEEK_API_KEY
        return bool(key and "your_" not in key.lower() and "REMOVED" not in key)

    def generate(self, messages: list[dict], timeout: int) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )
        resp = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=messages,
            timeout=timeout,
        )
        text = resp.choices[0].message.content.strip()
        if not text:
            raise ValueError("DeepSeek returned empty response")
        return text
