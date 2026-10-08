from langchain_core.language_models import BaseChatModel

from triage_bot.config import Settings
from triage_bot.llm.base import LLMFactory, LLMProvider
from triage_bot.llm.providers import OllamaFactory, OpenAIFactory, OpenRouterFactory

_REGISTRY: dict[LLMProvider, type[LLMFactory]] = {
    LLMProvider.OPENAI: OpenAIFactory,
    LLMProvider.OPENROUTER: OpenRouterFactory,
    LLMProvider.OLLAMA: OllamaFactory,
}


def register(provider: LLMProvider, factory_cls: type[LLMFactory]) -> None:
    _REGISTRY[provider] = factory_cls


def get_llm(settings: Settings) -> BaseChatModel:
    try:
        factory_cls = _REGISTRY[LLMProvider(settings.llm_provider)]
    except (KeyError, ValueError) as exc:
        supported = ", ".join(p.value for p in _REGISTRY)
        raise ValueError(f"Unsupported LLM provider '{settings.llm_provider}'. Supported: {supported}") from exc
    return factory_cls().create(settings)
