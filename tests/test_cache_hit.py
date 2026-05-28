# app/tests/test_cache_hit.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_ai_cache_hit(monkeypatch):
    """
    Verifierar att andra anropet till /ai/ask returnerar 304 Not Modified
    när ETag matchar cache-nyckeln.
    """

    # ---------------------------------------------------------
    # 1. Mocka pipeline.run så vi kan se om den körs igen
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
    # 3. Första anropet → ska generera ETag
    # ---------------------------------------------------------
    payload = {"question": "Vad är medeltemperaturen?"}
    res1 = client.post("/ai/ask", json=payload)

    assert res1.status_code == 200
    assert "ETag" in res1.headers

    etag = res1.headers["ETag"]

    # Pipeline ska ha körts exakt 1 gång
    assert run_spy.call_count == 1

    # ---------------------------------------------------------
    # 4. Andra anropet → ska ge 304 Not Modified
    # ---------------------------------------------------------
    res2 = client.post(
        "/ai/ask",
        json=payload,
        headers={"If-None-Match": etag}
    )

    assert res2.status_code == 304

    # Pipeline ska INTE ha körts igen
    assert run_spy.call_count == 1
