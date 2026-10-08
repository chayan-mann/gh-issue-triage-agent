from langchain_core.language_models import BaseChatModel

from triage_bot.config import Settings
from triage_bot.llm.base import LLMFactory


class OpenAIFactory(LLMFactory):
    def create(self, settings: Settings) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=settings.llm_temperature,
        )


class OpenRouterFactory(LLMFactory):
    def create(self, settings: Settings) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=settings.llm_temperature,
            default_headers={"X-Title": "gh-issue-triage-bot"},
        )


class OllamaFactory(LLMFactory):
    def create(self, settings: Settings) -> BaseChatModel:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
        )
