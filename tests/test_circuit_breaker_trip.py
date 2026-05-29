# app/tests/test_circuit_breaker_trip.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator
from app.chain.circuit_breaker import CircuitBreaker


client = TestClient(app)


def test_circuit_breaker_trips_after_failures(monkeypatch):
    """
    Verifierar att Circuit Breaker går till OPEN state efter upprepade fel
    och därefter blockerar alla nya anrop direkt.
    """

    # ---------------------------------------------------------
    # 1. Mocka pipeline.run så att den kastar fel varje gång
    # ---------------------------------------------------------
    def failing_run(*args, **kwargs):
        raise RuntimeError("Simulated LLM failure")

    monkeypatch.setattr(PipelineOrchestrator, "run", failing_run)

    # ---------------------------------------------------------
    # 2. Hämta CB-instansen från LLMRunner
    #    (alla LLMRunner delar samma CB i din implementation)
    # ---------------------------------------------------------
    from app.chain.steps import LLMRunner
    runner = LLMRunner()
    cb = runner.circuit

    # Säkerställ att vi börjar i CLOSED state
    cb.state = "CLOSED"
    cb.failure_count = 0

    # ---------------------------------------------------------
    # 3. Ladda upp dataset (krävs för /ai/ask)
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}

    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}

    # ---------------------------------------------------------
    # 4. Trigga fel tills CB trippar
    # ---------------------------------------------------------
    for _ in range(cb.max_failures):
        res = client.post("/ai/ask", json=payload)
        assert res.status_code == 500  # pipeline-fel

    # Circuit Breaker ska nu vara OPEN
    assert cb.state == "OPEN"

    # ---------------------------------------------------------
    # 5. Nytt anrop → ska blockeras direkt (ingen pipeline-run)
    # ---------------------------------------------------------
    res_blocked = client.post("/ai/ask", json=payload)

    # CB ska blockera direkt → 503 eller 500 beroende på din implementation
    assert res_blocked.status_code in (500, 503)

    # Felmeddelandet ska indikera CB-blockering
    assert "circuit" in res_blocked.text.lower() or "breaker" in res_blocked.text.lower()
