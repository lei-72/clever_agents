"""第一版路由定义。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.rbac import router as rbac_router

router = APIRouter()
router.include_router(health_router, prefix="/system", tags=["system"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(rbac_router, prefix="/rbac", tags=["rbac"])
