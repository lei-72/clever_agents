"""接口服务应用工厂。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.api.router import build_api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIdAndMetricsMiddleware
from app.schemas.common import MessageResponse

"""全局配置初始化"""
settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


"""应用生命周期管理器"""
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """处理应用启动与关闭生命周期。"""

    logger.info("Starting %s (%s)", settings.app_name, settings.environment)
    yield
    logger.info("Stopping %s", settings.app_name)


def create_app() -> FastAPI:
    """创建并配置接口服务应用实例。"""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    allow_origins = [o.strip() for o in (settings.cors_allow_origins or "").split(",") if o.strip()]
    if allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(RequestIdAndMetricsMiddleware)
    register_exception_handlers(app)
    app.include_router(build_api_router(settings))

    @app.get("/metrics", tags=["observability"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/", response_model=MessageResponse, tags=["meta"])
    async def root() -> MessageResponse:
        return MessageResponse(message="Clever Agents backend is running.")

    return app


app = create_app()
