import io
import pandas as pd
import pyarrow.parquet as pq
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================
# CSV Content Test
# ============================================================

def test_download_csv_content_matches_uploaded():
    """Ensure that /data/download/csv returns the exact same CSV content."""

    original_csv = b"city,temp\nMalmo,10\nLund,12"

    # Upload dataset
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", original_csv)}
    )
    assert upload.status_code == 200

    # Download CSV
    response = client.get("/data/download/csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    downloaded_csv = response.content

    # Compare byte-for-byte
    assert downloaded_csv == original_csv


# ============================================================
# Parquet Content Test
# ============================================================

def test_download_parquet_content_matches_uploaded():
    """
    Ensure that /data/download/parquet returns a valid Parquet file
    that matches the uploaded CSV content exactly.
    """

    original_csv = b"city,temp\nMalmo,10\nLund,12"

    # Upload dataset
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", original_csv)}
    )
    assert upload.status_code == 200

    # Download Parquet
    response = client.get("/data/download/parquet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"

    parquet_bytes = response.content

    # Read Parquet into DataFrame
    table = pq.read_table(io.BytesIO(parquet_bytes))
    df_parquet = table.to_pandas()

    # Read original CSV into DataFrame
    df_original = pd.read_csv(io.BytesIO(original_csv))

    # Compare DataFrames
    assert df_original.equals(df_parquet)


# ============================================================
# Round-trip Test: CSV → Parquet → CSV
# ============================================================

def test_roundtrip_csv_parquet_csv():
    """Upload CSV → download Parquet → convert back to CSV → compare."""

    original_csv = b"city,temp\nMalmo,10\nLund,12"

    # Upload dataset
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", original_csv)}
    )
    assert upload.status_code == 200

    # Download Parquet
    parquet_resp = client.get("/data/download/parquet")
    assert parquet_resp.status_code == 200

    # Convert Parquet → DataFrame
    table = pq.read_table(io.BytesIO(parquet_resp.content))
    df_parquet = table.to_pandas()

    # Convert DataFrame → CSV
    csv_roundtrip = df_parquet.to_csv(index=False).encode("utf-8")

    # Compare with original CSV
    assert csv_roundtrip == original_csv

def test_csv_download_has_correct_headers():
    """
    Ensure CSV download endpoint returns correct Content-Disposition header.
    """

    csv = b"city,temp\nMalmo,10"
    upload = client.post("/data/upload", files={"file": ("data.csv", csv)})
    assert upload.status_code == 200

    response = client.get("/data/download/csv")
    assert response.status_code == 200

    assert "Content-Disposition" in response.headers
    assert response.headers["Content-Disposition"] == "attachment; filename=dataset.csv"