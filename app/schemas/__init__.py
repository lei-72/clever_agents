"""Schema 导出集合。"""

from app.schemas.qa import (
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
    "KnowledgeChunkIn",
    "KnowledgeIngestRequest",
    "KnowledgeIngestResponse",
]
"""接口路由共享的数据模型。"""
