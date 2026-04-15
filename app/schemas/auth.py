"""认证与授权数据模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["student", "teacher", "admin"]


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    """登录返回令牌。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: Role


class CurrentUser(BaseModel):
    """当前认证用户。"""

    username: str
    role: Role
