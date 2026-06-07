"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://haccp:haccp_dev_password@[::1]:5432/haccp_db"
    )
    database_url_sync: str = (
        "postgresql://haccp:haccp_dev_password@[::1]:5432/haccp_db"
    )

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "regulatory_docs"

    # LLM (OpenRouter)
    openrouter_api_key: str = ""
    openrouter_model: str = "z-ai/glm-5"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "http://localhost:8000"
    openrouter_app_name: str = "HACCP AI System"

    # Embeddings
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "haccp-ai-system"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # Tavily (optional — for regulatory web search)
    tavily_api_key: str = ""

    # Server
    agent_host: str = "0.0.0.0"
    agent_port: int = 8000
    cors_origins: str = "http://localhost:8080"

    # RAG
    chunk_size: int = 1500
    chunk_overlap: int = 300
    retrieval_top_k: int = 5
    retrieval_confidence_threshold: float = 0.65

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
