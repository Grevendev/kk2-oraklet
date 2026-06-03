# tests/conftest.py

import os

# TESTING måste sättas innan app importeras
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data import data_service
from app.state import state
from app.container_test import get_test_pipeline


from app.chain.steps import GLOBAL_CIRCUIT_BREAKER

@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    """
    Säkerställer att Circuit Breaker alltid startar i CLOSED state
    och inte läcker state mellan tester.
    """
    GLOBAL_CIRCUIT_BREAKER.reset()
    yield
    GLOBAL_CIRCUIT_BREAKER.reset()



@pytest.fixture(autouse=True)
def reset_state():
    from app.api import ai

    data_service.clear()
    state.dataset = None
    state.stats = None
    ai._cache_store.clear()

    yield

    data_service.clear()
    state.dataset = None
    state.stats = None
    ai._cache_store.clear()


@pytest.fixture(autouse=True)
def patch_pipeline(monkeypatch):
    """
    Ersätter hela ai.pipeline med test-pipelinen.
    Detta är den ENDA patch som fungerar med FastAPI.
    """
    from app.api import ai
    test_pipeline = get_test_pipeline()

    # Viktigt: ersätt hela pipeline-objektet
    monkeypatch.setattr(ai, "pipeline", test_pipeline)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def disable_rate_limit(monkeypatch):
    from app.api import ai

    if hasattr(ai.ask_ai, "_rate_limit"):
        monkeypatch.delattr(ai.ask_ai, "_rate_limit", raising=False)

    if hasattr(ai.ask_ai_stream, "_rate_limit"):
        monkeypatch.delattr(ai.ask_ai_stream, "_rate_limit", raising=False)

    for route in ai.router.routes:
        if hasattr(route, "dependant"):
            route.dependant.dependencies = [
                d for d in route.dependant.dependencies
                if "slowapi" not in str(d.call)
            ]
