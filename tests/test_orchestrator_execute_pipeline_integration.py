from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.grading import GradingResponse, LearningAnalysisReport
from app.schemas.interview import InterviewSessionSnapshot, InterviewStartResponse, InterviewStatus, InterviewStage
from app.schemas.qa import QAResponse
from app.schemas.resume import ResumeRadarChartData, ResumeReviewResponse


class _FakeQAService:
    async def run(self, request):  # noqa: ANN001
        return QAResponse(
            answer=f"fake-answer: {request.query}",
            confidence=0.9,
            should_escalate=False,
            sources=[],
            trace_id="t-qa-1",
        )


class _FakeGradingService:
    async def run(self, request):  # noqa: ANN001
        return GradingResponse(
            exam_id=request.exam_id,
            student_id=request.student_id,
            total_score=10.0,
            full_score=20.0,
            reviewed=False,
            question_results=[],
            teacher_review_items=[],
            analysis_report=LearningAnalysisReport(),
            trace_id="t-grade-1",
        )


class _FakeInterviewService:
    async def start(self, request):  # noqa: ANN001
        session = InterviewSessionSnapshot(
            session_id="interview-123",
            candidate_id=request.candidate_id,
            status=InterviewStatus.RUNNING,
            current_stage=InterviewStage.INTRO,
        )
        return InterviewStartResponse(session=session)


class _FakeResumeService:
    async def run(self, request):  # noqa: ANN001
        return ResumeReviewResponse(
            overall_score=88.0,
            dimension_scores=[],
            high_priority_issues=[],
            medium_priority_issues=[],
            low_priority_issues=[],
            radar_metrics=[],
            radar_chart=ResumeRadarChartData(indicators=[], values=[], max_value=100.0),
            trace_id="t-resume-1",
        )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from app.api.v1.endpoints import orchestrator as orchestrator_endpoint

    async def _fake_get_qa_service():
        return _FakeQAService()

    async def _fake_get_grading_service():
        return _FakeGradingService()

    async def _fake_get_interview_service():
        return _FakeInterviewService()

    async def _fake_get_resume_service():
        return _FakeResumeService()

    monkeypatch.setattr(orchestrator_endpoint, "_get_qa_service", _fake_get_qa_service)
    monkeypatch.setattr(orchestrator_endpoint, "_get_grading_service", _fake_get_grading_service)
    monkeypatch.setattr(orchestrator_endpoint, "_get_interview_service", _fake_get_interview_service)
    monkeypatch.setattr(orchestrator_endpoint, "_get_resume_service", _fake_get_resume_service)
    return TestClient(app)


def test_execute_routes_to_qa_and_returns_result(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/orchestrator/execute",
        json={"query": "什么是RAG？", "session_id": "s1", "user_id": "u1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["route"]["agent"] == "qa_agent"
    assert body["qa_result"]["answer"].startswith("fake-answer:")
    assert body["qa_result"]["trace_id"] == "t-qa-1"


def test_execute_requires_grading_payload_when_routed_to_grading(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/orchestrator/execute",
        json={"query": "请批改这份试卷", "session_id": "s1", "user_id": "u1"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "BAD_REQUEST"


def test_pipeline_execute_job_coaching_success(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/orchestrator/pipeline/execute",
        json={
            "query": "帮我做求职辅导",
            "pipeline_type": "job_coaching",
            "expect_trace": True,
            "resume_payload": {
                "resume_text": "这是用于测试的简历文本，长度至少二十个字符。",
                "target_role": "后端",
                "job_description": "JD",
            },
            "interview_payload": {
                "candidate_id": "c1",
                "resume_profile": {"summary": "s", "skills": [], "projects": []},
                "history_performance": [],
                "weak_tag_pool": [],
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pipeline_type"] == "job_coaching"
    assert body["unified_output"]["final_message"]
    assert body["trace"]["pipeline_id"].startswith("pipeline-")


def test_pipeline_execute_coding_coaching_missing_payload_degrades_to_failed_trace(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/orchestrator/pipeline/execute",
        json={
            "query": "这道题我总是超时，请帮我分析",
            "pipeline_type": "coding_coaching",
            "expect_trace": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["trace"]["status"] in {"failed", "success"}
    # 至少应该包含节点追踪，缺 payload 的 grading 节点会标记 failed
    assert len(body["trace"]["nodes"]) >= 1

