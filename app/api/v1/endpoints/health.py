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
