"""QA Agent 节点函数（纯函数风格）。"""

from __future__ import annotations

from dataclasses import dataclass
import asyncio

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
    max_prompt_sources: int = 3
    max_source_chars: int = 700

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
        if not sources:
            # 没有命中知识时直接快速返回，避免无意义的大模型调用拖慢响应。
            return {
                "answer": "当前知识库没有检索到可用内容。请换个问法，或先上传相关资料后再提问。",
                "should_escalate": True,
                "confidence": 0.0,
            }

        top_sources = sources[: self.max_prompt_sources]
        context = self._join_sources(top_sources, self.max_source_chars)
        history_text = "\n".join(
            f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in state.get("history", [])
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
            f"用户问题：{state['query']}\n\n"
            f"历史对话：\n{history_text}\n\n"
            f"检索上下文：\n{context}\n\n"
            "请给出最终回答。"
        )
        # 给模型调用加一层超时保护，避免单次请求长时间阻塞前端。
        settings = get_settings()
        answer = await asyncio.wait_for(
            self.llm_factory.chat(system_prompt=system_prompt, user_prompt=user_prompt),
            timeout=settings.qa_request_timeout_seconds,
        )
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
    def _join_sources(sources: list[QASource], max_source_chars: int) -> str:
        if not sources:
            return "无可用知识片段。"
        return "\n\n".join(
            (
                f"[{item.document_id}/{item.chunk_id}] {item.title}\n"
                f"score={item.score:.4f}\n"
                f"{item.content[:max_source_chars]}"
            )
            for item in sources
        )
