# app/tests/test_circuit_breaker_open.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app

client = TestClient(app)


@pytest.mark.usefixtures(
    "reset_circuit_breaker",
    "reset_state",
    "disable_rate_limit",
    "reset_ai_cache",
)
def test_circuit_breaker_blocks_when_open(monkeypatch):
    """
    Detta test körs MEDVETET utan patch_pipeline-fixturen.
    """

    # ---------------------------------------------------------
    # 1. Patcha pipeline.run manuellt
    # ---------------------------------------------------------
    from app.api import ai
    run_spy = MagicMock()
    monkeypatch.setattr(ai.pipeline, "run", run_spy)

    # ---------------------------------------------------------
    # 2. Öppna rätt Circuit Breaker
    # ---------------------------------------------------------
    cb = ai.pipeline.circuit
    cb.state = "OPEN"
    cb.failure_count = cb.max_failures

    # ---------------------------------------------------------
    # 3. Ladda dataset
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}
    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}

    # ---------------------------------------------------------
    # 4. Anrop → ska blockeras direkt
    # ---------------------------------------------------------
    res = client.post("/ai/ask", json=payload)

    assert res.status_code == 500
    assert "circuit" in res.text.lower() or "breaker" in res.text.lower()

    # ---------------------------------------------------------
    # 5. Pipeline får INTE köras
    # ---------------------------------------------------------
    run_spy.assert_not_called()
