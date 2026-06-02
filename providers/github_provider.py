import config
from .base import BaseProvider


class GitHubProvider(BaseProvider):
    name = "github"

    def is_available(self) -> bool:
        key = config.GITHUB_TOKEN
        return bool(key and "your_" not in key.lower() and "REMOVED" not in key)

    def generate(self, messages: list[dict], timeout: int) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=config.GITHUB_TOKEN,
            base_url="https://models.inference.ai.azure.com",
        )
        resp = client.chat.completions.create(
            model=config.GITHUB_MODEL,
            messages=messages,
            timeout=timeout,
        )
        text = resp.choices[0].message.content.strip()
        if not text:
            raise ValueError("GitHub Models returned empty response")
        return text
