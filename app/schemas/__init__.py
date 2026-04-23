"""Schema 导出集合。"""

from app.schemas.qa import (
    FileIngestResponse,
    KnowledgeChunkIn,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    QARequest,
    QAResponse,
    QASource,
)

__all__ = [
    "QARequest",
    "QAResponse",
    "QASource",
    "FileIngestResponse",
    "KnowledgeChunkIn",
    "KnowledgeIngestRequest",
    "KnowledgeIngestResponse",
]
"""接口路由共享的数据模型。"""
