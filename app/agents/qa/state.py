"""QA Agent 状态定义。"""

from __future__ import annotations

from typing import TypedDict

from app.schemas.qa import QASource


class QAAgentState(TypedDict, total=False):
    trace_id: str
    user_id: str | None
    session_id: str
    query: str
    top_k: int
    rerank_k: int
    query_type: str
    history: list[dict[str, str]]
    retrieved_sources: list[QASource]
    confidence: float
    answer: str
    should_escalate: bool
