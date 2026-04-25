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
    qa_request_timeout_seconds: float = 35.0

    # CORS（前端本地开发/联调）
    # 逗号分隔，例如: "http://localhost:3000,http://127.0.0.1:3000"
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    # LLM 调用韧性配置（超时/重试/灰度/熔断）
    llm_timeout_seconds: float = 120.0
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 0.6
    llm_gray_percent: int = 0
    llm_gray_chat_model: str = "qwen3.5-plus"
    llm_concurrency: int = 32
    llm_circuit_fail_threshold: int = 8
    llm_circuit_open_seconds: int = 20
    enable_multi_agent_pipeline: bool = False


def get_settings() -> Settings:
    """从环境变量读取关键线上配置，其余使用代码默认值。"""

    def _get_int(name: str, default: int) -> int:
        raw = os.getenv(name)
        return default if raw is None or raw.strip() == "" else int(raw)

    def _get_float(name: str, default: float) -> float:
        raw = os.getenv(name)
        return default if raw is None or raw.strip() == "" else float(raw)

    def _get_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None or raw.strip() == "":
            return default
        return raw.strip().lower() in ("1", "true", "yes", "y", "on")

    return Settings(
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
        cors_allow_origins=os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        ),
        llm_timeout_seconds=_get_float("LLM_TIMEOUT_SECONDS", 120.0),
        qa_request_timeout_seconds=_get_float("QA_REQUEST_TIMEOUT_SECONDS", 35.0),
        llm_max_retries=_get_int("LLM_MAX_RETRIES", 2),
        llm_retry_backoff_seconds=_get_float("LLM_RETRY_BACKOFF_SECONDS", 0.6),
        llm_gray_percent=_get_int("LLM_GRAY_PERCENT", 0),
        llm_gray_chat_model=os.getenv("LLM_GRAY_CHAT_MODEL", "qwen3.5-plus"),
        llm_concurrency=_get_int("LLM_CONCURRENCY", 32),
        llm_circuit_fail_threshold=_get_int("LLM_CIRCUIT_FAIL_THRESHOLD", 8),
        llm_circuit_open_seconds=_get_int("LLM_CIRCUIT_OPEN_SECONDS", 20),
        enable_multi_agent_pipeline=_get_bool("ENABLE_MULTI_AGENT_PIPELINE", False),
    )
