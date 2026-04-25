"""Interview Agent 节点函数。"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.interview import (
    InterviewAnswerTurn,
    InterviewLifecycleLog,
    InterviewStage,
    InterviewStatus,
)

from .state import InterviewAgentState
from .tools import InterviewAgentTools, stage_order


@dataclass(slots=True)
class AsyncInterviewNodes:
    """面试流程节点集合。"""

    tools: InterviewAgentTools

    async def intro_stage(self, state: InterviewAgentState) -> InterviewAgentState:
        return self._build_stage_question(state, InterviewStage.INTRO)

    async def tech_stage(self, state: InterviewAgentState) -> InterviewAgentState:
        return self._build_stage_question(state, InterviewStage.TECH)

    async def project_stage(self, state: InterviewAgentState) -> InterviewAgentState:
        return self._build_stage_question(state, InterviewStage.PROJECT)

    async def report_stage(self, state: InterviewAgentState) -> InterviewAgentState:
        # REPORT 阶段仍会出收尾问题，便于形成完整四阶段交互。
        stage_payload = self._build_stage_question(state, InterviewStage.REPORT)
        points = state.get("assessment_points", [])
        stage_scores = self.tools.aggregate_stage_scores(points)
        job_id = self.tools.schedule_report_job(session_id=state["session_id"], points=points)
        stage_payload["stage_scores"] = stage_scores
        stage_payload["async_report_job_id"] = job_id
        stage_payload["report_ready"] = False
        return stage_payload

    async def apply_answer(self, state: InterviewAgentState) -> InterviewAgentState:
        if state.get("interrupt"):
            return {"status": InterviewStatus.INTERRUPTED}

        question = state.get("pending_question")
        answer = (state.get("input_answer") or "").strip()
        if question is None or not answer:
            return {}

        turn = InterviewAnswerTurn(question=question, answer=answer)
        points = list(state.get("assessment_points", []))
        point = self.tools.score_turn(
            question=question,
            answer=answer,
            weak_tag_pool=state.get("weak_tag_pool", []),
        )
        points.append(point)

        weak_marks = list(state.get("weak_tag_marks", []))
        weak_marks.extend(point.weak_tags)

        qna_turns = list(state.get("qna_turns", []))
        qna_turns.append(turn)

        follow_up_chain = dict(state.get("follow_up_chain", {}))
        if question.follow_up_to:
            follow_up_chain.setdefault(question.follow_up_to, []).append(question.question_id)

        return {
            "qna_turns": qna_turns,
            "assessment_points": points,
            "weak_tag_marks": weak_marks,
            "follow_up_chain": follow_up_chain,
            "pending_question": None,
            "input_answer": None,
        }

    async def finalize_report(self, state: InterviewAgentState) -> InterviewAgentState:
        if state.get("status") == InterviewStatus.INTERRUPTED:
            return {"report_ready": False}

        report = await self.tools.get_report_if_ready(state["session_id"])
        if report is None:
            return {"report_ready": False}
        return {"report_ready": True, "report": report, "status": InterviewStatus.COMPLETED}

    def next_stage(self, state: InterviewAgentState) -> InterviewStage:
        current = state.get("current_stage", InterviewStage.INTRO)
        rollback = state.get("rollback_to_stage")
        jump = state.get("jump_to_stage")
        if rollback is not None:
            return rollback
        if jump is not None:
            return jump

        if current == InterviewStage.INTRO:
            return InterviewStage.TECH
        if current == InterviewStage.TECH:
            return InterviewStage.PROJECT
        if current == InterviewStage.PROJECT:
            return InterviewStage.REPORT
        return InterviewStage.REPORT

    def route_after_answer(self, state: InterviewAgentState) -> str:
        if state.get("interrupt"):
            return "finalize_report"
        # 当存在待回答问题且本轮没有输入答案时，停止流程，等待用户提交回答。
        pending_question = state.get("pending_question")
        answer = (state.get("input_answer") or "").strip()
        if pending_question is not None and not answer:
            return "end"
        next_stage = self.next_stage(state)
        if next_stage == InterviewStage.INTRO:
            return "intro_stage"
        if next_stage == InterviewStage.TECH:
            return "tech_stage"
        if next_stage == InterviewStage.PROJECT:
            return "project_stage"
        return "report_stage"

    def route_after_report(self, state: InterviewAgentState) -> str:
        return "end" if state.get("report_ready") else "finalize_report"

    def _build_stage_question(
        self,
        state: InterviewAgentState,
        stage: InterviewStage,
    ) -> InterviewAgentState:
        asked = list(state.get("asked_questions", []))
        asked_signatures = list(state.get("asked_signatures", []))
        history_tags = [tag for item in state.get("history_performance", []) for tag in item.weak_tags]
        question = self.tools.build_question(
            session_id=state["session_id"],
            stage=stage,
            weak_tag_pool=state.get("weak_tag_pool", []),
            resume_skills=state["resume_profile"].skills,
            resume_projects=state["resume_profile"].projects,
            history_weak_tags=history_tags,
            asked_signatures=asked_signatures,
        )
        asked.append(question)
        asked_signatures.append(self.tools.signature_for_question(question))

        logs = list(state.get("stage_logs", []))
        current_stage = state.get("current_stage", stage)
        if stage_order(stage) != stage_order(current_stage):
            logs.append(
                InterviewLifecycleLog(
                    from_stage=current_stage,
                    to_stage=stage,
                    reason=self._transition_reason(state, stage),
                )
            )

        return {
            "current_stage": stage,
            "pending_question": question,
            "asked_questions": asked,
            "asked_signatures": asked_signatures,
            "status": InterviewStatus.RUNNING,
            "stage_logs": logs,
            "jump_to_stage": None,
            "rollback_to_stage": None,
            "interrupt": False,
        }

    @staticmethod
    def _transition_reason(state: InterviewAgentState, next_stage: InterviewStage) -> str:
        if state.get("rollback_to_stage") is not None:
            return "用户触发回溯阶段。"
        if state.get("jump_to_stage") is not None:
            return "用户触发跳转阶段。"
        return f"流程自动推进至 {next_stage.value} 阶段。"
