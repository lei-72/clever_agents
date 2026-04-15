"""认证与 RBAC 依赖。"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.schemas.auth import CurrentUser, Role

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "认证失败。") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """解析并返回当前用户。"""

    if credentials is None:
        raise _unauthorized("缺少访问令牌。")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise _unauthorized("访问令牌无效或已过期。") from exc

    return CurrentUser(username=str(payload["sub"]), role=str(payload["role"]))


def require_roles(*allowed_roles: Role) -> Callable[[CurrentUser], CurrentUser]:
    """构建角色检查依赖。"""

    async def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="当前角色无权访问该资源。",
            )
        return current_user

    return checker
