from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable

class LlmClient(ABC):
    name = "base"
    @abstractmethod
    def is_alive(self) -> bool: ...
    @abstractmethod
    def chat(self, messages: list, stream: bool = False) -> str: ...
    def chat_stream(self, messages: list) -> Iterable[str]:
        yield self.chat(messages)
