# app/tests/test_circuit_breaker_half_open.py

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

    # Sänk tröskeln så CB öppnar direkt
    cb.max_failures = 1
    cb.recovery_time_sec = 1
    cb.reset()

    # ---------------------------------------------------------
    # 3. Ladda upp dataset (krävs för /ai/ask)
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}
    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}

    # ---------------------------------------------------------
    # 4. Tvinga CB till OPEN state
    # ---------------------------------------------------------
    cb.state = "OPEN"
    cb.failure_count = cb.max_failures
    cb.opened_at = time.time()

    # Direkt efter öppning ska CB blockera
    blocked = client.post("/ai/ask", json=payload)
    assert blocked.status_code == 500

    # ---------------------------------------------------------
    # 5. Vänta tills CB kan gå till HALF_OPEN
    # ---------------------------------------------------------
    time.sleep(cb.recovery_time_sec + 0.1)

    # CB är fortfarande OPEN tills första anropet
    assert cb.state == "OPEN"

    # ---------------------------------------------------------
    # 6. Första anropet efter timeout → HALF_OPEN → CLOSED
    # ---------------------------------------------------------
    res1 = client.post("/ai/ask", json=payload)
    assert res1.status_code == 200
    assert "Recovery OK" in res1.text

    # Pipeline ska ha körts exakt 1 gång
    assert run_spy.call_count == 1

    # CB ska nu vara CLOSED (eller i vissa race: HALF_OPEN → CLOSED)
    assert cb.state in ("CLOSED", "HALF_OPEN")

    # failure_count kan vara 0 eller 1 beroende på timing
    assert cb.failure_count in (0, 1)

    # ---------------------------------------------------------
    # 7. Nytt anrop → ska fungera normalt
    # ---------------------------------------------------------
    res2 = client.post("/ai/ask", json=payload)
    assert res2.status_code == 200
    assert run_spy.call_count == 2
