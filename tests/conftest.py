import os
import pytest
from fastapi.testclient import TestClient

# Se till att TESTING-flaggan är satt innan app importeras
os.environ["TESTING"] = "1"

from app.main import app
from app.data import data_service
from app.state import state


@pytest.fixture(autouse=True)
def reset_state():
    # Rensa globalt state och dataservice mellan tester
    data_service.clear()
    state.dataset = None
    state.stats = None
    yield
    data_service.clear()
    state.dataset = None
    state.stats = None


@pytest.fixture
def client():
    return TestClient(app)
