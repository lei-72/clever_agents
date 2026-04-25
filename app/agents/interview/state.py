"""Interview Agent 状态定义。"""

from __future__ import annotations

from typing import TypedDict

from app.schemas.interview import (
    InterviewAnswerTurn,
    InterviewAssessmentPoint,
    InterviewLifecycleLog,
    InterviewPerformanceRecord,
    InterviewQuestion,
    InterviewReport,
    InterviewResumeProfile,
    InterviewStage,
    InterviewStageScore,
    InterviewStatus,
)


class InterviewAgentState(TypedDict, total=False):
    session_id: str
    candidate_id: str
    status: InterviewStatus
    current_stage: InterviewStage
    resume_profile: InterviewResumeProfile
    history_performance: list[InterviewPerformanceRecord]
    weak_tag_pool: list[str]
    asked_signatures: list[str]
    asked_questions: list[InterviewQuestion]
    pending_question: InterviewQuestion | None
    qna_turns: list[InterviewAnswerTurn]
    follow_up_chain: dict[str, list[str]]
    weak_tag_marks: list[str]
    assessment_points: list[InterviewAssessmentPoint]
    stage_logs: list[InterviewLifecycleLog]
    stage_scores: list[InterviewStageScore]
    report_ready: bool
    report: InterviewReport | None
    async_report_job_id: str | None
    input_answer: str | None
    jump_to_stage: InterviewStage | None
    rollback_to_stage: InterviewStage | None
    interrupt: bool
