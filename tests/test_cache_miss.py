# app/tests/test_cache_miss.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator


client = TestClient(app)


def test_ai_cache_miss(monkeypatch):

    class FakeParsed:
        def __init__(self):
            self.answer = "Mockat svar"
            self.model = "test-model"
            self.stats_used = {}
            self.reasoning = "Mockad reasoning"

    run_spy = MagicMock(return_value=FakeParsed())
    monkeypatch.setattr(PipelineOrchestrator, "run", run_spy)

    csv_content = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}

    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}
    res1 = client.post("/ai/ask", json=payload)

    assert res1.status_code == 200
    assert "ETag" in res1.headers
    assert run_spy.call_count == 1

    res2 = client.post("/ai/ask", json=payload)

    assert res2.status_code == 200
    assert "ETag" in res2.headers
    assert run_spy.call_count == 2
