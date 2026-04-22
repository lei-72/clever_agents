"""Phase 3 Orchestrator MVP tests.

测试目标：
1) 验证路由规则是否命中预期 Agent
2) 验证 SSE 事件协议顺序是否固定为 route -> delta -> done
3) 验证 API 端点基础可用（同步路由 + SSE）
"""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.orchestrator import OrchestratorService
from app.schemas.orchestrator import AgentName, IntentLabel, OrchestratorRequest


class TestOrchestratorService(unittest.IsolatedAsyncioTestCase):
    """服务层测试：覆盖 Phase 3 MVP 的核心行为。"""

    def setUp(self) -> None:
        self.service = OrchestratorService()

    def test_route_grading_intent(self) -> None:
        """命中批改关键词时应路由到 Grading Agent。"""
        request = OrchestratorRequest(query="请帮我批改这份试卷")
        result = self.service.route(request)
        self.assertEqual(result.intent, IntentLabel.GRADING)
        self.assertEqual(result.agent, AgentName.GRADING_AGENT)

    def test_route_default_to_qa(self) -> None:
        """未命中特殊意图时应兜底到 QA Agent。"""
        request = OrchestratorRequest(query="这门课的知识点是什么")
        result = self.service.route(request)
        self.assertEqual(result.intent, IntentLabel.QA)
        self.assertEqual(result.agent, AgentName.QA_AGENT)

    async def test_stream_protocol_order(self) -> None:
        """SSE 事件必须按 route -> delta -> done 顺序输出。"""
        request = OrchestratorRequest(query="我要做一场模拟面试")
        chunks = [chunk async for chunk in self.service.stream_route_events(request)]

        # 每个 chunk 形如:
        # event: route
        # data: {...}
        # 这里仅断言协议关键字顺序，避免测试对文案细节过度耦合。
        self.assertIn("event: route", chunks[0])
        self.assertIn("event: delta", chunks[1])
        self.assertIn("event: done", chunks[2])
        self.assertEqual(len(chunks), 3)


class TestOrchestratorApi(unittest.TestCase):
    """接口层测试：验证 v1 orchestrator endpoint 基础行为。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_route_endpoint(self) -> None:
        """`/route` 返回结构化路由结果。"""
        response = self.client.post(
            "/api/v1/orchestrator/route",
            json={"query": "请给我的简历提建议"},
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["message"], "routed")
        self.assertEqual(payload["route"]["intent"], "resume")
        self.assertEqual(payload["route"]["agent"], "resume_agent")

    def test_stream_endpoint(self) -> None:
        """`/stream` 返回 SSE 文本流，并包含 route/delta/done 事件。"""
        response = self.client.post(
            "/api/v1/orchestrator/stream",
            json={"query": "帮我做技术面试"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers.get("content-type", ""))

        body = response.text
        self.assertIn("event: route", body)
        self.assertIn("event: delta", body)
        self.assertIn("event: done", body)


if __name__ == "__main__":
    unittest.main()
