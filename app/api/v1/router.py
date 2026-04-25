"""第一版路由定义。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.grading import router as grading_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.interview import router as interview_router
from app.api.v1.endpoints.orchestrator import router as orchestrator_router
from app.api.v1.endpoints.qa import router as qa_router
from app.api.v1.endpoints.rbac import router as rbac_router
from app.api.v1.endpoints.resume import router as resume_router

router = APIRouter()
router.include_router(health_router, prefix="/system", tags=["system"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(rbac_router, prefix="/rbac", tags=["rbac"])
router.include_router(orchestrator_router, prefix="/orchestrator", tags=["orchestrator"])
router.include_router(qa_router, prefix="/qa", tags=["qa"])
router.include_router(grading_router, prefix="/grading", tags=["grading"])
router.include_router(resume_router, prefix="/resume", tags=["resume"])
router.include_router(interview_router, prefix="/interview", tags=["interview"])
