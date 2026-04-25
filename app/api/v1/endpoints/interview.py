"""Interview Agent 端点。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.agents import InterviewAgentService
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewReportGenerateResponse,
    InterviewReportQueryResponse,
    InterviewSessionSnapshot,
    InterviewStartRequest,
    InterviewStartResponse,
)

router = APIRouter()
_interview_service: InterviewAgentService | None = None


async def _get_service() -> InterviewAgentService:
    global _interview_service
    if _interview_service is None:
        _interview_service = await InterviewAgentService.create()
    return _interview_service


@router.post("/start", response_model=InterviewStartResponse)
async def start(payload: InterviewStartRequest) -> InterviewStartResponse:
    try:
        service = await _get_service()
        return await service.start(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{session_id}/answer", response_model=InterviewAnswerResponse)
async def answer(session_id: str, payload: InterviewAnswerRequest) -> InterviewAnswerResponse:
    try:
        service = await _get_service()
        return await service.answer(session_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{session_id}", response_model=InterviewSessionSnapshot)
async def get_session(session_id: str) -> InterviewSessionSnapshot:
    try:
        service = await _get_service()
        return service.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{session_id}/report/generate", response_model=InterviewReportGenerateResponse)
async def generate_report(session_id: str) -> InterviewReportGenerateResponse:
    try:
        service = await _get_service()
        return await service.generate_report(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{session_id}/report", response_model=InterviewReportQueryResponse)
async def query_report(session_id: str) -> InterviewReportQueryResponse:
    try:
        service = await _get_service()
        return await service.query_report(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
