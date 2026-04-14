"""顶层 API 路由组装。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.router import router as v1_router
from app.core.config import Settings


def build_api_router(settings: Settings) -> APIRouter:
    """构建并返回根级 API 路由。"""

    router = APIRouter()
    router.include_router(v1_router, prefix=settings.api_v1_prefix, tags=["v1"])
    return router
