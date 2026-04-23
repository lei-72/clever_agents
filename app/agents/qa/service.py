"""QA Agent 对外服务封装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.core.config import get_settings
from app.llm import LLMFactory
from app.memory import MemoryService
from app.schemas.qa import (
    FileIngestResponse,
    KnowledgeChunkIn,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    QARequest,
    QAResponse,
)
from app.tools import DocumentParserTool, RAGTool

from .graph import build_qa_graph
from .nodes import AsyncQANodes
from .tools import QAAgentTools


@dataclass(slots=True)
class QAAgentService:
    """QA Agent 运行入口。"""

    graph_app: object
    tools: QAAgentTools
    parser: DocumentParserTool

    @classmethod
    async def create(cls) -> "QAAgentService":
        rag_tool = await RAGTool.from_settings()
        memory_service = MemoryService.from_settings()
        tools = QAAgentTools(rag_tool=rag_tool, memory_service=memory_service)
        nodes = AsyncQANodes(tools=tools, llm_factory=LLMFactory.from_settings())
        graph_app = build_qa_graph(nodes)
        return cls(graph_app=graph_app, tools=tools, parser=DocumentParserTool())

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
        inserted = await self.tools.ingest_chunks(request.chunks)
        settings = get_settings()
        return KnowledgeIngestResponse(inserted=inserted, collection=settings.milvus_collection)

    async def ingest_file(
        self,
        *,
        filename: str,
        content: bytes,
        document_id: str,
        source_uri: str | None = None,
    ) -> FileIngestResponse:
        parsed = self.parser.parse(filename=filename, content=content)
        chunks = self.parser.build_chunks(
            document_id=document_id,
            source_uri=source_uri,
            parsed=parsed,
        )
        inserted = await self.tools.ingest_chunks(chunks)
        settings = get_settings()
        return FileIngestResponse(
            document_id=document_id,
            filename=filename,
            chunk_count=inserted,
            collection=settings.milvus_collection,
        )
