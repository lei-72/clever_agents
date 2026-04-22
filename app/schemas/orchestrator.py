"""编排层请求与响应模型（Phase 3 MVP）。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class IntentLabel(str, Enum):
    """编排层支持的最小意图集合。

    说明：当前为 Phase 3 MVP 标签集，后续可按分类器能力扩展。
    """

    QA = "qa"
    GRADING = "grading"
    RESUME = "resume"
    INTERVIEW = "interview"
    UNKNOWN = "unknown"


class AgentName(str, Enum):
    """可被编排层选择的 Agent 标识。"""

    QA_AGENT = "qa_agent"
    GRADING_AGENT = "grading_agent"
    RESUME_AGENT = "resume_agent"
    INTERVIEW_AGENT = "interview_agent"
    FALLBACK_AGENT = "fallback_agent"


class OrchestratorRequest(BaseModel):
    """统一编排请求。"""

    query: str = Field(..., min_length=1, description="用户输入内容。")
    user_id: str | None = Field(default=None, description="调用方用户标识。")
    session_id: str | None = Field(default=None, description="会话标识。")


class OrchestratorRouteResult(BaseModel):
    """编排路由结果。"""

    intent: IntentLabel
    agent: AgentName
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., description="路由原因说明。")


class OrchestratorRouteResponse(BaseModel):
    """同步路由响应。"""

    route: OrchestratorRouteResult
    message: str = Field(default="routed")


class SseEventType(str, Enum):
    """SSE 事件类型。

    协议约定：
    - route: 路由决策
    - delta: 增量内容
    - done: 流结束
    - error: 错误信息
    """

    ROUTE = "route"
    DELTA = "delta"
    DONE = "done"
    ERROR = "error"


class SseEnvelope(BaseModel):
    """统一 SSE 事件包结构。

    前后端统一结构：{"event": "...", "data": {...}}
    """

    event: SseEventType
    data: dict[str, object]
