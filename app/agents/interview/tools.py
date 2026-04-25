"""Interview Agent 工具集合。"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from dataclasses import dataclass, field

from app.schemas.interview import (
    InterviewAssessmentPoint,
    InterviewQuestion,
    InterviewRadarChartData,
    InterviewReport,
    InterviewScoreBreakdown,
    InterviewStage,
    InterviewStageScore,
    QuestionSource,
)


def stage_order(stage: InterviewStage) -> int:
    mapping = {
        InterviewStage.INTRO: 0,
        InterviewStage.TECH: 1,
        InterviewStage.PROJECT: 2,
        InterviewStage.REPORT: 3,
    }
    return mapping[stage]


@dataclass(slots=True)
class InterviewAgentTools:
    """负责出题、打分与报告聚合。"""

    report_store: dict[str, InterviewReport] = field(default_factory=dict)
    report_tasks: dict[str, asyncio.Task[InterviewReport]] = field(default_factory=dict)

    def build_question(
        self,
        *,
        session_id: str,
        stage: InterviewStage,
        weak_tag_pool: list[str],
        resume_skills: list[str],
        resume_projects: list[str],
        history_weak_tags: list[str],
        asked_signatures: list[str],
        follow_up_to: str | None = None,
    ) -> InterviewQuestion:
        preferred_tags = history_weak_tags + weak_tag_pool + resume_skills
        seed_tag = next((tag for tag in preferred_tags if tag and tag not in asked_signatures), None)
        if stage == InterviewStage.INTRO:
            content = "请先做 1 分钟自我介绍，并突出与你目标岗位最相关的技术经历。"
            source = QuestionSource.RESUME
            tags = ["self_intro"]
        elif stage == InterviewStage.TECH:
            core = seed_tag or "计算机基础"
            content = f"请深入讲解你在 {core} 上的核心理解，并结合一个故障排查案例说明。"
            source = QuestionSource.WEAKNESS if seed_tag else QuestionSource.GENERAL
            tags = [core]
        elif stage == InterviewStage.PROJECT:
            project = resume_projects[0] if resume_projects else "最近一次关键项目"
            content = f"请复盘项目「{project}」：架构选型、技术难点、性能/稳定性权衡是怎么做的？"
            source = QuestionSource.RESUME
            tags = ["project_review"]
        else:
            content = "请总结本场面试你的优势、短板和下一步提升计划。"
            source = QuestionSource.GENERAL
            tags = ["summary"]

        signature = self._signature(f"{stage.value}|{content}")
        if signature in asked_signatures:
            content = f"{content}（请补充一个之前未提及的细节）"
            signature = self._signature(f"{stage.value}|{content}")

        return InterviewQuestion(
            question_id=f"q-{uuid.uuid4().hex[:10]}",
            stage=stage,
            content=content,
            source=source,
            knowledge_tags=tags,
            difficulty=2 if stage == InterviewStage.INTRO else 3,
            follow_up_to=follow_up_to,
        )

    def signature_for_question(self, question: InterviewQuestion) -> str:
        return self._signature(f"{question.stage.value}|{question.content}")

    def score_turn(
        self,
        *,
        question: InterviewQuestion,
        answer: str,
        weak_tag_pool: list[str],
    ) -> InterviewAssessmentPoint:
        answer_len = len(answer.strip())
        technical = min(100.0, 30.0 + answer_len * 0.5)
        communication = min(100.0, 35.0 + answer_len * 0.45)
        weak_hits = [tag for tag in weak_tag_pool if tag and tag.lower() in answer.lower()]
        if question.stage == InterviewStage.TECH and not weak_hits:
            technical = max(technical - 12.0, 0.0)
        if "我觉得" in answer and "例如" not in answer:
            communication = max(communication - 8.0, 0.0)
        summary = f"{question.stage.value} 阶段完成，技术 {technical:.1f}，表达 {communication:.1f}。"
        return InterviewAssessmentPoint(
            question_id=question.question_id,
            stage=question.stage,
            technical_score=round(technical, 2),
            communication_score=round(communication, 2),
            weak_tags=weak_hits,
            summary=summary,
        )

    def aggregate_stage_scores(self, points: list[InterviewAssessmentPoint]) -> list[InterviewStageScore]:
        result: list[InterviewStageScore] = []
        for stage in (InterviewStage.INTRO, InterviewStage.TECH, InterviewStage.PROJECT, InterviewStage.REPORT):
            items = [item for item in points if item.stage == stage]
            if not items:
                continue
            technical = sum(item.technical_score for item in items) / len(items)
            communication = sum(item.communication_score for item in items) / len(items)
            result.append(
                InterviewStageScore(
                    stage=stage,
                    technical_score=round(technical, 2),
                    communication_score=round(communication, 2),
                )
            )
        return result

    def build_report(self, *, session_id: str, points: list[InterviewAssessmentPoint]) -> InterviewReport:
        stage_scores = self.aggregate_stage_scores(points)
        if not points:
            zero_breakdown = InterviewScoreBreakdown()
            return InterviewReport(
                session_id=session_id,
                overall_score=0.0,
                stage_scores=[],
                technical_breakdown=zero_breakdown,
                communication_breakdown=zero_breakdown,
                radar_chart=InterviewRadarChartData(indicators=[], values=[]),
                weak_points=[],
                highlights=[],
                suggestions=[],
                generated_in_seconds=30,
            )

        avg_tech = sum(item.technical_score for item in points) / len(points)
        avg_comm = sum(item.communication_score for item in points) / len(points)
        overall = round(avg_tech * 0.65 + avg_comm * 0.35, 2)

        technical = InterviewScoreBreakdown(
            technical_depth=round(avg_tech, 2),
            problem_solving=round(min(avg_tech + 3, 100.0), 2),
            system_design=round(max(avg_tech - 2, 0.0), 2),
        )
        communication = InterviewScoreBreakdown(
            communication_clarity=round(avg_comm, 2),
            structure_expression=round(max(avg_comm - 3, 0.0), 2),
            collaboration_signal=round(min(avg_comm + 2, 100.0), 2),
        )
        weak_points = sorted({tag for item in points for tag in item.weak_tags})
        highlights = ["技术回答具备一定细节深度。", "整体表达较连贯。"]
        suggestions = [
            "优先补齐高频薄弱知识点，建立专题化复习清单。",
            "项目复盘时补充量化指标与取舍依据。",
            "回答采用结论先行 + 证据补充的结构。"
        ]
        radar = InterviewRadarChartData(
            indicators=["技术深度", "问题求解", "系统设计", "表达清晰", "结构化表达", "协作信号"],
            values=[
                technical.technical_depth,
                technical.problem_solving,
                technical.system_design,
                communication.communication_clarity,
                communication.structure_expression,
                communication.collaboration_signal,
            ],
            max_value=100.0,
        )
        return InterviewReport(
            session_id=session_id,
            overall_score=overall,
            stage_scores=stage_scores,
            technical_breakdown=technical,
            communication_breakdown=communication,
            radar_chart=radar,
            weak_points=weak_points,
            highlights=highlights,
            suggestions=suggestions,
            generated_in_seconds=30,
        )

    def schedule_report_job(self, *, session_id: str, points: list[InterviewAssessmentPoint]) -> str:
        if session_id in self.report_tasks and not self.report_tasks[session_id].done():
            return session_id

        async def _job() -> InterviewReport:
            await asyncio.sleep(0)
            report = self.build_report(session_id=session_id, points=points)
            self.report_store[session_id] = report
            return report

        task = asyncio.create_task(_job())
        self.report_tasks[session_id] = task
        return session_id

    async def get_report_if_ready(self, session_id: str) -> InterviewReport | None:
        task = self.report_tasks.get(session_id)
        if task is None:
            return self.report_store.get(session_id)
        if task.done():
            return task.result()
        return None

    @staticmethod
    def _signature(value: str) -> str:
        return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]
