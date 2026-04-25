"""Resume Agent 使用的工具编排。"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.llm import LLMFactory
from app.schemas.resume import (
    ResumeDimension,
    ResumeDimensionScore,
    ResumeReviewIssue,
    ReviewPriority,
)


@dataclass(slots=True)
class ResumeAgentTools:
    llm_factory: LLMFactory

    async def review_dimension_group(
        self,
        *,
        dimensions: list[ResumeDimension],
        resume_text: str,
        target_role: str | None,
        job_description: str | None,
    ) -> tuple[list[ResumeDimensionScore], list[ResumeReviewIssue]]:
        payload = await self._ask_llm_json(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(
                dimensions=dimensions,
                resume_text=resume_text,
                target_role=target_role,
                job_description=job_description,
            ),
        )

        scores = self._parse_dimension_scores(payload.get("dimension_scores", []), dimensions)
        issues = self._parse_issues(payload.get("issues", []), dimensions)
        return scores, issues

    async def _ask_llm_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        content = await self.llm_factory.chat(system_prompt=system_prompt, user_prompt=user_prompt)
        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.strip("`")
            if normalized.startswith("json"):
                normalized = normalized[4:].strip()
        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, dict):
                return dict(parsed)
            return {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "你是资深简历评审专家。请根据指定维度深度诊断简历并输出严格 JSON。"
            "输出必须包含两个字段：dimension_scores 和 issues。"
            "dimension_scores 为数组，每个元素字段：dimension, score(0-100), rationale。"
            "issues 为数组，每个元素字段：dimension, priority(high/medium/low), issue, original_text, suggestion, rewritten_text。"
            "必须提供可执行修改建议，且 original_text 必须是简历中的原文片段。"
            "不要输出 JSON 以外内容。"
        )

    @staticmethod
    def _build_user_prompt(
        *,
        dimensions: list[ResumeDimension],
        resume_text: str,
        target_role: str | None,
        job_description: str | None,
    ) -> str:
        target_role_text = target_role or "未提供"
        job_description_text = job_description or "未提供"
        dimensions_text = ", ".join(item.value for item in dimensions)
        return (
            f"评审维度: {dimensions_text}\n"
            f"目标岗位: {target_role_text}\n"
            f"岗位JD:\n{job_description_text}\n\n"
            f"简历全文:\n{resume_text}\n\n"
            "要求：\n"
            "1) 逐句定位问题并给出改写。\n"
            "2) 按影响程度打 high/medium/low。\n"
            "3) 每个维度至少输出 1 条问题。\n"
            "4) 评分需有简短理由。"
        )

    @staticmethod
    def _parse_dimension_scores(raw: object, dimensions: list[ResumeDimension]) -> list[ResumeDimensionScore]:
        allowed = {item.value for item in dimensions}
        parsed: list[ResumeDimensionScore] = []
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                dimension = str(item.get("dimension", ""))
                if dimension not in allowed:
                    continue
                score = max(min(float(item.get("score", 0.0)), 100.0), 0.0)
                rationale = str(item.get("rationale", "已完成维度评审。")).strip() or "已完成维度评审。"
                parsed.append(
                    ResumeDimensionScore(
                        dimension=ResumeDimension(dimension),
                        score=score,
                        rationale=rationale,
                    )
                )
        if parsed:
            return parsed
        return [
            ResumeDimensionScore(
                dimension=dimension,
                score=60.0,
                rationale="未获取稳定结构化评分，使用保守默认分。",
            )
            for dimension in dimensions
        ]

    @staticmethod
    def _parse_issues(raw: object, dimensions: list[ResumeDimension]) -> list[ResumeReviewIssue]:
        allowed = {item.value for item in dimensions}
        parsed: list[ResumeReviewIssue] = []
        if not isinstance(raw, list):
            return parsed
        for item in raw:
            if not isinstance(item, dict):
                continue
            dimension = str(item.get("dimension", ""))
            if dimension not in allowed:
                continue
            priority = str(item.get("priority", ReviewPriority.MEDIUM.value)).lower()
            if priority not in {ReviewPriority.HIGH.value, ReviewPriority.MEDIUM.value, ReviewPriority.LOW.value}:
                priority = ReviewPriority.MEDIUM.value
            issue = str(item.get("issue", "")).strip()
            original_text = str(item.get("original_text", "")).strip()
            suggestion = str(item.get("suggestion", "")).strip()
            rewritten_text = str(item.get("rewritten_text", "")).strip()
            if not issue or not original_text or not suggestion or not rewritten_text:
                continue
            parsed.append(
                ResumeReviewIssue(
                    dimension=ResumeDimension(dimension),
                    priority=ReviewPriority(priority),
                    issue=issue,
                    original_text=original_text,
                    suggestion=suggestion,
                    rewritten_text=rewritten_text,
                )
            )
        return parsed
