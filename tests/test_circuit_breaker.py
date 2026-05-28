import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================
# Helper
# ============================================================

def _invalid_csv():
    """Helper: returns a CSV that always triggers ValidationError."""
    return b"bad_column\n123"


# ============================================================
# Circuit Breaker Tests
# ============================================================

def test_circuit_breaker_opens(monkeypatch):
    """
    After 10 validation failures within 30 seconds,
    the circuit breaker should open and block /data/upload.
    """

    fake_time = [1000.0]

    def fake_time_func():
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_time_func)

    # Trigger 10 validation failures
    for _ in range(10):
        response = client.post(
            "/data/upload",
            files={"file": ("bad.csv", _invalid_csv())}
        )
        assert response.status_code == 422  # ValidationError

    # Circuit breaker should now be open
    response = client.post(
        "/data/upload",
        files={"file": ("bad.csv", _invalid_csv())}
    )

    assert response.status_code == 503
    body = response.json()
    assert body["error_type"] == "CircuitBreakerOpen"
    assert "retry_after_seconds" in body


def test_circuit_breaker_blocks_requests(monkeypatch):
    """
    Ensure that once the circuit breaker is open,
    all /data/upload requests return 503.
    """

    fake_time = [2000.0]

    def fake_time_func():
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_time_func)

    # Open circuit breaker by simulating 10 failures
    for _ in range(10):
        client.post(
            "/data/upload",
            files={"file": ("bad.csv", _invalid_csv())}
        )

    # Immediately after → should be blocked
    response = client.post(
        "/data/upload",
        files={"file": ("bad.csv", _invalid_csv())}
    )

    assert response.status_code == 503
    assert response.json()["error_type"] == "CircuitBreakerOpen"


def test_circuit_breaker_resets_after_timeout(monkeypatch):
    """
    After CIRCUIT_BREAKER_DURATION seconds have passed,
    /data/upload should work again.
    """

    fake_time = [3000.0]

    def fake_time_func():
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_time_func)

    # Trigger 10 failures → opens breaker
    for _ in range(10):
        client.post(
            "/data/upload",
            files={"file": ("bad.csv", _invalid_csv())}
        )

    # Confirm breaker is open
    blocked = client.post(
        "/data/upload",
        files={"file": ("bad.csv", _invalid_csv())}
    )
    assert blocked.status_code == 503

    # Advance time by 31 seconds (breaker duration = 30)
    fake_time[0] += 31

    # Now upload should be allowed again
    valid_csv = b"city,temp\nMalmo,10"
    response = client.post(
        "/data/upload",
        files={"file": ("data.csv", valid_csv)}
    )

    assert response.status_code == 200
