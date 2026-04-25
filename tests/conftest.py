from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_orchestrator_endpoint_singletons() -> None:
    """避免跨用例污染 orchestrator endpoint 的全局单例。"""

    from app.api.v1.endpoints import orchestrator as orchestrator_endpoint

    orchestrator_endpoint._qa_service = None
    orchestrator_endpoint._grading_service = None
    orchestrator_endpoint._interview_service = None
    orchestrator_endpoint._resume_service = None

