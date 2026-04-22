"""QA Agent 节点函数（纯函数风格）。"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.llm import LLMFactory
from app.schemas.qa import QASource

from .state import QAAgentState
from .tools import QAAgentTools


def build_query_classifier() -> callable:
    """构造 query 分类节点。"""

    def classify_query(state: QAAgentState) -> QAAgentState:
        query = state["query"].lower()
        if any(word in query for word in ("定义", "是什么", "什么是", "what is", "概念")):
            query_type = "definition"
        elif any(word in query for word in ("怎么", "如何", "how", "步骤")):
            query_type = "procedure"
        else:
            query_type = "general"
        return {"query_type": query_type}

    return classify_query


@dataclass(slots=True)
class AsyncQANodes:
    """异步节点集合。"""

    tools: QAAgentTools
    llm_factory: LLMFactory

    async def load_history(self, state: QAAgentState) -> QAAgentState:
        history = await self.tools.memory_service.get_history(state["session_id"])
        return {"history": history}

    async def retrieve_documents(self, state: QAAgentState) -> QAAgentState:
        retrieved = await self.tools.retrieve(
            query=state["query"],
            top_k=state["top_k"],
            rerank_k=state["rerank_k"],
        )
        return {"retrieved_sources": retrieved}

    async def generate_answer(self, state: QAAgentState) -> QAAgentState:
        sources = state.get("retrieved_sources", [])
        context = self._join_sources(sources)
        history_text = "\n".join(
            f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in state.get("history", [])
        )

        system_prompt = (
            "你是教学问答助手。必须优先基于检索上下文回答。"
            "如果上下文不足，明确指出不确定并给出下一步建议。"
            "回答要简洁、结构化。"
        )
        user_prompt = (
            f"用户问题：{state['query']}\n\n"
            f"历史对话：\n{history_text}\n\n"
            f"检索上下文：\n{context}\n\n"
            "请给出最终回答。"
        )
        answer = await self.llm_factory.chat(system_prompt=system_prompt, user_prompt=user_prompt)
        return {"answer": answer}

    async def evaluate_confidence(self, state: QAAgentState) -> QAAgentState:
        sources = state.get("retrieved_sources", [])
        if not sources:
            return {"confidence": 0.0, "should_escalate": True}

        best = sources[0].score
        mean_score = sum(item.score for item in sources) / len(sources)
        confidence = max(min(best * 0.7 + mean_score * 0.3, 1.0), 0.0)

        settings = get_settings()
        should_escalate = confidence < settings.qa_confidence_threshold
        return {"confidence": confidence, "should_escalate": should_escalate}

    async def persist_history(self, state: QAAgentState) -> QAAgentState:
        await self.tools.memory_service.append_turn(state["session_id"], "user", state["query"])
        await self.tools.memory_service.append_turn(state["session_id"], "assistant", state["answer"])
        return {}

    @staticmethod
    def _join_sources(sources: list[QASource]) -> str:
        if not sources:
            return "无可用知识片段。"
        return "\n\n".join(
            (
                f"[{item.document_id}/{item.chunk_id}] {item.title}\n"
                f"score={item.score:.4f}\n"
                f"{item.content}"
            )
            for item in sources
        )
