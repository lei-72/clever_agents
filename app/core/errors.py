from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    """可控业务异常：用于返回稳定的结构化 4xx/5xx。"""

    code: str
    message: str
    status_code: int = 400
    details: object | None = None

