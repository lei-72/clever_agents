"""第一版路由定义。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router

router = APIRouter()
router.include_router(health_router, prefix="/system", tags=["system"])
