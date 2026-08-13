import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-5"
    llm_fast_model: str = "claude-haiku-4-5"

    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "gemma4"

    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    openai_api_key: str = ""

    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "enterprise-knowledge"

    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "enterprise-ai-assistant"

    jwt_secret_key: str = "change-me-in-local-env"
    jwt_expiry_minutes: int = 60

    rate_limit_capacity: int = 20
    rate_limit_refill_per_sec: float = 0.5

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 8501
    backend_base_url: str = "http://backend:8000"
    log_level: str = "INFO"

    mcp_server_url: str = "http://mcp_server:9000"


def _configure_langsmith(settings: Settings) -> None:
    # LangChain/LangSmith's tracer reads raw process env vars directly, not
    # our Settings object - pydantic-settings loading .env into Settings
    # fields never touches os.environ. Without this, tracing silently never
    # activates even with LANGCHAIN_TRACING_V2=true in .env.
    if not settings.langchain_tracing_v2 or not settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    # LANGSMITH_* are the current SDK's env var names; LANGCHAIN_* are the
    # older aliases some components still read. Set both for safety.
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langchain_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langchain_project


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _configure_langsmith(settings)
    return settings
