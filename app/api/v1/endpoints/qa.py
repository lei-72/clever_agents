"""QA Agent 端点。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.agents import QAAgentService
from app.schemas.qa import KnowledgeIngestRequest, KnowledgeIngestResponse, QARequest, QAResponse

router = APIRouter()
_qa_service: QAAgentService | None = None


async def _get_service() -> QAAgentService:
    global _qa_service
    if _qa_service is None:
        _qa_service = await QAAgentService.create()
    return _qa_service


@router.post("/ask", response_model=QAResponse)
async def ask(payload: QARequest) -> QAResponse:
    try:
        service = await _get_service()
        return await service.run(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QA agent failed: {exc}",
        ) from exc


@router.post("/ingest", response_model=KnowledgeIngestResponse)
async def ingest(payload: KnowledgeIngestRequest) -> KnowledgeIngestResponse:
    try:
        service = await _get_service()
        return await service.ingest_knowledge(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge ingest failed: {exc}",
        ) from exc
