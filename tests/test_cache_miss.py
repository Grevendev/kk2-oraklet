# app/tests/test_cache_miss.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_ai_cache_miss(monkeypatch):
    """
    Verifierar att /ai/ask kör pipelinen när ingen ETag skickas
    eller när cache saknas → cache-miss.
    """

    # ---------------------------------------------------------
    # 1. Mocka pipeline.run så vi kan se hur många gånger den körs
    # ---------------------------------------------------------
    run_spy = MagicMock(return_value={
        "question": "Vad är medeltemperaturen?",
        "answer": "Mockat svar",
        "model": "test-model"
    })

    monkeypatch.setattr(PipelineOrchestrator, "run", run_spy)

    # ---------------------------------------------------------
    # 2. Ladda upp dataset
    # ---------------------------------------------------------
    csv_content = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}

    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    # ---------------------------------------------------------
    # 3. Första anropet → cache miss (ingen ETag skickas)
    # ---------------------------------------------------------
    payload = {"question": "Vad är medeltemperaturen?"}
    res1 = client.post("/ai/ask", json=payload)

    assert res1.status_code == 200
    assert "ETag" in res1.headers

    # Pipeline ska ha körts exakt 1 gång
    assert run_spy.call_count == 1

    # ---------------------------------------------------------
    # 4. Andra anropet → cache miss igen (ingen If-None-Match)
    # ---------------------------------------------------------
    res2 = client.post("/ai/ask", json=payload)

    assert res2.status_code == 200
    assert "ETag" in res2.headers

    # Pipeline ska ha körts igen → totalt 2 gånger
    assert run_spy.call_count == 2
