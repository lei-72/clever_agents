"""Orchestrator Phase 3 MVP 路由端点。"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.orchestrator import OrchestratorService
from app.schemas.orchestrator import (
    OrchestratorRequest,
    OrchestratorRouteResponse,
)

router = APIRouter()
# PHASE3-MVP: 服务实例当前为无状态，可直接模块级复用。
service = OrchestratorService()


@router.post("/route", response_model=OrchestratorRouteResponse)
async def route_request(payload: OrchestratorRequest) -> OrchestratorRouteResponse:
    """返回编排层的同步路由结果。"""

    route = service.route(payload)
    return OrchestratorRouteResponse(route=route)


@router.post("/stream")
async def stream_route(payload: OrchestratorRequest) -> StreamingResponse:
    """基于统一 SSE 协议返回流式路由事件。

    协议要点：
    - Content-Type: text/event-stream
    - 事件顺序: route -> delta -> done
    """

    return StreamingResponse(
        service.stream_route_events(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
