"""Resume Agent 节点函数（纯函数风格）。"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.resume import ResumeDimension, ResumeReviewIssue, ReviewPriority

from .state import ResumeAgentState
from .tools import ResumeAgentTools


@dataclass(slots=True)
class AsyncResumeNodes:
    """异步节点集合。"""

    tools: ResumeAgentTools

    async def review_group_a(self, state: ResumeAgentState) -> ResumeAgentState:
        dimensions = [ResumeDimension.WORK_EXPERIENCE, ResumeDimension.SKILL_MATCHING]
        scores, issues = await self.tools.review_dimension_group(
            dimensions=dimensions,
            resume_text=state["resume_text"],
            target_role=state.get("target_role"),
            job_description=state.get("job_description"),
        )
        return {"group_a_scores": scores, "group_a_issues": issues}

    async def review_group_b(self, state: ResumeAgentState) -> ResumeAgentState:
        dimensions = [ResumeDimension.PROJECT_DESCRIPTION, ResumeDimension.QUANTITATIVE_DATA]
        scores, issues = await self.tools.review_dimension_group(
            dimensions=dimensions,
            resume_text=state["resume_text"],
            target_role=state.get("target_role"),
            job_description=state.get("job_description"),
        )
        return {"group_b_scores": scores, "group_b_issues": issues}

    async def review_group_c(self, state: ResumeAgentState) -> ResumeAgentState:
        dimensions = [ResumeDimension.FORMATTING_LAYOUT, ResumeDimension.LANGUAGE_EXPRESSION]
        scores, issues = await self.tools.review_dimension_group(
            dimensions=dimensions,
            resume_text=state["resume_text"],
            target_role=state.get("target_role"),
            job_description=state.get("job_description"),
        )
        return {"group_c_scores": scores, "group_c_issues": issues}

    async def merge_report(self, state: ResumeAgentState) -> ResumeAgentState:
        dimension_scores = (
            state.get("group_a_scores", [])
            + state.get("group_b_scores", [])
            + state.get("group_c_scores", [])
        )
        all_issues: list[ResumeReviewIssue] = (
            state.get("group_a_issues", [])
            + state.get("group_b_issues", [])
            + state.get("group_c_issues", [])
        )
        high_issues = [item for item in all_issues if item.priority == ReviewPriority.HIGH]
        medium_issues = [item for item in all_issues if item.priority == ReviewPriority.MEDIUM]
        low_issues = [item for item in all_issues if item.priority == ReviewPriority.LOW]
        overall_score = (
            sum(item.score for item in dimension_scores) / len(dimension_scores)
            if dimension_scores
            else 0.0
        )
        return {
            "dimension_scores": dimension_scores,
            "all_issues": all_issues,
            "high_priority_issues": high_issues,
            "medium_priority_issues": medium_issues,
            "low_priority_issues": low_issues,
            "overall_score": round(overall_score, 2),
        }
