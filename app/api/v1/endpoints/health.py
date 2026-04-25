"""健康检查与就绪检查接口。"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthResponse, MessageResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """服务存活检查接口。"""

    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="clever-agents-api",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=MessageResponse)
async def readiness_check() -> MessageResponse:
    """本地/开发环境就绪检查接口。"""

    return MessageResponse(message="ready")


@router.get("/llm")
async def llm_status() -> dict[str, object]:
    """LLM 运行配置与连通性提示（不暴露密钥）。"""

    settings = get_settings()
    return {
        "configured": bool(settings.dashscope_api_key),
        "base_url": settings.openai_base_url,
        "chat_model": settings.qa_chat_model,
        "embedding_model": settings.qa_embedding_model,
        "timeout_seconds": settings.llm_timeout_seconds,
    }
