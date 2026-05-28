# app/tests/test_cache_invalidation.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_ai_cache_invalidation_after_new_upload(monkeypatch):
    """
    Verifierar att cache invalidieras när datasetet ändras.
    Ny upload → nytt fingerprint → nytt ETag → pipeline körs igen.
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
    # 2. Ladda upp första datasetet
    # ---------------------------------------------------------
    csv1 = "city,temp\nMalmö,10\nLund,12\n"
    files1 = {"file": ("test1.csv", csv1, "text/csv")}

    upload_res1 = client.post("/data/upload", files=files1)
    assert upload_res1.status_code == 200

    # ---------------------------------------------------------
    # 3. Första /ai/ask → genererar ETag
    # ---------------------------------------------------------
    payload = {"question": "Vad är medeltemperaturen?"}
    res1 = client.post("/ai/ask", json=payload)

    assert res1.status_code == 200
    assert "ETag" in res1.headers

    etag1 = res1.headers["ETag"]

    # Pipeline ska ha körts exakt 1 gång
    assert run_spy.call_count == 1

    # ---------------------------------------------------------
    # 4. Ladda upp ett nytt dataset → fingerprint ändras
    # ---------------------------------------------------------
    csv2 = "city,temp\nGöteborg,5\nUmeå,2\n"
    files2 = {"file": ("test2.csv", csv2, "text/csv")}

    upload_res2 = client.post("/data/upload", files=files2)
    assert upload_res2.status_code == 200

    # ---------------------------------------------------------
    # 5. Nytt /ai/ask → cache ska invalidieras → pipeline körs igen
    # ---------------------------------------------------------
    res2 = client.post("/ai/ask", json=payload)

    assert res2.status_code == 200
    assert "ETag" in res2.headers

    etag2 = res2.headers["ETag"]

    # ETag MÅSTE vara annorlunda efter ny upload
    assert etag1 != etag2

    # Pipeline ska ha körts igen → totalt 2 gånger
    assert run_spy.call_count == 2
