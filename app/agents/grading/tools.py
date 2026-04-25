"""Grading Agent 使用的工具编排。"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.llm import LLMFactory
from app.schemas.grading import (
    CodingRubric,
    GradingQuestion,
    GradingQuestionResult,
    GradingSuggestion,
    SubjectiveRubricPoint,
)


@dataclass(slots=True)
class GradingAgentTools:
    llm_factory: LLMFactory

    def grade_objective(self, question: GradingQuestion) -> GradingQuestionResult:
        rule = question.objective_rule
        if rule is None:
            raise ValueError("objective_rule is required for objective question.")

        expected = rule.expected_answer
        actual = question.student_answer
        if rule.trim_whitespace:
            expected = expected.strip()
            actual = actual.strip()
        if rule.ignore_case:
            expected = expected.lower()
            actual = actual.lower()

        is_correct = expected == actual
        score = question.max_score if is_correct else 0.0
        rationale = "答案与标准答案一致。" if is_correct else "答案与标准答案不一致。"
        suggestions = [] if is_correct else [GradingSuggestion(type="knowledge", content="复习该题对应知识点。")]
        return GradingQuestionResult(
            question_id=question.question_id,
            question_type=question.question_type,
            score=score,
            is_correct=is_correct,
            rationale=rationale,
            suggestions=suggestions,
        )

    async def grade_subjective(self, question: GradingQuestion) -> GradingQuestionResult:
        rubric = question.subjective_rubric
        if not rubric:
            raise ValueError("subjective_rubric is required for subjective question.")

        system_prompt = (
            "你是严格的阅卷老师。请根据给定采分点对学生答案进行评分。"
            "必须返回 JSON，包含: matched_keys(list[str]), missed_keys(list[str]), rationale(str), score(float)。"
            "score 不能超过 max_score。"
        )
        user_prompt = (
            f"题干:\n{question.stem}\n\n"
            f"学生答案:\n{question.student_answer}\n\n"
            f"max_score: {question.max_score}\n"
            f"采分点(JSON):\n{self._rubric_points_json(rubric)}"
        )
        result = await self._ask_llm_json(system_prompt=system_prompt, user_prompt=user_prompt)
        matched_keys = [str(key) for key in result.get("matched_keys", [])]
        missed_keys = [str(key) for key in result.get("missed_keys", [])]
        rationale = str(result.get("rationale", "已按采分点评分。"))
        score = max(min(float(result.get("score", 0.0)), question.max_score), 0.0)

        score_map = {point.key: point.score for point in rubric}
        matched_points = [point.description for point in rubric if point.key in matched_keys]
        missed_points = [point.description for point in rubric if point.key in missed_keys]
        if not matched_keys:
            score = 0.0
        elif score == 0.0:
            score = min(sum(score_map.get(key, 0.0) for key in matched_keys), question.max_score)

        return GradingQuestionResult(
            question_id=question.question_id,
            question_type=question.question_type,
            score=score,
            rationale=rationale,
            matched_points=matched_points,
            missed_points=missed_points,
            suggestions=self._build_subjective_suggestions(missed_points),
        )

    async def grade_coding(self, question: GradingQuestion) -> GradingQuestionResult:
        rubric = question.coding_rubric or CodingRubric()
        system_prompt = (
            "你是编程题阅卷助手。请判断学生代码是否满足需求并给出分数。"
            "必须返回 JSON，包含: passed(bool), rationale(str), score(float), suggestions(list[str])。"
            "score 不能超过 max_score。"
        )
        user_prompt = (
            f"题干:\n{question.stem}\n\n"
            f"学生代码:\n{question.student_answer}\n\n"
            f"max_score: {question.max_score}\n"
            f"requirements: {json.dumps(rubric.requirements, ensure_ascii=False)}\n"
            f"test_cases: {json.dumps(rubric.test_cases, ensure_ascii=False)}"
        )
        result = await self._ask_llm_json(system_prompt=system_prompt, user_prompt=user_prompt)
        passed = bool(result.get("passed", False))
        score = max(min(float(result.get("score", 0.0)), question.max_score), 0.0)
        if passed and score == 0.0:
            score = question.max_score
        rationale = str(result.get("rationale", "已完成代码语义判读。"))
        suggestions = [
            GradingSuggestion(type="coding", content=str(item))
            for item in result.get("suggestions", [])
        ]
        if not suggestions and not passed:
            suggestions = [GradingSuggestion(type="coding", content="补充边界条件与异常处理。")]
        return GradingQuestionResult(
            question_id=question.question_id,
            question_type=question.question_type,
            score=score,
            rationale=rationale,
            suggestions=suggestions,
        )

    async def _ask_llm_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        content = await self.llm_factory.chat(system_prompt=system_prompt, user_prompt=user_prompt)
        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.strip("`")
            if normalized.startswith("json"):
                normalized = normalized[4:].strip()
        try:
            return dict(json.loads(normalized))
        except json.JSONDecodeError:
            return {"rationale": content, "score": 0.0}

    @staticmethod
    def _rubric_points_json(points: list[SubjectiveRubricPoint]) -> str:
        payload = [
            {"key": point.key, "description": point.description, "score": point.score}
            for point in points
        ]
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _build_subjective_suggestions(missed_points: list[str]) -> list[GradingSuggestion]:
        return [GradingSuggestion(type="subjective", content=f"补充要点：{item}") for item in missed_points]
