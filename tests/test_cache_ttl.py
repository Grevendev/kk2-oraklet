# app/tests/test_cache_ttl.py

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator
from app.config import STATS_CACHE_TTL_SECONDS


client = TestClient(app)


def test_ai_cache_ttl_expiration(monkeypatch):
    """
    Verifierar att cache upphör att gälla efter TTL.
    Efter TTL ska pipeline köras igen och ETag ska ändras.
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
    # 4. Vänta tills TTL löpt ut
    # ---------------------------------------------------------
    time.sleep(STATS_CACHE_TTL_SECONDS + 1)

    # ---------------------------------------------------------
    # 5. Nytt /ai/ask → cache ska vara expired → pipeline körs igen
    # ---------------------------------------------------------
    res2 = client.post("/ai/ask", json=payload)

    assert res2.status_code == 200
    assert "ETag" in res2.headers

    etag2 = res2.headers["ETag"]

    # ETag MÅSTE vara annorlunda efter TTL-expiration
    assert etag1 != etag2

    # Pipeline ska ha körts igen → totalt 2 gånger
    assert run_spy.call_count == 2
