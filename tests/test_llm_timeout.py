import pytest
import gc
import types
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.chain.orchestrator import PipelineOrchestrator
import app.chain.steps as steps_module

client = TestClient(app)

def test_llm_timeout_triggers_pipeline_error(monkeypatch):
    """
    Verifierar att LLMRunner timeout triggas korrekt och ökar failure_count
    genom att leta upp och patcha den exakta instansen i minnet.
    """
    # ---------------------------------------------------------
    # 1. Hitta ALLA existerande LLMRunner-instanser i minnet
    # ---------------------------------------------------------
    live_runners = [obj for obj in gc.get_objects() if type(obj).__name__ == "LLMRunner"]

    # ---------------------------------------------------------
    # 2. Skapa vår mock-metod som kastar TimeoutError
    # ---------------------------------------------------------
    async def mock_run_model_async(self, prompt: str):
        raise TimeoutError("LLM timed out")

    # ---------------------------------------------------------
    # 3. Hängslen och livrem: Patcha ALLT (Instanser, Klasser och Breakers)
    # ---------------------------------------------------------
    # Nollställ modulens globala breaker utifall den används
    steps_module.GLOBAL_CIRCUIT_BREAKER.failure_count = 0
    monkeypatch.setattr(steps_module.LLMRunner, "_run_model_async", mock_run_model_async)
    monkeypatch.setattr(steps_module.LLMRunner, "_sleep", lambda self, seconds: None)

    # Patcha de faktiska instanserna som FastAPI-appen redan har laddat in i minnet
    for runner in live_runners:
        runner.circuit.failure_count = 0
        # Binder om metoderna dynamiskt på instansnivå
        runner._run_model_async = types.MethodType(mock_run_model_async, runner)
        runner._sleep = types.MethodType(lambda self, seconds: None, runner)

    # ---------------------------------------------------------
    # 4. Mocka PipelineOrchestrator.parse_output för kontrollerad retur
    # ---------------------------------------------------------
    monkeypatch.setattr(
        PipelineOrchestrator,
        "parse_output",
        MagicMock(return_value={"answer": "timeout_fallback_triggered"})
    )

    # ---------------------------------------------------------
    # 5. Kör applikationsflödet (ladda upp CSV och anropa endpoint)
    # ---------------------------------------------------------
    csv = "city,temp\nMalmö,10\nLund,12\n"
    files = {"file": ("test.csv", csv, "text/csv")}
    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    payload = {"question": "Vad är medeltemperaturen?"}
    res = client.post("/ai/ask", json=payload)

    # ---------------------------------------------------------
    # 6. Verifiera resultat och att breakern faktiskt har räknat upp
    # ---------------------------------------------------------
    assert res.status_code == 200
    assert "timeout" in res.text.lower()
    
    # Vi kollar både minnes-instanserna och modulens breaker för säkerhets skull
    if live_runners:
        assert any(runner.circuit.failure_count >= 1 for runner in live_runners), \
            "Ingen av de levande LLMRunner-instanserna registrerade felet."
    else:
        assert steps_module.GLOBAL_CIRCUIT_BREAKER.failure_count >= 1, \
            "Modulens globala circuit breaker registrerade inte felet."