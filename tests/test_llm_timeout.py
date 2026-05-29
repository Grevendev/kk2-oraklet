# app/tests/test_llm_timeout.py

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator
from app.chain.steps import LLMRunner


client = TestClient(app)


def test_llm_timeout_triggers_pipeline_error(monkeypatch):
    """
    Verifierar att LLMRunner timeout triggas korrekt och att pipeline
    returnerar fel utan att hänga.
    """

    # ---------------------------------------------------------
    # 1. Mocka LLMRunner.run_model så att den aldrig returnerar
    #    → simulerar en hängande LLM
    # ---------------------------------------------------------
    async def hanging_model(*args, **kwargs):
        await asyncio.sleep(999)  # längre än timeout

    monkeypatch.setattr(LLMRunner, "_run_model_async", hanging_model)

    # ---------------------------------------------------------
    # 2. Mocka ResponseParser så att den inte stör testet
    # ---------------------------------------------------------
    monkeypatch.setattr(
        PipelineOrchestrator,
        "parse_output",
        MagicMock(return_value={"answer": "timeout"})
    )

    # ---------------------------------------------------------
    # 3. Ladda upp dataset
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}

    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}

    # ---------------------------------------------------------
    # 4. Kör /ai/ask → timeout ska triggas → 500
    # ---------------------------------------------------------
    res = client.post("/ai/ask", json=payload)

    assert res.status_code == 500
    assert "timeout" in res.text.lower() or "timed" in res.text.lower()

    # ---------------------------------------------------------
    # 5. Kontrollera att Circuit Breaker failure_count ökat
    # ---------------------------------------------------------
    runner = LLMRunner()
    cb = runner.circuit

    assert cb.failure_count >= 1
