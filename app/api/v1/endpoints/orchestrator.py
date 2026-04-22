"""Orchestrator Phase 3 MVP 路由端点。"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents import QAAgentService
from app.orchestrator import OrchestratorService
from app.schemas.orchestrator import (
    OrchestratorExecuteResponse,
    OrchestratorRequest,
    OrchestratorRouteResponse,
)

router = APIRouter()
_qa_service: QAAgentService | None = None


async def _get_qa_service() -> QAAgentService:
    global _qa_service
    if _qa_service is None:
        _qa_service = await QAAgentService.create()
    return _qa_service


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
async def execute(payload: OrchestratorRequest) -> OrchestratorExecuteResponse:
    """执行编排后的目标 Agent（当前支持 QA Agent）。"""

    qa_service = await _get_qa_service()
    service = OrchestratorService(qa_executor=qa_service.run)
    return await service.execute(payload)
