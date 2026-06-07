"""
Application configuration loaded from environment variables.
All settings are type-safe via Pydantic BaseSettings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="InsurIQ", env="APP_NAME")
    app_env: str = Field(default="development", env="APP_ENV")
    app_port: int = Field(default=8000, env="APP_PORT")
    debug: bool = Field(default=True, env="DEBUG")

    # PostgreSQL
    database_url: str = Field(default="postgresql://insuriq_user:root123@localhost:5432/insuriq", env="DATABASE_URL")

    # OpenAI / API Gateway
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", env="OPENAI_BASE_URL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    openai_chat_model: str = Field(default="gpt-4o-mini", env="OPENAI_CHAT_MODEL")
    openai_max_tokens: int = Field(default=500, env="OPENAI_MAX_TOKENS")
    openai_embedding_batch_size: int = Field(default=100, env="OPENAI_EMBEDDING_BATCH_SIZE")

    # Redis (Upstash)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_ttl_seconds: int = Field(default=3600, env="REDIS_TTL_SECONDS")

    # LangSmith
    langchain_api_key: str = Field(default="", env="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="InsurIQ", env="LANGCHAIN_PROJECT")
    langchain_tracing_v2: bool = Field(default=True, env="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str = Field(default="https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT")

    # RAG
    rag_top_k_vector: int = Field(default=20, env="RAG_TOP_K_VECTOR")
    rag_top_k_fts: int = Field(default=20, env="RAG_TOP_K_FTS")
    rag_top_k_final: int = Field(default=5, env="RAG_TOP_K_FINAL")
    rag_similarity_threshold: float = Field(default=0.4, env="RAG_SIMILARITY_THRESHOLD")

    # Fraud scoring
    fraud_high_risk_threshold: int = Field(default=70, env="FRAUD_HIGH_RISK_THRESHOLD")
    fraud_medium_risk_threshold: int = Field(default=40, env="FRAUD_MEDIUM_RISK_THRESHOLD")

    # Data
    data_path: str = Field(default="./data/fraud_oracle_cleaned.csv", env="DATA_PATH")

    # ChromaDB
    chroma_persist_path: str = Field(default="./chroma_db", env="CHROMA_PERSIST_PATH")

    # Security
    secret_key: str = Field(default="insuriq-secret-key-change-in-production", env="SECRET_KEY")

    # Guardrails
    max_query_length: int = Field(default=500, env="MAX_QUERY_LENGTH")
    min_query_length: int = Field(default=10, env="MIN_QUERY_LENGTH")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
