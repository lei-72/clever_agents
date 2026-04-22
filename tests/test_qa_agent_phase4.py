"""QA Agent Phase 4 核心流程测试。"""

from __future__ import annotations

import unittest

from app.agents.qa.graph import build_qa_graph
from app.agents.qa.nodes import AsyncQANodes
from app.agents.qa.tools import QAAgentTools
from app.schemas.qa import QASource


class _FakeMemoryService:
    def __init__(self) -> None:
        self.turns: list[tuple[str, str, str]] = []

    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        return [{"role": "user", "content": "上一轮提问"}] if session_id else []

    async def append_turn(self, session_id: str, role: str, content: str) -> None:
        self.turns.append((session_id, role, content))


class _FakeRagTool:
    async def ingest(self, chunks):  # noqa: ANN001
        return len(chunks)

    async def retrieve_hybrid(self, query: str, top_k: int, rerank_k: int) -> list[QASource]:
        _ = (query, top_k)
        return [
            QASource(
                document_id="doc-1",
                chunk_id="c1",
                title="Python 异步",
                content="async/await 用于并发 IO。",
                source_uri="kb://python-async",
                score=0.87,
            )
        ][:rerank_k]


class _FakeLLMFactory:
    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        _ = (system_prompt, user_prompt)
        return "这是基于知识库的回答。"


class TestQAAgentGraph(unittest.IsolatedAsyncioTestCase):
    async def test_graph_pipeline(self) -> None:
        tools = QAAgentTools(rag_tool=_FakeRagTool(), memory_service=_FakeMemoryService())
        nodes = AsyncQANodes(tools=tools, llm_factory=_FakeLLMFactory())
        app = build_qa_graph(nodes)

        state = await app.ainvoke(
            {
                "trace_id": "t-1",
                "query": "什么是 async/await？",
                "session_id": "s-1",
                "top_k": 6,
                "rerank_k": 4,
            }
        )
        self.assertEqual(state["query_type"], "definition")
        self.assertIn("回答", state["answer"])
        self.assertGreater(state["confidence"], 0.0)
        self.assertEqual(state["should_escalate"], False)
        self.assertEqual(len(state["retrieved_sources"]), 1)


if __name__ == "__main__":
    unittest.main()
