"""Grading Agent 端点。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.agents import GradingAgentService
from app.schemas.grading import GradingRequest, GradingResponse, TeacherReviewPublishRequest

router = APIRouter()
_grading_service: GradingAgentService | None = None


async def _get_service() -> GradingAgentService:
    global _grading_service
    if _grading_service is None:
        _grading_service = await GradingAgentService.create()
    return _grading_service


@router.post("/grade", response_model=GradingResponse)
async def grade(payload: GradingRequest) -> GradingResponse:
    try:
        service = await _get_service()
        return await service.run(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grading request invalid: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grading agent failed: {exc}",
        ) from exc


@router.post("/review-publish", response_model=GradingResponse)
async def review_publish(payload: TeacherReviewPublishRequest) -> GradingResponse:
    try:
        service = await _get_service()
        return await service.review_and_publish(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Review request invalid: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review publish failed: {exc}",
        ) from exc
