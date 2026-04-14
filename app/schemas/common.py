"""通用响应数据模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查接口返回体。"""

    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["clever-agents-api"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["dev"])


class MessageResponse(BaseModel):
    """简单消息返回体。"""

    message: str
