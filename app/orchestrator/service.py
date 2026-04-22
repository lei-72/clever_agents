"""Orchestrator 路由服务（Phase 3 MVP）。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Awaitable, Callable

from app.schemas.orchestrator import (
    AgentName,
    IntentLabel,
    OrchestratorExecuteResponse,
    OrchestratorRequest,
    OrchestratorRouteResult,
    SseEnvelope,
    SseEventType,
)
from app.schemas.qa import QARequest, QAResponse


class OrchestratorService:
    """意图识别与 Agent 选择服务。

    Phase 3 范围说明：
    - 仅做编排入口的意图识别与 Agent 选择
    - 暂不执行具体 Agent 业务，不在此层写 RAG/LLM 逻辑
    """

    # PHASE3-MVP: 关键词规则路由（后续可替换为分类模型）
    _INTENT_RULES: tuple[tuple[IntentLabel, AgentName, tuple[str, ...], str], ...] = (
        (
            IntentLabel.GRADING,
            AgentName.GRADING_AGENT,
            ("批改", "评分", "作业", "试卷", "judge0", "grade", "grading"),
            "检测到批改类关键词，优先走 Grading Agent。",
        ),
        (
            IntentLabel.RESUME,
            AgentName.RESUME_AGENT,
            ("简历", "resume", "cv"),
            "检测到简历审查相关关键词，路由到 Resume Agent。",
        ),
        (
            IntentLabel.INTERVIEW,
            AgentName.INTERVIEW_AGENT,
            ("面试", "interview", "模拟面"),
            "检测到面试训练相关关键词，路由到 Interview Agent。",
        ),
    )

    def __init__(self, qa_executor: Callable[[QARequest], Awaitable[QAResponse]] | None = None) -> None:
        self._qa_executor = qa_executor

    def route(self, request: OrchestratorRequest) -> OrchestratorRouteResult:
        """基于规则进行意图识别并返回路由结果。"""

        normalized_query = request.query.strip().lower()
        for intent, agent, keywords, reason in self._INTENT_RULES:
            if any(keyword in normalized_query for keyword in keywords):
                return OrchestratorRouteResult(
                    intent=intent,
                    agent=agent,
                    confidence=0.86,
                    reason=reason,
                )

        # PHASE3-MVP: 默认兜底到 QA Agent，保证编排入口可用。
        return OrchestratorRouteResult(
            intent=IntentLabel.QA,
            agent=AgentName.QA_AGENT,
            confidence=0.65,
            reason="未命中特殊意图，默认路由到 QA Agent。",
        )

    async def stream_route_events(
        self,
        request: OrchestratorRequest,
    ) -> AsyncIterator[str]:
        """返回统一 SSE 协议数据流。

        事件顺序约定（前后端联调协议）：
        1) route: 返回路由决策
        2) delta: 返回阶段性文本（MVP 占位）
        3) done : 返回流结束信号
        """

        route_result = self.route(request)

        # PHASE3-MVP: 首事件固定为 route，便于前端先渲染路由信息。
        route_event = SseEnvelope(
            event=SseEventType.ROUTE,
            data={
                "intent": route_result.intent.value,
                "agent": route_result.agent.value,
                "confidence": route_result.confidence,
                "reason": route_result.reason,
            },
        )
        yield self._format_sse(route_event)

        # PHASE3-MVP: delta 为占位输出；后续可替换为真实 Agent 流式 token。
        delta_event = SseEnvelope(
            event=SseEventType.DELTA,
            data={
                "content": f"[MVP] Routed to {route_result.agent.value}.",
            },
        )
        yield self._format_sse(delta_event)

        # PHASE3-MVP: done 作为统一结束标记，前端据此关闭 loading。
        done_event = SseEnvelope(
            event=SseEventType.DONE,
            data={"status": "completed"},
        )
        yield self._format_sse(done_event)

    async def execute(self, request: OrchestratorRequest) -> OrchestratorExecuteResponse:
        """执行编排，当前仅接入 QA Agent 实现。"""

        route_result = self.route(request)
        qa_result: QAResponse | None = None
        if route_result.agent == AgentName.QA_AGENT and self._qa_executor is not None:
            qa_result = await self._qa_executor(
                QARequest(
                    query=request.query,
                    session_id=request.session_id or "orchestrator-default",
                    user_id=request.user_id,
                )
            )
        return OrchestratorExecuteResponse(route=route_result, qa_result=qa_result)

    @staticmethod
    def _format_sse(envelope: SseEnvelope) -> str:
        payload = json.dumps(envelope.model_dump(), ensure_ascii=False)
        return f"event: {envelope.event.value}\ndata: {payload}\n\n"
