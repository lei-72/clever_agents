"""Grading Agent 状态定义。"""

from __future__ import annotations

from typing import TypedDict

from app.schemas.grading import (
    GradingQuestion,
    GradingQuestionResult,
    TeacherReviewItem,
    WeakKnowledgePoint,
)


class GradingAgentState(TypedDict, total=False):
    trace_id: str
    exam_id: str
    student_id: str
    teacher_id: str | None
    questions: list[GradingQuestion]
    question_results: list[GradingQuestionResult]
    teacher_review_items: list[TeacherReviewItem]
    wrong_reason_summary: list[str]
    weak_knowledge_points: list[WeakKnowledgePoint]
    answering_shortcomings: list[str]
    optimization_suggestions: list[str]
    total_score: float
    full_score: float
