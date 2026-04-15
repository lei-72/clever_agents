"""RBAC 最小闭环接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user, require_roles
from app.schemas.auth import CurrentUser
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/me", response_model=CurrentUser)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """返回当前登录用户。"""

    return current_user


@router.get("/teacher-area", response_model=MessageResponse)
async def teacher_area(
    _: CurrentUser = Depends(require_roles("teacher", "admin")),
) -> MessageResponse:
    """教师及管理员可访问。"""

    return MessageResponse(message="teacher access granted")


@router.get("/admin-area", response_model=MessageResponse)
async def admin_area(
    _: CurrentUser = Depends(require_roles("admin")),
) -> MessageResponse:
    """仅管理员可访问。"""

    return MessageResponse(message="admin access granted")
