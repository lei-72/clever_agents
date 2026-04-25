"""Orchestrator Phase 3 MVP 路由端点。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.agents import GradingAgentService, InterviewAgentService, QAAgentService, ResumeAgentService
from app.core.config import get_settings
from app.orchestrator import OrchestratorService
from app.schemas.orchestrator import (
    OrchestratorExecuteRequest,
    OrchestratorExecuteResponse,
    OrchestratorPipelineRequest,
    OrchestratorPipelineResponse,
    OrchestratorRequest,
    OrchestratorRouteResponse,
)

router = APIRouter()
_qa_service: QAAgentService | None = None
_grading_service: GradingAgentService | None = None
_interview_service: InterviewAgentService | None = None
_resume_service: ResumeAgentService | None = None


async def _get_qa_service() -> QAAgentService:
    global _qa_service
    if _qa_service is None:
        _qa_service = await QAAgentService.create()
    return _qa_service


async def _get_grading_service() -> GradingAgentService:
    global _grading_service
    if _grading_service is None:
        _grading_service = await GradingAgentService.create()
    return _grading_service


async def _get_interview_service() -> InterviewAgentService:
    global _interview_service
    if _interview_service is None:
        _interview_service = await InterviewAgentService.create()
    return _interview_service


async def _get_resume_service() -> ResumeAgentService:
    global _resume_service
    if _resume_service is None:
        _resume_service = await ResumeAgentService.create()
    return _resume_service


@router.post("/route", response_model=OrchestratorRouteResponse)
async def route_request(payload: OrchestratorRequest) -> OrchestratorRouteResponse:
    """返回编排层的同步路由结果。"""

    service = OrchestratorService()
    route = service.route(payload)
    return OrchestratorRouteResponse(route=route)


@router.post("/stream")
async def stream_route(payload: OrchestratorRequest) -> StreamingResponse:
    """基于统一 SSE 协议返回流式路由事件。

    协议要点：
    - Content-Type: text/event-stream
    - 事件顺序: route -> delta -> done
    """

    service = OrchestratorService()
    return StreamingResponse(
        service.stream_route_events(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/execute", response_model=OrchestratorExecuteResponse)
async def execute(payload: OrchestratorExecuteRequest) -> OrchestratorExecuteResponse:
    """执行编排后的目标 Agent（当前支持 QA Agent）。"""

    qa_service = await _get_qa_service()
    grading_service = await _get_grading_service()
    interview_service = await _get_interview_service()
    service = OrchestratorService(
        qa_executor=qa_service.run,
        grading_executor=grading_service.run,
        interview_executor=interview_service.start,
    )
    return await service.execute(payload)


@router.post("/pipeline/execute", response_model=OrchestratorPipelineResponse)
async def execute_pipeline(payload: OrchestratorPipelineRequest) -> OrchestratorPipelineResponse:
    """执行多 Agent 业务流水线（拆解、串联、聚合、追踪）。"""

    settings = get_settings()
    if not settings.enable_multi_agent_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-agent pipeline is disabled for performance. Use /orchestrator/execute or single agent endpoints.",
        )

    qa_service = await _get_qa_service()
    grading_service = await _get_grading_service()
    interview_service = await _get_interview_service()
    resume_service = await _get_resume_service()
    service = OrchestratorService(
        qa_executor=qa_service.run,
        grading_executor=grading_service.run,
        interview_executor=interview_service.start,
        resume_executor=resume_service.run,
    )
    return await service.execute_pipeline(payload)
