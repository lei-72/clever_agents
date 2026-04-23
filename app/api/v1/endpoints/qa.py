"""QA Agent 端点。"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.agents import QAAgentService
from app.schemas.qa import (
    FileIngestResponse,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    QARequest,
    QAResponse,
)

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

"""上传单个知识分块"""
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


"""上传文件并自动解析切块后入库。"""
@router.post("/ingest-file", response_model=FileIngestResponse)
@router.post("/ingest-file/", response_model=FileIngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    document_id: str = Form(...),
    source_uri: str | None = Form(default=None),
) -> FileIngestResponse:
    """上传文件并自动解析切块后入库。

    支持文件类型：txt / md / pdf / docx
    """

    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="filename is required.",
            )
        service = await _get_service()
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file content is empty.",
            )
        return await service.ingest_file(
            filename=file.filename,
            content=content,
            document_id=document_id,
            source_uri=source_uri,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File ingest failed: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File ingest failed: {exc}",
        ) from exc
