from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    """Ensure the health endpoint returns OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_invalid_file():
    """Uploading a non-CSV file should return 422 ValidationError."""
    response = client.post(
        "/data/upload",
        files={"file": ("test.txt", b"hello")}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_and_stats():
    """Upload a valid CSV and then retrieve stats."""
    csv_content = b"city,temp\nMalmo,10\nLund,12"

    upload_response = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv_content)}
    )
    assert upload_response.status_code == 200

    stats_response = client.get("/data/stats")
    assert stats_response.status_code == 200
    assert "stats" in stats_response.json()


def test_upload_too_large_file():
    """Uploading a file larger than allowed should return 400 UserError."""
    big_content = b"a" * (51 * 1024 * 1024)  # 51 MB
    response = client.post(
        "/data/upload",
        files={"file": ("big.csv", big_content)}
    )
    assert response.status_code == 400
    assert response.json()["error_type"] == "UserError"


def test_upload_invalid_columns():
    """Uploading a CSV with invalid column names should return 422 ValidationError."""
    csv_content = b"Unnamed: 0,temp\n1,10"
    response = client.post(
        "/data/upload",
        files={"file": ("bad.csv", csv_content)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_download_csv_without_upload():
    """Downloading CSV without uploading should return 422 ValidationError."""
    response = client.get("/data/download/csv")
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_download_parquet_without_upload():
    """Downloading Parquet without uploading should return 422 ValidationError."""
    response = client.get("/data/download/parquet")
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_and_download_parquet():
    """Upload CSV and ensure Parquet download works."""
    csv_content = b"city,temp\nMalmo,10\nLund,12"

    upload_response = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv_content)}
    )
    assert upload_response.status_code == 200

    parquet_response = client.get("/data/download/parquet")
    assert parquet_response.status_code == 200
    assert parquet_response.headers["Content-Disposition"] == "attachment; filename=dataset.parquet"


def test_error_model_structure():
    """Ensure error responses follow the standardized ErrorResponse model."""
    response = client.get("/data/stats")  # no dataset uploaded
    assert response.status_code == 422

    body = response.json()
    assert "error_type" in body
    assert "message" in body
    assert "details" in body


def test_validation_error_for_empty_csv():
    """Uploading an empty CSV should return 422 ValidationError."""
    response = client.post(
        "/data/upload",
        files={"file": ("empty.csv", b"")}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_user_error_for_stats_without_upload():
    """Requesting stats without uploading should return 422 ValidationError."""
    response = client.get("/data/stats")
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"

# ============================================================
# /data/upload — 5 requests per minute
# ============================================================

def test_rate_limit_upload():
    """Ensure /data/upload enforces 5 requests/minute."""
    csv = b"city,temp\nMalmo,10"

    # First 5 uploads should pass
    for _ in range(5):
        response = client.post(
            "/data/upload",
            files={"file": ("data.csv", csv)}
        )
        assert response.status_code == 200

    # 6th request should be rate-limited
    response = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert response.status_code == 429
    assert response.json()["error_type"] == "RateLimitExceeded"


# ============================================================
# /data/stats — 20 requests per minute
# ============================================================

def test_rate_limit_stats():
    """Ensure /data/stats enforces 20 requests/minute."""

    # Upload dataset first
    csv = b"city,temp\nMalmo,10"
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert upload.status_code == 200

    # First 20 requests should pass
    for _ in range(20):
        response = client.get("/data/stats")
        assert response.status_code == 200

    # 21st request should be rate-limited
    response = client.get("/data/stats")
    assert response.status_code == 429
    assert response.json()["error_type"] == "RateLimitExceeded"


# ============================================================
# /data/download/csv — 10 requests per minute
# ============================================================

def test_rate_limit_download_csv():
    """Ensure /data/download/csv enforces 10 requests/minute."""

    # Upload dataset first
    csv = b"city,temp\nMalmo,10"
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert upload.status_code == 200

    # First 10 requests should pass
    for _ in range(10):
        response = client.get("/data/download/csv")
        assert response.status_code == 200

    # 11th request should be rate-limited
    response = client.get("/data/download/csv")
    assert response.status_code == 429
    assert response.json()["error_type"] == "RateLimitExceeded"


# ============================================================
# /data/download/parquet — 10 requests per minute
# ============================================================

def test_rate_limit_download_parquet():
    """Ensure /data/download/parquet enforces 10 requests/minute."""

    # Upload dataset first
    csv = b"city,temp\nMalmo,10"
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert upload.status_code == 200

    # First 10 requests should pass
    for _ in range(10):
        response = client.get("/data/download/parquet")
        assert response.status_code == 200

    # 11th request should be rate-limited
    response = client.get("/data/download/parquet")
    assert response.status_code == 429
    assert response.json()["error_type"] == "RateLimitExceeded"

def _invalid_csv():
    """Helper: returns a CSV that always triggers ValidationError."""
    return b"bad_column\n123"


def test_circuit_breaker_opens(monkeypatch):
    """
    After 10 validation failures within 30 seconds,
    the circuit breaker should open and block /data/upload.
    """

    # Freeze time
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