from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-5"
    llm_fast_model: str = "claude-haiku-4-5"

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
