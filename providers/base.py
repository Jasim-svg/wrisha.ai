class BaseProvider:
    name: str = "base"

    def is_available(self) -> bool:
        raise NotImplementedError

    def generate(self, messages: list[dict], timeout: int) -> str:
        raise NotImplementedError
