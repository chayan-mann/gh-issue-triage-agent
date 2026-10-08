from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: Literal["openai", "openrouter", "ollama"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    openai_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_base_url: str = "http://localhost:11434"

    github_app_id: str = ""
    github_app_private_key_path: Path = Path("triage-bot.private-key.pem")
    github_webhook_secret: SecretStr = SecretStr("")
    github_api_url: str = "https://api.github.com"

    dry_run: bool = False
    allowed_labels: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["bug", "feature", "docs"])
    log_level: str = "INFO"

    @field_validator("allowed_labels", mode="before")
    @classmethod
    def _split_labels(cls, value: object) -> object:
        if isinstance(value, str):
            return [label.strip() for label in value.split(",") if label.strip()]
        return value

    @model_validator(mode="after")
    def _check_provider_key(self) -> "Settings":
        required = {"openai": self.openai_api_key, "openrouter": self.openrouter_api_key}
        if self.llm_provider in required and not required[self.llm_provider]:
            raise ValueError(f"{self.llm_provider.upper()}_API_KEY is required when LLM_PROVIDER={self.llm_provider}")
        return self

    @property
    def github_private_key(self) -> str:
        return self.github_app_private_key_path.read_text()


@lru_cache
def get_settings() -> Settings:
    return Settings()
