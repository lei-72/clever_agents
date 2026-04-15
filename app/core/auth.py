"""认证核心逻辑与最小用户仓储。"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.security import hash_password, verify_password
from app.schemas.auth import Role


@dataclass(frozen=True, slots=True)
class UserRecord:
    username: str
    role: Role
    password_hash: str


_USER_STORE: dict[str, UserRecord] = {
    "student_demo": UserRecord(
        username="student_demo",
        role="student",
        password_hash=hash_password("student123"),
    ),
    "teacher_demo": UserRecord(
        username="teacher_demo",
        role="teacher",
        password_hash=hash_password("teacher123"),
    ),
    "admin_demo": UserRecord(
        username="admin_demo",
        role="admin",
        password_hash=hash_password("admin123"),
    ),
}


def authenticate_user(username: str, password: str) -> UserRecord | None:
    """认证用户名密码，成功返回用户信息。"""

    user = _USER_STORE.get(username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
