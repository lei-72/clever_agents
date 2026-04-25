"""Grading Agent 节点函数（纯函数风格）。"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.grading import (
    GradingQuestionResult,
    GradingSuggestion,
    QuestionType,
    TeacherReviewItem,
    WeakKnowledgePoint,
)

from .state import GradingAgentState
from .tools import GradingAgentTools


@dataclass(slots=True)
class AsyncGradingNodes:
    """异步节点集合。"""

    tools: GradingAgentTools

    async def grade_questions(self, state: GradingAgentState) -> GradingAgentState:
        results: list[GradingQuestionResult] = []
        for question in state["questions"]:
            if question.question_type == QuestionType.OBJECTIVE:
                result = self.tools.grade_objective(question)
            elif question.question_type == QuestionType.SUBJECTIVE:
                result = await self.tools.grade_subjective(question)
            else:
                result = await self.tools.grade_coding(question)
            results.append(result)
        return {"question_results": results}

    async def build_teacher_review(self, state: GradingAgentState) -> GradingAgentState:
        review_items = [
            TeacherReviewItem(
                question_id=item.question_id,
                ai_score=item.score,
                final_score=item.score,
                modified_by_teacher=False,
                teacher_comment=None,
            )
            for item in state.get("question_results", [])
        ]
        return {"teacher_review_items": review_items}

    async def build_learning_analysis(self, state: GradingAgentState) -> GradingAgentState:
        question_map = {question.question_id: question for question in state["questions"]}
        wrong_reasons: list[str] = []
        weaknesses: dict[str, WeakKnowledgePoint] = {}
        shortcomings: list[str] = []
        optimization: list[str] = []

        for result in state.get("question_results", []):
            question = question_map.get(result.question_id)
            if question is None:
                continue
            if result.score >= question.max_score:
                continue

            wrong_reasons.append(f"{result.question_id}: {result.rationale}")
            shortcomings.extend(result.missed_points)
            for suggestion in result.suggestions:
                optimization.append(self._format_suggestion(suggestion))
            for tag in question.knowledge_tags:
                current = weaknesses.get(tag)
                if current is None:
                    weaknesses[tag] = WeakKnowledgePoint(tag=tag, wrong_count=1, impact_score=question.max_score - result.score)
                else:
                    current.wrong_count += 1
                    current.impact_score += question.max_score - result.score

        weak_points = sorted(weaknesses.values(), key=lambda item: item.impact_score, reverse=True)
        return {
            "wrong_reason_summary": wrong_reasons,
            "weak_knowledge_points": weak_points,
            "answering_shortcomings": list(dict.fromkeys(shortcomings)),
            "optimization_suggestions": list(dict.fromkeys(optimization)),
        }

    async def finalize_totals(self, state: GradingAgentState) -> GradingAgentState:
        total_score = sum(item.score for item in state.get("question_results", []))
        full_score = sum(question.max_score for question in state["questions"])
        return {"total_score": total_score, "full_score": full_score}

    @staticmethod
    def _format_suggestion(suggestion: GradingSuggestion) -> str:
        return f"{suggestion.type}: {suggestion.content}"
