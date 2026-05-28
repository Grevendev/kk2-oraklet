from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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
