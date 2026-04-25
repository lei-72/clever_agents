"""Orchestrator 路由服务（Phase 3 MVP）。"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Awaitable, Callable

from app.core.errors import AppError
from app.schemas.grading import GradingRequest, GradingResponse
from app.schemas.interview import InterviewStartRequest, InterviewStartResponse
from app.schemas.orchestrator import (
    AgentName,
    OrchestratorExecuteRequest,
    IntentLabel,
    OrchestratorExecuteResponse,
    OrchestratorPipelineRequest,
    OrchestratorPipelineResponse,
    OrchestratorRequest,
    OrchestratorRouteResult,
    PipelineNodeTrace,
    PipelineTaskName,
    PipelineTaskSpec,
    PipelineTrace,
    PipelineType,
    SseEnvelope,
    SseEventType,
    TaskStatus,
    UnifiedPipelineOutput,
    UnifiedResultItem,
)
from app.schemas.qa import QARequest, QAResponse
from app.schemas.resume import ResumeReviewRequest, ResumeReviewResponse


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

    def __init__(
        self,
        qa_executor: Callable[[QARequest], Awaitable[QAResponse]] | None = None,
        grading_executor: Callable[[GradingRequest], Awaitable[GradingResponse]] | None = None,
        interview_executor: Callable[[InterviewStartRequest], Awaitable[InterviewStartResponse]] | None = None,
        resume_executor: Callable[[ResumeReviewRequest], Awaitable[ResumeReviewResponse]] | None = None,
    ) -> None:
        self._qa_executor = qa_executor
        self._grading_executor = grading_executor
        self._interview_executor = interview_executor
        self._resume_executor = resume_executor

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

    async def execute(self, request: OrchestratorExecuteRequest) -> OrchestratorExecuteResponse:
        """执行编排，当前仅接入 QA Agent 实现。"""

        route_result = self.route(request)
        qa_result: QAResponse | None = None
        grading_result: GradingResponse | None = None
        interview_result: InterviewStartResponse | None = None
        if route_result.agent == AgentName.QA_AGENT and self._qa_executor is not None:
            qa_result = await self._qa_executor(
                QARequest(
                    query=request.query,
                    session_id=request.session_id or "orchestrator-default",
                    user_id=request.user_id,
                )
            )
        if route_result.agent == AgentName.GRADING_AGENT and self._grading_executor is not None:
            if request.grading_payload is None:
                raise AppError(
                    code="BAD_REQUEST",
                    message="grading_payload is required when route targets grading agent.",
                    status_code=400,
                )
            grading_result = await self._grading_executor(request.grading_payload)
        if route_result.agent == AgentName.INTERVIEW_AGENT and self._interview_executor is not None:
            if request.interview_payload is None:
                raise AppError(
                    code="BAD_REQUEST",
                    message="interview_payload is required when route targets interview agent.",
                    status_code=400,
                )
            interview_result = await self._interview_executor(request.interview_payload)
        return OrchestratorExecuteResponse(
            route=route_result,
            qa_result=qa_result,
            grading_result=grading_result,
            interview_result=interview_result,
        )

    async def execute_pipeline(
        self,
        request: OrchestratorPipelineRequest,
    ) -> OrchestratorPipelineResponse:
        """执行复合意图流水线：拆解 -> 串联 -> 聚合 -> 追踪。"""

        pipeline_type = self._resolve_pipeline_type(request)
        tasks = self._build_tasks(request, pipeline_type)
        inferred_intents = self._infer_intents_from_tasks(tasks)
        pipeline_id = f"pipeline-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(UTC)
        node_traces: list[PipelineNodeTrace] = []
        raw_items: list[UnifiedResultItem] = []
        has_failure = False

        for task in tasks:
            started_ns = time.perf_counter_ns()
            status = TaskStatus.SUCCESS
            output_preview: dict[str, object] = {}
            error_message: str | None = None
            try:
                item = await self._run_task(task, request)
                raw_items.append(item)
                output_preview = {
                    "title": item.title,
                    "confidence": item.confidence,
                    "tags": item.tags[:3],
                }
            except (ValueError, AppError) as exc:
                has_failure = True
                status = TaskStatus.FAILED
                error_message = str(exc)
                output_preview = {}
            elapsed_ms = int((time.perf_counter_ns() - started_ns) / 1_000_000)
            node_traces.append(
                PipelineNodeTrace(
                    node_id=f"{pipeline_id}-{task.order}",
                    task=task.name,
                    agent=task.agent,
                    status=status,
                    elapsed_ms=elapsed_ms,
                    input_preview={"query": request.query[:120], "task_reason": task.reason},
                    output_preview=output_preview,
                    error_message=error_message,
                )
            )

        unified_items = self._normalize_and_merge(raw_items)
        unified_output = self._build_unified_output(pipeline_type, unified_items, request.query)
        finished_at = datetime.now(UTC)
        trace = PipelineTrace(
            pipeline_id=pipeline_id,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            total_elapsed_ms=max(0, int((finished_at - started_at).total_seconds() * 1000)),
            status=TaskStatus.FAILED if has_failure else TaskStatus.SUCCESS,
            nodes=node_traces,
        )
        return OrchestratorPipelineResponse(
            pipeline_type=pipeline_type,
            inferred_intents=inferred_intents,
            tasks=tasks,
            unified_output=unified_output,
            trace=trace if request.expect_trace else None,
        )

    def _resolve_pipeline_type(self, request: OrchestratorPipelineRequest) -> PipelineType:
        if request.pipeline_type != PipelineType.AUTO:
            return request.pipeline_type
        query = request.query.lower()
        coding_keywords = ("代码", "bug", "修复", "算法", "编程", "题解", "优化代码")
        if any(keyword in query for keyword in coding_keywords) or request.grading_payload is not None:
            return PipelineType.CODING_COACHING
        return PipelineType.JOB_COACHING

    def _build_tasks(
        self,
        request: OrchestratorPipelineRequest,
        pipeline_type: PipelineType,
    ) -> list[PipelineTaskSpec]:
        if pipeline_type == PipelineType.JOB_COACHING:
            return [
                PipelineTaskSpec(
                    name=PipelineTaskName.RESUME_REVIEW,
                    agent=AgentName.RESUME_AGENT,
                    order=1,
                    weight=0.35,
                    reason="简历诊断作为求职基础输入。",
                ),
                PipelineTaskSpec(
                    name=PipelineTaskName.INTERVIEW_SIMULATION,
                    agent=AgentName.INTERVIEW_AGENT,
                    order=2,
                    weight=0.3,
                    reason="面试模拟用于检验表达与技术能力。",
                ),
                PipelineTaskSpec(
                    name=PipelineTaskName.CAREER_QA,
                    agent=AgentName.QA_AGENT,
                    order=3,
                    weight=0.2,
                    reason="求职答疑补全策略建议。",
                ),
                PipelineTaskSpec(
                    name=PipelineTaskName.OFFER_ANALYSIS,
                    agent=AgentName.QA_AGENT,
                    order=4,
                    weight=0.15,
                    reason="Offer 分析输出最终决策建议。",
                ),
            ]
        return [
            PipelineTaskSpec(
                name=PipelineTaskName.CODING_INTENT_PARSE,
                agent=AgentName.QA_AGENT,
                order=1,
                weight=0.15,
                reason="先解析题意并拆解解题目标。",
            ),
            PipelineTaskSpec(
                name=PipelineTaskName.CODE_GRADING,
                agent=AgentName.GRADING_AGENT,
                order=2,
                weight=0.35,
                reason="执行代码批改并产出结构化评估。",
            ),
            PipelineTaskSpec(
                name=PipelineTaskName.BUG_FIX_QA,
                agent=AgentName.QA_AGENT,
                order=3,
                weight=0.2,
                reason="定位问题并提供修复建议。",
            ),
            PipelineTaskSpec(
                name=PipelineTaskName.KNOWLEDGE_EXPLAIN,
                agent=AgentName.QA_AGENT,
                order=4,
                weight=0.15,
                reason="讲解关键知识点。",
            ),
            PipelineTaskSpec(
                name=PipelineTaskName.OPTIMIZATION_QA,
                agent=AgentName.QA_AGENT,
                order=5,
                weight=0.15,
                reason="输出性能和可维护性优化方案。",
            ),
        ]

    async def _run_task(
        self,
        task: PipelineTaskSpec,
        request: OrchestratorPipelineRequest,
    ) -> UnifiedResultItem:
        if task.name == PipelineTaskName.RESUME_REVIEW:
            if self._resume_executor is None:
                raise AppError(code="EXECUTOR_NOT_CONFIGURED", message="resume executor is not configured", status_code=500)
            if request.resume_payload is None:
                raise AppError(
                    code="BAD_REQUEST",
                    message="resume_payload is required for resume_review task",
                    status_code=400,
                )
            result = await self._resume_executor(request.resume_payload)
            return UnifiedResultItem(
                task=task.name,
                title="简历诊断",
                summary=f"简历综合得分 {result.overall_score:.1f}/100，已给出分优先级修改建议。",
                confidence=0.86,
                source_agent=task.agent,
                tags=["resume", "diagnosis"],
                payload={"overall_score": result.overall_score, "trace_id": result.trace_id},
            )
        if task.name == PipelineTaskName.INTERVIEW_SIMULATION:
            if self._interview_executor is None:
                raise AppError(
                    code="EXECUTOR_NOT_CONFIGURED",
                    message="interview executor is not configured",
                    status_code=500,
                )
            if request.interview_payload is None:
                raise AppError(
                    code="BAD_REQUEST",
                    message="interview_payload is required for interview_simulation task",
                    status_code=400,
                )
            result = await self._interview_executor(request.interview_payload)
            return UnifiedResultItem(
                task=task.name,
                title="模拟面试启动",
                summary=f"已创建会话 {result.session.session_id}，当前阶段 {result.session.current_stage.value}。",
                confidence=0.82,
                source_agent=task.agent,
                tags=["interview", "session"],
                payload={"session_id": result.session.session_id, "status": result.session.status.value},
            )
        if task.name == PipelineTaskName.CODE_GRADING:
            if self._grading_executor is None:
                raise AppError(
                    code="EXECUTOR_NOT_CONFIGURED",
                    message="grading executor is not configured",
                    status_code=500,
                )
            if request.grading_payload is None:
                raise AppError(
                    code="BAD_REQUEST",
                    message="grading_payload is required for code_grading task",
                    status_code=400,
                )
            result = await self._grading_executor(request.grading_payload)
            return UnifiedResultItem(
                task=task.name,
                title="代码批改结果",
                summary=f"批改总分 {result.total_score:.1f}/{result.full_score:.1f}，已返回错因与优化建议。",
                confidence=0.88,
                source_agent=task.agent,
                tags=["grading", "code"],
                payload={"total_score": result.total_score, "trace_id": result.trace_id},
            )
        if self._qa_executor is None:
            raise AppError(code="EXECUTOR_NOT_CONFIGURED", message="qa executor is not configured", status_code=500)
        qa_query_map = {
            PipelineTaskName.CAREER_QA: f"请基于该用户诉求给出求职策略建议：{request.query}",
            PipelineTaskName.OFFER_ANALYSIS: f"请基于该用户诉求给出 offer 对比分析框架：{request.query}",
            PipelineTaskName.CODING_INTENT_PARSE: f"请解析这道代码题意并拆解目标：{request.query}",
            PipelineTaskName.BUG_FIX_QA: f"请定位潜在 bug 并给出修复方案：{request.query}",
            PipelineTaskName.KNOWLEDGE_EXPLAIN: f"请讲解这道题涉及的核心知识点：{request.query}",
            PipelineTaskName.OPTIMIZATION_QA: f"请给出可执行的代码优化策略：{request.query}",
        }
        result = await self._qa_executor(
            QARequest(
                query=qa_query_map[task.name],
                session_id=request.session_id or f"pipeline-{uuid.uuid4().hex[:8]}",
                user_id=request.user_id,
            )
        )
        return UnifiedResultItem(
            task=task.name,
            title=task.name.value,
            summary=result.answer.strip(),
            confidence=result.confidence,
            source_agent=task.agent,
            tags=["qa", task.name.value],
            payload={"trace_id": result.trace_id, "should_escalate": result.should_escalate},
        )

    @staticmethod
    def _infer_intents_from_tasks(tasks: list[PipelineTaskSpec]) -> list[IntentLabel]:
        intents: list[IntentLabel] = []
        for task in tasks:
            if task.agent == AgentName.RESUME_AGENT and IntentLabel.RESUME not in intents:
                intents.append(IntentLabel.RESUME)
            elif task.agent == AgentName.INTERVIEW_AGENT and IntentLabel.INTERVIEW not in intents:
                intents.append(IntentLabel.INTERVIEW)
            elif task.agent == AgentName.GRADING_AGENT and IntentLabel.GRADING not in intents:
                intents.append(IntentLabel.GRADING)
            elif task.agent == AgentName.QA_AGENT and IntentLabel.QA not in intents:
                intents.append(IntentLabel.QA)
        return intents

    @staticmethod
    def _normalize_and_merge(items: list[UnifiedResultItem]) -> list[UnifiedResultItem]:
        merged: dict[tuple[str, str], UnifiedResultItem] = {}
        for item in items:
            dedupe_key = (item.task.value, item.summary.strip().lower())
            if dedupe_key not in merged:
                merged[dedupe_key] = item
                continue
            existing = merged[dedupe_key]
            existing.confidence = max(existing.confidence, item.confidence)
            existing.tags = sorted(set(existing.tags + item.tags))
            existing.payload = {**existing.payload, **item.payload}
        return sorted(merged.values(), key=lambda item: item.confidence, reverse=True)

    @staticmethod
    def _build_unified_output(
        pipeline_type: PipelineType,
        items: list[UnifiedResultItem],
        query: str,
    ) -> UnifiedPipelineOutput:
        highlights = [item.summary for item in items[:3]]
        action_plan = [f"执行 {item.title}" for item in items[:5]]
        final_message = (
            f"已完成 {pipeline_type.value} 流水线，共产出 {len(items)} 个标准化结果项。"
            f" 你可以基于这些结果继续多轮追问，当前原始诉求：{query[:60]}"
        )
        return UnifiedPipelineOutput(
            highlights=highlights,
            action_plan=action_plan,
            result_items=items,
            final_message=final_message,
        )

    @staticmethod
    def _format_sse(envelope: SseEnvelope) -> str:
        payload = json.dumps(envelope.model_dump(), ensure_ascii=False)
        return f"event: {envelope.event.value}\ndata: {payload}\n\n"
