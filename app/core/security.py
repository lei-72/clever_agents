"""JWT 与密码处理工具。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings


def _urlsafe_b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")
    # base64.urlsafe_b64encode(raw): 对字节数据进行 URL 安全的 Base64 编码
    # .rstrip(b"="): 去除末尾的填充字符 "="
    # .decode("utf-8"): 将字节数据解码为 UTF-8 字符串

def _urlsafe_b64decode(raw: str) -> bytes:
    padding = "=" * ((4 - len(raw) % 4) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("utf-8"))


def hash_password(password: str) -> str:
    """返回密码摘要值（最小可用实现）。"""

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与摘要是否匹配。"""

    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(subject: str, role: str) -> str:
    """创建 HS256 JWT 访问令牌。"""

    settings = get_settings()
    now = datetime.now(UTC)
    expire_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    header_b64 = _urlsafe_b64encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    payload_b64 = _urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    signature_b64 = _urlsafe_b64encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> dict[str, str | int]:
    """验证并解析访问令牌。"""

    settings = get_settings()
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    actual_signature = _urlsafe_b64decode(signature_b64)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise ValueError("Invalid token signature")

    payload_raw = _urlsafe_b64decode(payload_b64)
    payload = json.loads(payload_raw.decode("utf-8"))
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise ValueError("Invalid exp claim")

    now_ts = int(datetime.now(UTC).timestamp())
    if now_ts >= exp:
        raise ValueError("Token expired")

    if not isinstance(payload.get("sub"), str):
        raise ValueError("Invalid sub claim")
    if not isinstance(payload.get("role"), str):
        raise ValueError("Invalid role claim")
    return payload
