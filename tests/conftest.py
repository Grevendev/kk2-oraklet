# tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data import data_service
from app.state import state
from app.container_test import get_test_pipeline


# ---------------------------------------------------------
# Aktivera testläge
# ---------------------------------------------------------
os.environ["TESTING"] = "1"


@pytest.fixture(autouse=True)
def reset_state():
    """
    Rensar dataservice, state och AI-cache före och efter varje test.
    """
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
    Patchar den pipeline som FastAPI faktiskt använder.
    Detta är den ENDA patch som fungerar med FastAPI.
    """
    from app.api import ai

    # Skapa testpipeline
    test_pipeline = get_test_pipeline()

    # Patcha pipeline-variabeln i ai-modulen
    monkeypatch.setattr(ai, "pipeline", test_pipeline)

    # Patcha run-metoden på den pipeline som redan är bunden i routern
    # (FastAPI binder pipeline.run vid import av ai.py)
    for route in ai.router.routes:
        if hasattr(route, "endpoint"):
            if hasattr(route.endpoint, "__self__"):
                # Patcha endpointens pipeline om den har en
                endpoint_self = route.endpoint.__self__
                if hasattr(endpoint_self, "pipeline"):
                    monkeypatch.setattr(endpoint_self, "pipeline", test_pipeline)


@pytest.fixture
def client():
    """
    Ger en TestClient som använder den patchade test-pipelinen.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def disable_rate_limit(monkeypatch):
    """
    Tar bort SlowAPI rate limiting helt i tester.
    """
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
