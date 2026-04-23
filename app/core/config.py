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
    dashscope_api_key: str = ""
    openai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qa_chat_model: str = "qwen3.5-plus"
    qa_embedding_model: str = "text-embedding-v3"
    qa_embedding_dim: int = 1024
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/clever_agents"
    redis_url: str = "redis://localhost:6379/0"
    milvus_uri: str = "http://localhost:19530"
    milvus_collection: str = "qa_knowledge_chunks"
    qa_top_k: int = 6
    qa_rerank_k: int = 4
    qa_confidence_threshold: float = 0.55


def get_settings() -> Settings:
    """仅从环境变量读取 DASHSCOPE_API_KEY，其余使用代码默认值。"""

    return Settings(dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""))
