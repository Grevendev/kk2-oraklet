# app/tests/test_retry_policy.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.steps import LLMRunner
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_retry_policy_multiple_attempts(monkeypatch):
    """
    Verifierar att retry-policy kör flera försök innan den lyckas.
    Försök 1-2 misslyckas → försök 3 lyckas → pipeline returnerar 200.
    """

    # ---------------------------------------------------------
    # 1. Mocka LLMRunner._run_model_async så att:
    #    - Försök 1 → RuntimeError
    #    - Försök 2 → RuntimeError
    #    - Försök 3 → lyckas
    # ---------------------------------------------------------
    call_counter = {"count": 0}

    async def flaky_model(*args, **kwargs):
        call_counter["count"] += 1
        if call_counter["count"] < 3:
            raise RuntimeError("Simulated transient LLM failure")
        return {"answer": "Retry success"}

    monkeypatch.setattr(LLMRunner, "_run_model_async", flaky_model)

    # ---------------------------------------------------------
    # 2. Mocka backoff-sleep så att testet inte väntar på riktigt
    # ---------------------------------------------------------
    monkeypatch.setattr(LLMRunner, "_sleep", lambda *args, **kwargs: None)

    # ---------------------------------------------------------
    # 3. Mocka ResponseParser så att den inte stör testet
    # ---------------------------------------------------------
    monkeypatch.setattr(
        PipelineOrchestrator,
        "parse_output",
        MagicMock(return_value={"answer": "Retry success"})
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
    # 5. Kör /ai/ask → retry-policy ska göra 3 försök
    # ---------------------------------------------------------
    res = client.post("/ai/ask", json=payload)

    assert res.status_code == 200
    assert "Retry success" in res.text

    # ---------------------------------------------------------
    # 6. Kontrollera att modellen kördes exakt 3 gånger
    # ---------------------------------------------------------
    assert call_counter["count"] == 3

    # ---------------------------------------------------------
    # 7. Kontrollera att Circuit Breaker inte trippar
    # ---------------------------------------------------------
    runner = LLMRunner()
    cb = runner.circuit

    assert cb.state == "CLOSED"
    assert cb.failure_count == 0
