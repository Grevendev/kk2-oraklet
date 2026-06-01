# tests/conftest.py

import os

# ---------------------------------------------------------
# Sätt TESTING innan appen importeras
# ---------------------------------------------------------
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data import data_service
from app.state import state
from app.container_test import get_test_pipeline


@pytest.fixture(autouse=True)
def reset_state():
    """
    Rensar dataservice, state och AI-cache före och efter varje test.
    """
    from app.api import ai

    # Före test
    data_service.clear()
    state.dataset = None
    state.stats = None
    ai._cache_store.clear()

    yield

    # Efter test
    data_service.clear()
    state.dataset = None
    state.stats = None
    ai._cache_store.clear()


@pytest.fixture(autouse=True)
def patch_pipeline(monkeypatch):
    """
    Ersätter produktions-pipelinen med TestPipeline för ALLA tester.
    """
    from app.api import ai
    test_pipeline = get_test_pipeline()

    # Byt ut pipeline-variabeln i ai-modulen mot test-pipelinen
    monkeypatch.setattr(ai, "pipeline", test_pipeline)


@pytest.fixture
def client():
    """
    Ger en TestClient som använder den patchade test-pipelinen.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def disable_rate_limit(monkeypatch):
    from app.api import ai

    # Ta bort SlowAPI's rate-limit attribut
    if hasattr(ai.ask_ai, "_rate_limit"):
        monkeypatch.delattr(ai.ask_ai, "_rate_limit", raising=False)

    if hasattr(ai.ask_ai_stream, "_rate_limit"):
        monkeypatch.delattr(ai.ask_ai_stream, "_rate_limit", raising=False)

    # Ta bort SlowAPI dependencies från FastAPI-routen
    for route in ai.router.routes:
        if hasattr(route, "dependant"):
            route.dependant.dependencies = [
                d for d in route.dependant.dependencies
                if "slowapi" not in str(d.call)
            ]
