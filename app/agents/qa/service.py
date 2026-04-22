"""QA Agent 对外服务封装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.core.config import get_settings
from app.llm import LLMFactory
from app.memory import MemoryService
from app.schemas.qa import (
    KnowledgeChunkIn,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    QARequest,
    QAResponse,
)
from app.tools import RAGTool

from .graph import build_qa_graph
from .nodes import AsyncQANodes
from .tools import QAAgentTools


@dataclass(slots=True)
class QAAgentService:
    """QA Agent 运行入口。"""

    graph_app: object
    tools: QAAgentTools

    @classmethod
    async def create(cls) -> "QAAgentService":
        rag_tool = await RAGTool.from_settings()
        memory_service = MemoryService.from_settings()
        tools = QAAgentTools(rag_tool=rag_tool, memory_service=memory_service)
        nodes = AsyncQANodes(tools=tools, llm_factory=LLMFactory.from_settings())
        graph_app = build_qa_graph(nodes)
        return cls(graph_app=graph_app, tools=tools)

    async def run(self, request: QARequest) -> QAResponse:
        settings = get_settings()
        trace_id = uuid.uuid4().hex
        state = await self.graph_app.ainvoke(
            {
                "trace_id": trace_id,
                "query": request.query,
                "session_id": request.session_id,
                "user_id": request.user_id,
                "top_k": request.top_k or settings.qa_top_k,
                "rerank_k": settings.qa_rerank_k,
            }
        )
        return QAResponse(
            answer=state["answer"],
            confidence=state["confidence"],
            should_escalate=state["should_escalate"],
            sources=state.get("retrieved_sources", []),
            trace_id=trace_id,
        )

    async def ingest_knowledge(self, request: KnowledgeIngestRequest) -> KnowledgeIngestResponse:
        inserted = await self.tools.ingest_chunks([KnowledgeChunkIn(**item.model_dump()) for item in request.chunks])
        settings = get_settings()
        return KnowledgeIngestResponse(inserted=inserted, collection=settings.milvus_collection)
