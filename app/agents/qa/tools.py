"""QA Agent 使用的工具编排。"""

from __future__ import annotations

from dataclasses import dataclass

from app.memory import MemoryService
from app.schemas.qa import KnowledgeChunkIn, QASource
from app.tools import RAGTool


@dataclass(slots=True)
class QAAgentTools:
    rag_tool: RAGTool
    memory_service: MemoryService

    async def ingest_chunks(self, chunks: list[KnowledgeChunkIn]) -> int:
        return await self.rag_tool.ingest(chunks)

    async def retrieve(self, query: str, top_k: int, rerank_k: int) -> list[QASource]:
        return await self.rag_tool.retrieve_hybrid(query=query, top_k=top_k, rerank_k=rerank_k)
