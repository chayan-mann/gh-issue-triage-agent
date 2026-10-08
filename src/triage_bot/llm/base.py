from abc import ABC, abstractmethod
from enum import StrEnum

from langchain_core.language_models import BaseChatModel

from triage_bot.config import Settings


class LLMProvider(StrEnum):
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class LLMFactory(ABC):
    @abstractmethod
    def create(self, settings: Settings) -> BaseChatModel: ...
