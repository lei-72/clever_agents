"""Resume Agent 端点。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.agents import ResumeAgentService
from app.schemas.resume import ResumeReviewRequest, ResumeReviewResponse

router = APIRouter()
_resume_service: ResumeAgentService | None = None


async def _get_service() -> ResumeAgentService:
    global _resume_service
    if _resume_service is None:
        _resume_service = await ResumeAgentService.create()
    return _resume_service


@router.post("/review", response_model=ResumeReviewResponse)
async def review(payload: ResumeReviewRequest) -> ResumeReviewResponse:
    try:
        service = await _get_service()
        return await service.run(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resume review request invalid: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume agent failed: {exc}",
        ) from exc
