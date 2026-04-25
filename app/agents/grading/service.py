"""Grading Agent 对外服务封装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.llm import LLMFactory
from app.schemas.grading import (
    GradingRequest,
    GradingResponse,
    LearningAnalysisReport,
    TeacherReviewItem,
    TeacherReviewPublishRequest,
)

from .graph import build_grading_graph
from .nodes import AsyncGradingNodes
from .tools import GradingAgentTools


@dataclass(slots=True)
class GradingAgentService:
    """Grading Agent 运行入口。"""

    graph_app: object

    @classmethod
    async def create(cls) -> "GradingAgentService":
        tools = GradingAgentTools(llm_factory=LLMFactory.from_settings())
        nodes = AsyncGradingNodes(tools=tools)
        graph_app = build_grading_graph(nodes)
        return cls(graph_app=graph_app)

    async def run(self, request: GradingRequest) -> GradingResponse:
        trace_id = uuid.uuid4().hex
        state = await self.graph_app.ainvoke(
            {
                "trace_id": trace_id,
                "exam_id": request.exam_id,
                "student_id": request.student_id,
                "teacher_id": request.teacher_id,
                "questions": request.questions,
            }
        )
        return GradingResponse(
            exam_id=request.exam_id,
            student_id=request.student_id,
            total_score=state.get("total_score", 0.0),
            full_score=state.get("full_score", 0.0),
            reviewed=False,
            question_results=state.get("question_results", []),
            teacher_review_items=state.get("teacher_review_items", []),
            analysis_report=LearningAnalysisReport(
                wrong_reason_summary=state.get("wrong_reason_summary", []),
                weak_knowledge_points=state.get("weak_knowledge_points", []),
                answering_shortcomings=state.get("answering_shortcomings", []),
                optimization_suggestions=state.get("optimization_suggestions", []),
            ),
            trace_id=trace_id,
        )

    async def review_and_publish(self, request: TeacherReviewPublishRequest) -> GradingResponse:
        result = request.grading_result.model_copy(deep=True)
        override_map = {item.question_id: item for item in request.overrides}

        question_map = {item.question_id: item for item in result.question_results}
        new_review_items: list[TeacherReviewItem] = []
        total_score = 0.0
        for item in result.teacher_review_items:
            override = override_map.get(item.question_id)
            final_score = item.ai_score if override is None else override.final_score
            modified = override is not None and final_score != item.ai_score
            teacher_comment = None if override is None else override.teacher_comment
            review_item = TeacherReviewItem(
                question_id=item.question_id,
                ai_score=item.ai_score,
                final_score=final_score,
                modified_by_teacher=modified,
                teacher_comment=teacher_comment,
            )
            new_review_items.append(review_item)
            if item.question_id in question_map:
                question_map[item.question_id].score = final_score
            total_score += final_score

        result.teacher_review_items = new_review_items
        result.total_score = total_score
        result.reviewed = True
        return result
