from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Property Intelligence"
    environment: str = "local"
    api_prefix: str = "/api"
    database_url: str = Field(default="sqlite:///./property_intelligence.db", alias="DATABASE_URL")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    data_dir: Path = Field(default=Path("../data/processed"), alias="DATA_DIR")
    model_dir: Path = Field(default=Path("../models"), alias="MODEL_DIR")
    embedding_model: str = Field(default="BAAI/bge-base-en-v1.5", alias="EMBEDDING_MODEL")
    embedding_device: str = Field(default="auto", alias="EMBEDDING_DEVICE")
    embedding_batch_size: int = Field(default=256, alias="EMBEDDING_BATCH_SIZE")
    rag_embedding_mode: str = Field(default="semantic", alias="RAG_EMBEDDING_MODE")
    llm_provider: str = Field(default="fallback", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.1:8b", alias="OLLAMA_MODEL")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    request_timeout_seconds: float = 8.0
    search_timeout_seconds: float = 20.0
    rate_limit_per_minute: int = 240

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
