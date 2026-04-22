"""QA Agent 请求与响应模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QASource(BaseModel):
    """回答引用来源。"""

    document_id: str = Field(..., description="文档唯一标识。")
    chunk_id: str = Field(..., description="分块唯一标识。")
    title: str = Field(..., description="文档标题。")
    content: str = Field(..., description="命中分块内容。")
    source_uri: str | None = Field(default=None, description="来源地址。")
    score: float = Field(..., ge=0.0, le=1.0, description="最终重排分数。")


class QARequest(BaseModel):
    """QA 查询请求。"""

    query: str = Field(..., min_length=1, description="用户问题。")
    session_id: str = Field(..., min_length=1, description="会话标识。")
    user_id: str | None = Field(default=None, description="用户标识。")
    top_k: int | None = Field(default=None, ge=1, le=20, description="召回候选数量。")


class QAResponse(BaseModel):
    """QA 结构化响应。"""

    answer: str = Field(..., description="回答正文。")
    confidence: float = Field(..., ge=0.0, le=1.0, description="回答置信度。")
    should_escalate: bool = Field(..., description="是否需要进入知识补充队列。")
    sources: list[QASource] = Field(default_factory=list, description="可追溯来源列表。")
    trace_id: str = Field(..., description="请求追踪标识。")


class KnowledgeChunkIn(BaseModel):
    """入库知识分块。"""

    document_id: str = Field(..., min_length=1)
    chunk_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source_uri: str | None = None


class KnowledgeIngestRequest(BaseModel):
    """知识入库请求。"""

    chunks: list[KnowledgeChunkIn] = Field(..., min_length=1)


class KnowledgeIngestResponse(BaseModel):
    """知识入库响应。"""

    inserted: int = Field(..., ge=0)
    collection: str
