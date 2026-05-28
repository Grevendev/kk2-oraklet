# tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data import data_service
from app.state import state
from app.container_test import get_test_pipeline

os.environ["TESTING"] = "1"


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
    monkeypatch.setattr(ai, "pipeline", get_test_pipeline())


@pytest.fixture
def client():
    """
    Ger en TestClient som använder den patchade test-pipelinen.
    """
    return TestClient(app)
