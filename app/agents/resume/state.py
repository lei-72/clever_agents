"""Resume Agent 状态定义。"""

from __future__ import annotations

from typing import TypedDict

from app.schemas.resume import ResumeDimensionScore, ResumeReviewIssue


class ResumeAgentState(TypedDict, total=False):
    trace_id: str
    resume_text: str
    target_role: str | None
    job_description: str | None
    group_a_scores: list[ResumeDimensionScore]
    group_a_issues: list[ResumeReviewIssue]
    group_b_scores: list[ResumeDimensionScore]
    group_b_issues: list[ResumeReviewIssue]
    group_c_scores: list[ResumeDimensionScore]
    group_c_issues: list[ResumeReviewIssue]
    dimension_scores: list[ResumeDimensionScore]
    all_issues: list[ResumeReviewIssue]
    high_priority_issues: list[ResumeReviewIssue]
    medium_priority_issues: list[ResumeReviewIssue]
    low_priority_issues: list[ResumeReviewIssue]
    overall_score: float
