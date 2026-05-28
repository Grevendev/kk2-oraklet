import os
import pytest
from fastapi.testclient import TestClient
from app.schemas import AIResponse

# Se till att TESTING-flaggan är satt innan app importeras
os.environ["TESTING"] = "1"

from app.main import app
from app.data import data_service
from app.state import state


@pytest.fixture(autouse=True)
def reset_state():
    # Rensa globalt state och dataservice mellan tester
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

@pytest.fixture(autouse=True)
def mock_pipeline_run(monkeypatch):
    """Mockar hela AI‑pipeline så inga riktiga LLM‑anrop görs."""
    def fake_run(question: str):
        return AIResponse(
            question=question,
            answer="Detta är ett mockat AI‑svar.",
            reasoning="Mockad reasoning.",
            stats_used={"temp": {"mean": 10}}
        )
    monkeypatch.setattr("app.api.ai.pipeline.run", fake_run)
    yield
