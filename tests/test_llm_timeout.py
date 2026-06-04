import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator
import app.chain.steps as steps_module
from app.chain.steps import GLOBAL_CIRCUIT_BREAKER

client = TestClient(app)

def test_llm_timeout_triggers_pipeline_error(monkeypatch):
    """
    Verifierar att LLMRunner timeout triggas korrekt och ökar failure_count
    på GLOBAL_CIRCUIT_BREAKER.
    """
    # 1. Nollställ den globala breakern inför testet så att inga gamla tester stör
    GLOBAL_CIRCUIT_BREAKER.failure_count = 0

    # 2. Mocka den asynkrona modellen till att kasta TimeoutError direkt på klassen
    async def mock_run_model_async(self, prompt: str):
        raise TimeoutError("LLM timed out")

    monkeypatch.setattr(steps_module.LLMRunner, "_run_model_async", mock_run_model_async)

    # 3. Mocka bort sleep-metoden så att retries sker omedelbart utan att fördröja testet
    monkeypatch.setattr(steps_module.LLMRunner, "_sleep", lambda self, seconds: None)

    # 4. Mocka PipelineOrchestrator.parse_output för att säkerställa kontrollerad retur
    monkeypatch.setattr(
        PipelineOrchestrator,
        "parse_output",
        MagicMock(return_value={"answer": "timeout_fallback_triggered"})
    )

    # 5. Ladda upp dataset (krävs för att din pipeline ska kunna starta)
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}
    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    # 6. Kör anropet mot endpointen som drar igång pipelinen
    payload = {"question": "Vad är medeltemperaturen?"}
    res = client.post("/ai/ask", json=payload)

    # 7. Verifiera att anropet lyckades (tack vare fallback) och att breakern räknat upp
    assert res.status_code == 200
    assert "timeout" in res.text.lower()
    
    # Nu kommer denna garanterat att vara >= 1 eftersom efter_failure() anropas i 'except'
    assert GLOBAL_CIRCUIT_BREAKER.failure_count >= 1