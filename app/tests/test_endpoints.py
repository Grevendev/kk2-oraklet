from fastapi.testclient import TestClient
from app.main import app
from app.state import state

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
    
EXPECTED_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "X-XSS-Protection": "1; mode=block",
}


def test_security_headers_on_health():
    """Ensure security headers are applied to the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    for header, expected_value in EXPECTED_HEADERS.items():
        assert header in response.headers
        assert response.headers[header] == expected_value


def test_security_headers_on_data_endpoint():
    """Ensure security headers are applied to a typical data endpoint."""
    response = client.get("/data/stats")  # returns ValidationError if no upload
    assert response.status_code in (200, 422, 400)

    for header, expected_value in EXPECTED_HEADERS.items():
        assert header in response.headers
        assert response.headers[header] == expected_value

def test_stats_returns_etag():
    """First stats request should return 200 and include an ETag header."""

    # Upload dataset
    csv = b"city,temp\nMalmo,10\nLund,12"
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert upload.status_code == 200

    # First stats call
    response = client.get("/data/stats")
    assert response.status_code == 200
    assert "ETag" in response.headers

    etag = response.headers["ETag"]
    assert etag.startswith('"') and etag.endswith('"')  # must be quoted


def test_stats_etag_not_modified():
    """Second stats request with matching If-None-Match should return 304."""

    # Upload dataset
    csv = b"city,temp\nMalmo,10\nLund,12"
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert upload.status_code == 200

    # First stats call
    first = client.get("/data/stats")
    assert first.status_code == 200
    etag = first.headers["ETag"]

    # Second call with If-None-Match
    second = client.get("/data/stats", headers={"If-None-Match": etag})
    assert second.status_code == 304
    assert second.content == b""  # no body allowed in 304


def test_stats_etag_changes_after_new_upload():
    """Uploading a new dataset should invalidate the old ETag."""

    # Upload dataset A
    csv_a = b"city,temp\nMalmo,10"
    upload_a = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv_a)}
    )
    assert upload_a.status_code == 200

    first = client.get("/data/stats")
    etag_a = first.headers["ETag"]

    # Upload dataset B (different)
    csv_b = b"city,temp\nMalmo,99"
    upload_b = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv_b)}
    )
    assert upload_b.status_code == 200

    second = client.get("/data/stats")
    etag_b = second.headers["ETag"]

    # ETag must change when dataset changes
    assert etag_a != etag_b

def test_schema_drift_no_change():
    """
    Uploading two CSVs with identical schema should NOT trigger schema drift.
    """

    # Reset state
    state.data_service._df = None
    state.data_service._schema_fingerprint = None

    csv1 = b"city,temp\nMalmo,10\nLund,12"
    csv2 = b"city,temp\nStockholm,15\nUppsala,14"

    # First upload
    r1 = client.post("/data/upload", files={"file": ("data.csv", csv1)})
    assert r1.status_code == 200

    old_fp = state.data_service._schema_fingerprint

    # Second upload with same schema
    r2 = client.post("/data/upload", files={"file": ("data.csv", csv2)})
    assert r2.status_code == 200

    new_fp = state.data_service._schema_fingerprint

    # Fingerprint must be identical
    assert old_fp == new_fp


def test_schema_drift_detected():
    """
    Uploading a CSV with a changed schema should trigger schema drift detection.
    Upload is still allowed by default.
    """

    # Reset state
    state.data_service._df = None
    state.data_service._schema_fingerprint = None

    csv1 = b"city,temp\nMalmo,10"
    csv2 = b"city,humidity\nMalmo,55"

    # First upload
    r1 = client.post("/data/upload", files={"file": ("data.csv", csv1)})
    assert r1.status_code == 200

    old_fp = state.data_service._schema_fingerprint

    # Second upload with changed schema
    r2 = client.post("/data/upload", files={"file": ("data.csv", csv2)})
    assert r2.status_code == 200

    new_fp = state.data_service._schema_fingerprint

    # Fingerprint must change
    assert old_fp != new_fp


def test_schema_drift_block_upload(monkeypatch):
    """
    If schema drift blocking is enabled, upload should return 400 UserError.
    """

    # Reset state
    state.data_service._df = None
    state.data_service._schema_fingerprint = None

    # Enable blocking via monkeypatch
    monkeypatch.setattr("app.chain.steps.LLMRunner.BLOCK_SCHEMA_DRIFT", True, raising=False)

    csv1 = b"city,temp\nMalmo,10"
    csv2 = b"city,humidity\nMalmo,55"

    # First upload
    r1 = client.post("/data/upload", files={"file": ("data.csv", csv1)})
    assert r1.status_code == 200

    # Second upload with changed schema → should be blocked
    r2 = client.post("/data/upload", files={"file": ("data.csv", csv2)})
    assert r2.status_code == 400
    assert r2.json()["error_type"] == "UserError"