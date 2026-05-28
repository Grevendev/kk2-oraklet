import io
import pandas as pd
import pyarrow.parquet as pq
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================
# Basic Endpoint Tests
# ============================================================

def test_health():
    """Ensure the health endpoint returns OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ============================================================
# Upload Endpoint Tests
# ============================================================

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


def test_validation_error_for_empty_csv():
    """Uploading an empty CSV should return 422 ValidationError."""
    response = client.post(
        "/data/upload",
        files={"file": ("empty.csv", b"")}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


# ============================================================
# Stats Endpoint Tests
# ============================================================

def test_user_error_for_stats_without_upload():
    """Requesting stats without uploading should return 422 ValidationError."""
    response = client.get("/data/stats")
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_error_model_structure():
    """Ensure error responses follow the standardized ErrorResponse model."""
    response = client.get("/data/stats")  # no dataset uploaded
    assert response.status_code == 422

    body = response.json()
    assert "error_type" in body
    assert "message" in body
    assert "details" in body


# ============================================================
# Download Endpoint Tests
# ============================================================

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

ENDPOINTS = [
    "/data/upload",
    "/data/stats",
    "/data/download/csv",
    "/data/download/parquet",
]


def test_error_model_consistency():
    """
    Ensure all endpoints return the standardized ErrorResponse model
    when triggered with invalid input.
    """

    for endpoint in ENDPOINTS:
        if endpoint == "/data/upload":
            response = client.post(endpoint, files={"file": ("bad.txt", b"hello")})
        else:
            response = client.get(endpoint)

        assert response.status_code in (400, 422)
        body = response.json()

        assert "error_type" in body
        assert "message" in body
        assert "details" in body

def test_stats_structure_is_correct():
    """
    Ensure /data/stats returns a well-structured stats object
    with expected keys and numeric values.
    """

    csv = b"city,temp\nMalmo,10\nLund,20"
    upload = client.post("/data/upload", files={"file": ("data.csv", csv)})
    assert upload.status_code == 200

    response = client.get("/data/stats")
    assert response.status_code == 200

    body = response.json()
    assert "stats" in body

    stats = body["stats"]
    assert "temp" in stats

    temp_stats = stats["temp"]

    # Expected keys
    for key in ("mean", "min", "max", "std", "count"):
        assert key in temp_stats
        assert isinstance(temp_stats[key], (int, float))