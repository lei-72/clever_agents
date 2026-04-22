"""运行时配置工具。"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """从环境变量加载应用配置。"""

    app_name: str = "Clever Agents API"
    app_version: str = "0.1.0"
    environment: str = "dev"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    qa_chat_model: str = "gpt-4o-mini"
    qa_embedding_model: str = "text-embedding-3-small"
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/clever_agents"
    redis_url: str = "redis://localhost:6379/0"
    milvus_uri: str = "http://localhost:19530"
    milvus_collection: str = "qa_knowledge_chunks"
    qa_top_k: int = 6
    qa_rerank_k: int = 4
    qa_confidence_threshold: float = 0.55


def get_settings() -> Settings:
    """基于环境变量构建配置，并提供安全默认值。"""

    return Settings(
        app_name=os.getenv("APP_NAME", "Clever Agents API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        environment=os.getenv("APP_ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-this-in-production"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        qa_chat_model=os.getenv("QA_CHAT_MODEL", "gpt-4o-mini"),
        qa_embedding_model=os.getenv("QA_EMBEDDING_MODEL", "text-embedding-3-small"),
        postgres_dsn=os.getenv(
            "POSTGRES_DSN",
            "postgresql://postgres:postgres@localhost:5432/clever_agents",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        milvus_uri=os.getenv("MILVUS_URI", "http://localhost:19530"),
        milvus_collection=os.getenv("MILVUS_COLLECTION", "qa_knowledge_chunks"),
        qa_top_k=int(os.getenv("QA_TOP_K", "6")),
        qa_rerank_k=int(os.getenv("QA_RERANK_K", "4")),
        qa_confidence_threshold=float(os.getenv("QA_CONFIDENCE_THRESHOLD", "0.55")),
    )
