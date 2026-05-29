# app/tests/test_circuit_breaker_open.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_circuit_breaker_blocks_when_open(monkeypatch):
    """
    Verifierar att Circuit Breaker i OPEN state blockerar alla anrop direkt
    utan att pipeline.run körs.
    """

    # ---------------------------------------------------------
    # 1. Mocka pipeline.run så vi kan se om den körs
    # ---------------------------------------------------------
    run_spy = MagicMock()
    monkeypatch.setattr(PipelineOrchestrator, "run", run_spy)

    # ---------------------------------------------------------
    # 2. Hämta CB-instansen från LLMRunner och sätt den till OPEN
    # ---------------------------------------------------------
    from app.chain.steps import LLMRunner
    runner = LLMRunner()
    cb = runner.circuit

    cb.state = "OPEN"
    cb.failure_count = cb.max_failures

    # ---------------------------------------------------------
    # 3. Ladda upp dataset (krävs för /ai/ask)
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}

    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}

    # ---------------------------------------------------------
    # 4. Anrop → ska blockeras direkt av CB
    # ---------------------------------------------------------
    res = client.post("/ai/ask", json=payload)

    # Din implementation returnerar 503 eller 500 beroende på felhantering
    assert res.status_code in (500, 503)

    # Felmeddelandet ska indikera CB-blockering
    assert "circuit" in res.text.lower() or "breaker" in res.text.lower()

    # ---------------------------------------------------------
    # 5. Pipeline får INTE köras när CB är OPEN
    # ---------------------------------------------------------
    run_spy.assert_not_called()
