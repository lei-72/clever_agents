"""Resume Agent 对外服务封装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.llm import LLMFactory
from app.schemas.resume import (
    ResumeRadarChartData,
    ResumeRadarMetric,
    ResumeReviewRequest,
    ResumeReviewResponse,
)

from .graph import build_resume_graph
from .nodes import AsyncResumeNodes
from .tools import ResumeAgentTools


@dataclass(slots=True)
class ResumeAgentService:
    """Resume Agent 运行入口。"""

    graph_app: object

    @classmethod
    async def create(cls) -> "ResumeAgentService":
        tools = ResumeAgentTools(llm_factory=LLMFactory.from_settings())
        nodes = AsyncResumeNodes(tools=tools)
        graph_app = build_resume_graph(nodes)
        return cls(graph_app=graph_app)

    async def run(self, request: ResumeReviewRequest) -> ResumeReviewResponse:
        trace_id = uuid.uuid4().hex
        state = await self.graph_app.ainvoke(
            {
                "trace_id": trace_id,
                "resume_text": request.resume_text,
                "target_role": request.target_role,
                "job_description": request.job_description,
            }
        )

        dimension_scores = state.get("dimension_scores", [])
        radar_metrics = [
            ResumeRadarMetric(dimension=item.dimension, score=item.score)
            for item in dimension_scores
        ]
        radar_chart = ResumeRadarChartData(
            indicators=[item.dimension.value for item in radar_metrics],
            values=[item.score for item in radar_metrics],
            max_value=100.0,
        )
        return ResumeReviewResponse(
            overall_score=state.get("overall_score", 0.0),
            dimension_scores=dimension_scores,
            high_priority_issues=state.get("high_priority_issues", []),
            medium_priority_issues=state.get("medium_priority_issues", []),
            low_priority_issues=state.get("low_priority_issues", []),
            radar_metrics=radar_metrics,
            radar_chart=radar_chart,
            trace_id=trace_id,
        )
