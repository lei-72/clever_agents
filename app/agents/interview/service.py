"""Interview Agent 对外服务封装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewReportGenerateResponse,
    InterviewReportQueryResponse,
    InterviewSessionSnapshot,
    InterviewStage,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewStatus,
)

from .graph import build_interview_graph
from .nodes import AsyncInterviewNodes
from .tools import InterviewAgentTools


@dataclass(slots=True)
class InterviewAgentService:
    """Interview Agent 运行入口。"""

    graph_app: object
    tools: InterviewAgentTools
    nodes: AsyncInterviewNodes
    session_store: dict[str, dict[str, object]]

    @classmethod
    async def create(cls) -> "InterviewAgentService":
        tools = InterviewAgentTools()
        nodes = AsyncInterviewNodes(tools=tools)
        graph_app = build_interview_graph(nodes)
        return cls(graph_app=graph_app, tools=tools, nodes=nodes, session_store={})

    async def start(self, request: InterviewStartRequest) -> InterviewStartResponse:
        session_id = f"interview-{uuid.uuid4().hex[:12]}"
        state = {
            "session_id": session_id,
            "candidate_id": request.candidate_id,
            "status": InterviewStatus.RUNNING,
            "current_stage": InterviewStage.INTRO,
            "resume_profile": request.resume_profile,
            "history_performance": request.history_performance,
            "weak_tag_pool": request.weak_tag_pool,
            "asked_signatures": [item.question_signature for item in request.history_performance],
            "asked_questions": [],
            "qna_turns": [],
            "follow_up_chain": {},
            "weak_tag_marks": [],
            "assessment_points": [],
            "stage_logs": [],
            "stage_scores": [],
            "pending_question": None,
            "report_ready": False,
            "report": None,
            "async_report_job_id": None,
            "input_answer": None,
            "interrupt": False,
            "jump_to_stage": None,
            "rollback_to_stage": None,
        }
        first_state = await self.nodes.intro_stage(state)
        state.update(first_state)
        self.session_store[session_id] = dict(state)
        return InterviewStartResponse(session=self._snapshot(state))

    async def answer(self, session_id: str, request: InterviewAnswerRequest) -> InterviewAnswerResponse:
        state = self.session_store.get(session_id)
        if state is None:
            raise ValueError(f"Interview session not found: {session_id}")

        next_state = dict(state)
        next_state["input_answer"] = request.answer
        next_state["jump_to_stage"] = request.jump_to_stage
        next_state["rollback_to_stage"] = request.rollback_to_stage
        next_state["interrupt"] = request.interrupt

        applied = await self.nodes.apply_answer(next_state)
        next_state.update(applied)

        if request.interrupt:
            next_state["status"] = InterviewStatus.INTERRUPTED
            next_state["pending_question"] = None
            self.session_store[session_id] = dict(next_state)
            return InterviewAnswerResponse(session=self._snapshot(next_state))

        current_stage = next_state.get("current_stage", InterviewStage.INTRO)
        if current_stage == InterviewStage.REPORT:
            next_state["status"] = InterviewStatus.COMPLETED
            next_state["pending_question"] = None
            self.session_store[session_id] = dict(next_state)
            return InterviewAnswerResponse(session=self._snapshot(next_state))

        target_stage = self.nodes.next_stage(next_state)
        if target_stage == InterviewStage.INTRO:
            stage_payload = await self.nodes.intro_stage(next_state)
        elif target_stage == InterviewStage.TECH:
            stage_payload = await self.nodes.tech_stage(next_state)
        elif target_stage == InterviewStage.PROJECT:
            stage_payload = await self.nodes.project_stage(next_state)
        else:
            stage_payload = await self.nodes.report_stage(next_state)

        next_state.update(stage_payload)
        self.session_store[session_id] = dict(next_state)
        return InterviewAnswerResponse(session=self._snapshot(next_state))

    async def generate_report(self, session_id: str) -> InterviewReportGenerateResponse:
        state = self.session_store.get(session_id)
        if state is None:
            raise ValueError(f"Interview session not found: {session_id}")

        points = state.get("assessment_points", [])
        self.tools.schedule_report_job(session_id=session_id, points=points)
        report = await self.tools.get_report_if_ready(session_id)
        if report is not None:
            state["report_ready"] = True
            state["report"] = report
            state["status"] = InterviewStatus.COMPLETED
            self.session_store[session_id] = state
        return InterviewReportGenerateResponse(
            session_id=session_id,
            report_status="ready" if report is not None else "generating",
            report=report,
        )

    async def query_report(self, session_id: str) -> InterviewReportQueryResponse:
        state = self.session_store.get(session_id)
        if state is None:
            raise ValueError(f"Interview session not found: {session_id}")

        report = state.get("report")
        if report is None:
            report = await self.tools.get_report_if_ready(session_id)
            if report is not None:
                state["report"] = report
                state["report_ready"] = True
                state["status"] = InterviewStatus.COMPLETED
                self.session_store[session_id] = state
        return InterviewReportQueryResponse(
            report_status="ready" if report is not None else "generating",
            report=report,
        )

    def get_session(self, session_id: str) -> InterviewSessionSnapshot:
        state = self.session_store.get(session_id)
        if state is None:
            raise ValueError(f"Interview session not found: {session_id}")
        return self._snapshot(state)

    @staticmethod
    def _snapshot(state: dict[str, object]) -> InterviewSessionSnapshot:
        return InterviewSessionSnapshot(
            session_id=str(state["session_id"]),
            candidate_id=str(state["candidate_id"]),
            status=state.get("status", InterviewStatus.RUNNING),
            current_stage=state.get("current_stage", InterviewStage.INTRO),
            pending_question=state.get("pending_question"),
            asked_questions=state.get("asked_questions", []),
            qna_turns=state.get("qna_turns", []),
            follow_up_chain=state.get("follow_up_chain", {}),
            weak_tag_marks=state.get("weak_tag_marks", []),
            assessment_points=state.get("assessment_points", []),
            stage_logs=state.get("stage_logs", []),
            stage_scores=state.get("stage_scores", []),
            report_ready=bool(state.get("report_ready", False)),
            report=state.get("report"),
        )
