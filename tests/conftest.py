# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from app.schemas import AIResponse

os.environ["TESTING"] = "1"

from app.main import app
from app.data import data_service
from app.state import state


@pytest.fixture(autouse=True)
def reset_state():
    data_service.clear()
    state.dataset = None
    state.stats = None
    yield
    data_service.clear()
    state.dataset = None
    state.stats = None


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_pipeline_run(monkeypatch):
    """Opt-in mock av pipeline.run för tester som vill ha det."""
    from app.api import ai

    def fake_run(question: str):
        return AIResponse(
            question=question,
            answer="Detta är ett mockat AI‑svar.",
            reasoning="Mockad reasoning.",
            stats_used={"temp": {"mean": 10}}
        )

    monkeypatch.setattr(ai.pipeline, "run", fake_run)
