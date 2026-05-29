# app/tests/test_fallback_strategy.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.steps import LLMRunner
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_fallback_strategy_after_primary_failures(monkeypatch):
    """
    Verifierar att fallback-modellen används när huvudmodellen misslyckas
    efter alla retry-försök.
    """

    # ---------------------------------------------------------
    # 1. Mocka huvudmodellen så att den ALLTID misslyckas
    # ---------------------------------------------------------
    async def failing_primary(*args, **kwargs):
        raise RuntimeError("Primary LLM failure")

    monkeypatch.setattr(LLMRunner, "_run_model_async", failing_primary)

    # ---------------------------------------------------------
    # 2. Mocka fallback-modellen så att den lyckas
    # ---------------------------------------------------------
    async def fallback_model(*args, **kwargs):
        return {"answer": "Fallback OK"}

    monkeypatch.setattr(LLMRunner, "_run_fallback_async", fallback_model)

    # ---------------------------------------------------------
    # 3. Mocka ResponseParser så att den inte stör testet
    # ---------------------------------------------------------
    monkeypatch.setattr(
        PipelineOrchestrator,
        "parse_output",
        MagicMock(return_value={"answer": "Fallback OK"})
    )

    # ---------------------------------------------------------
    # 4. Ladda upp dataset
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}

    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}

    # ---------------------------------------------------------
    # 5. Kör /ai/ask → fallback ska användas
    # ---------------------------------------------------------
    res = client.post("/ai/ask", json=payload)

    assert res.status_code == 200
    assert "Fallback OK" in res.text

    # ---------------------------------------------------------
    # 6. Kontrollera Circuit Breaker
    #    Fallback ska rädda körningen → CB ska INTE trippla
    # ---------------------------------------------------------
    runner = LLMRunner()
    cb = runner.circuit

    assert cb.state == "CLOSED"
    assert cb.failure_count == 0
