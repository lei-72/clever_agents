"""QA Agent 对外服务封装。"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import AsyncIterator

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

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class QAAgentService:
    """QA Agent 运行入口。"""

    graph_app: object
    tools: QAAgentTools
    parser: DocumentParserTool
    llm_factory: LLMFactory

    @classmethod
    async def create(cls) -> "QAAgentService":
        rag_tool = await RAGTool.from_settings()
        memory_service = MemoryService.from_settings()
        tools = QAAgentTools(rag_tool=rag_tool, memory_service=memory_service)
        llm_factory = LLMFactory.from_settings()
        nodes = AsyncQANodes(tools=tools, llm_factory=llm_factory)
        graph_app = build_qa_graph(nodes)
        return cls(graph_app=graph_app, tools=tools, parser=DocumentParserTool(), llm_factory=llm_factory)

    async def run(self, request: QARequest) -> QAResponse:
        settings = get_settings()
        trace_id = uuid.uuid4().hex
        try:
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
        except Exception as exc:  # noqa: BLE001
            logger.exception("QA run failed, fallback response returned. trace_id=%s", trace_id)
            return QAResponse(
                answer=(
                    "当前问答服务暂时不可用，请稍后重试。"
                    "我们已记录该问题并进入排查。"
                ),
                confidence=0.0,
                should_escalate=True,
                sources=[],
                trace_id=trace_id,
            )

    async def stream_run(self, request: QARequest) -> AsyncIterator[str]:
        """以 SSE 方式返回 QA 结果，直接透传上游模型流。"""
        settings = get_settings()
        trace_id = uuid.uuid4().hex
        top_k = request.top_k or settings.qa_top_k
        rerank_k = settings.qa_rerank_k

        try:
            yield self._format_sse("progress", {"message": "正在理解问题..."})
            history = await self.tools.memory_service.get_history(request.session_id)

            yield self._format_sse("progress", {"message": "正在检索知识库..."})
            sources = await self.tools.retrieve(query=request.query, top_k=top_k, rerank_k=rerank_k)
            confidence, should_escalate = self._evaluate_confidence(sources)

            if not sources:
                answer = "当前知识库没有检索到可用内容。请换个问法，或先上传相关资料后再提问。"
                yield self._format_sse("delta", {"content": answer})
                await self.tools.memory_service.append_turn(request.session_id, "user", request.query)
                await self.tools.memory_service.append_turn(request.session_id, "assistant", answer)
                yield self._format_sse(
                    "meta",
                    {
                        "confidence": confidence,
                        "should_escalate": True,
                        "sources": [],
                        "trace_id": trace_id,
                    },
                )
                yield self._format_sse("done", {"status": "completed"})
                return

            system_prompt, user_prompt = self._build_prompts(
                query=request.query,
                history=history,
                sources=sources[:3],
            )
            yield self._format_sse("progress", {"message": "正在生成回答..."})

            answer_parts: list[str] = []
            async for token in self.llm_factory.chat_stream(system_prompt=system_prompt, user_prompt=user_prompt):
                answer_parts.append(token)
                yield self._format_sse("delta", {"content": token})

            answer = "".join(answer_parts).strip()
            if not answer:
                answer = "本次未生成有效回答，请稍后再试。"
                should_escalate = True
                confidence = 0.0

            await self.tools.memory_service.append_turn(request.session_id, "user", request.query)
            await self.tools.memory_service.append_turn(request.session_id, "assistant", answer)

            yield self._format_sse(
                "meta",
                {
                    "confidence": confidence,
                    "should_escalate": should_escalate,
                    "sources": [item.model_dump() for item in sources],
                    "trace_id": trace_id,
                },
            )
            yield self._format_sse("done", {"status": "completed"})
        except Exception as exc:  # noqa: BLE001
            logger.exception("QA stream failed. trace_id=%s", trace_id)
            yield self._format_sse("error", {"message": f"流式问答失败: {type(exc).__name__}"})
            yield self._format_sse(
                "meta",
                {
                    "confidence": 0.0,
                    "should_escalate": True,
                    "sources": [],
                    "trace_id": trace_id,
                },
            )
            yield self._format_sse("done", {"status": "failed"})

    @staticmethod
    def _format_sse(event: str, data: dict[str, object]) -> str:
        payload = json.dumps({"event": event, "data": data}, ensure_ascii=False)
        return f"event: {event}\ndata: {payload}\n\n"

    @staticmethod
    def _evaluate_confidence(sources: list) -> tuple[float, bool]:
        if not sources:
            return 0.0, True
        settings = get_settings()
        best = sources[0].score
        mean_score = sum(item.score for item in sources) / len(sources)
        confidence = max(min(best * 0.7 + mean_score * 0.3, 1.0), 0.0)
        return confidence, confidence < settings.qa_confidence_threshold

    @staticmethod
    def _build_prompts(query: str, history: list[dict[str, str]], sources: list) -> tuple[str, str]:
        history_text = "\n".join(
            f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in history[-10:]
        )
        context = "\n\n".join(
            (
                f"[{item.document_id}/{item.chunk_id}] {item.title}\n"
                f"score={item.score:.4f}\n"
                f"{item.content[:700]}"
            )
            for item in sources
        )
        system_prompt = (
            "你是一个名为 Clever_Agent 的专业 IT 教学辅助智能体，由国产大模型驱动。你的核心职责是为学员提供 7x24 小时的专属答疑服务。\n\n"
            "【核心回答原则】\n"
            "1. 严格基于上下文：必须优先基于提供的【检索上下文】回答问题。如果上下文中没有包含足够的信息，请明确指出“根据当前知识库，我无法确定”，并建议用户换个问法或上传相关资料。\n"
            "2. 结构化与清晰性：回答必须结构清晰，合理使用 Markdown 语法（如：加粗、列表、代码块）。\n"
            "3. 教学引导风格：态度温和专业，除了给出直接答案外，适当时可以提供相关的扩展思路或学习建议，帮助学员更好理解知识点。\n"
            "4. 代码规范：如果回答包含代码，请务必指定正确的代码语言，并确保代码简洁、可读。\n"
            "5. 禁止编造：绝不捏造知识库中不存在的事实。若部分知识点需补充，可以提醒用户补充知识库。"
        )
        user_prompt = (
            f"用户问题：{query}\n\n"
            f"历史对话：\n{history_text}\n\n"
            f"检索上下文：\n{context}\n\n"
            "请给出最终回答。"
        )
        return system_prompt, user_prompt

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
