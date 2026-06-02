import config
from .gemini_provider import GeminiProvider
from .deepseek_provider import DeepSeekProvider
from .grok_provider import GrokProvider
from .github_provider import GitHubProvider
from .openrouter_provider import OpenRouterProvider

_REGISTRY = {
    "gemini":     GeminiProvider,
    "grok":       GrokProvider,
    "openrouter": OpenRouterProvider,
    "github":     GitHubProvider,
    "deepseek":   DeepSeekProvider,
}


class ProviderManager:
    def __init__(self):
        self._providers = []
        for name in config.PROVIDER_ORDER:
            cls = _REGISTRY.get(name)
            if cls:
                provider = cls()
                if provider.is_available():
                    self._providers.append(provider)
                    print(f"[providers] {name} available")
                else:
                    print(f"[providers] {name} skipped (no key)")
        self.last_provider: str | None = None

    def generate(self, messages: list[dict], timeout: int | None = None) -> str:
        if timeout is None:
            timeout = config.PROVIDER_TIMEOUT
        for provider in self._providers:
            try:
                text = provider.generate(messages, timeout)
                if text and text.strip():
                    self.last_provider = provider.name
                    print(f"[brain] answered by {provider.name}")
                    return text
            except Exception as e:
                print(f"[providers] {provider.name} failed: {e}")
        return ""

    def any_available(self) -> bool:
        return len(self._providers) > 0
