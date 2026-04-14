"""接口服务应用工厂。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.router import build_api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.schemas.common import MessageResponse

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


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
    register_exception_handlers(app)
    app.include_router(build_api_router(settings))

    @app.get("/", response_model=MessageResponse, tags=["meta"])
    async def root() -> MessageResponse:
        return MessageResponse(message="Clever Agents backend is running.")

    return app


app = create_app()
