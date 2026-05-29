# app/tests/test_circuit_breaker_half_open.py

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_circuit_breaker_half_open_recovery(monkeypatch):
    """
    Verifierar att Circuit Breaker går från OPEN → HALF_OPEN efter timeout
    och återställs till CLOSED när ett testanrop lyckas.
    """

    # ---------------------------------------------------------
    # 1. Mocka pipeline.run så att det lyckas (för recovery)
    # ---------------------------------------------------------
    run_spy = MagicMock(return_value={
        "question": "Vad är medeltemperaturen?",
        "answer": "Recovery OK",
        "model": "test-model"
    })

    monkeypatch.setattr(PipelineOrchestrator, "run", run_spy)

    # ---------------------------------------------------------
    # 2. Hämta CB-instansen från LLMRunner
    # ---------------------------------------------------------
    from app.chain.steps import LLMRunner
    runner = LLMRunner()
    cb = runner.circuit

    # Sätt CB till OPEN state
    cb.state = "OPEN"
    cb.failure_count = cb.max_failures

    # ---------------------------------------------------------
    # 3. Ladda upp dataset
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}

    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}

    # ---------------------------------------------------------
    # 4. Vänta tills CB timeout passerat → HALF_OPEN
    # ---------------------------------------------------------
    time.sleep(cb.reset_timeout + 0.5)

    # CB ska nu vara redo att gå till HALF_OPEN
    assert cb.state == "OPEN"  # fortfarande OPEN tills första anropet

    # ---------------------------------------------------------
    # 5. Första anropet efter timeout → HALF_OPEN → pipeline körs
    # ---------------------------------------------------------
    res1 = client.post("/ai/ask", json=payload)

    assert res1.status_code == 200
    assert "Recovery OK" in res1.text

    # Pipeline ska ha körts exakt 1 gång
    assert run_spy.call_count == 1

    # CB ska nu vara CLOSED igen
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0

    # ---------------------------------------------------------
    # 6. Nytt anrop → ska fungera normalt (CLOSED)
    # ---------------------------------------------------------
    res2 = client.post("/ai/ask", json=payload)

    assert res2.status_code == 200

    # Pipeline ska ha körts igen → totalt 2 gånger
    assert run_spy.call_count == 2
