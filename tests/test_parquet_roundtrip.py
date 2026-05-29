# app/tests/test_parquet_roundtrip.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import io
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def make_parquet_bytes(data: dict) -> bytes:
    table = pa.table(data)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()


def test_parquet_roundtrip_consistency():
    """
    Verifierar att Parquet → upload → download → Parquet → CSV → DataFrame
    är 100% lossless.
    """

    # ---------------------------------------------------------
    # 1. Skapa original Parquet-data
    # ---------------------------------------------------------
    original_data = {
        "city": ["Malmö", "Lund", "Göteborg"],
        "temp": [10, 12, 14],
        "humidity": [80, 75, 70],
    }

    parquet_bytes = make_parquet_bytes(original_data)

    # ---------------------------------------------------------
    # 2. Upload Parquet
    # ---------------------------------------------------------
    files = {"file": ("data.parquet", parquet_bytes, "application/octet-stream")}
    upload_res = client.post("/data/upload", files=files)
    assert upload_res.status_code == 200

    # ---------------------------------------------------------
    # 3. Download Parquet
    # ---------------------------------------------------------
    dl = client.get("/data/download/parquet")
    assert dl.status_code == 200
    assert dl.headers["content-type"] == "application/octet-stream"

    downloaded_parquet = dl.content

    # ---------------------------------------------------------
    # 4. Läs nedladdad Parquet → DataFrame
    # ---------------------------------------------------------
    table = pq.read_table(io.BytesIO(downloaded_parquet))
    df_parquet = table.to_pandas()

    # ---------------------------------------------------------
    # 5. Läs original Parquet → DataFrame
    # ---------------------------------------------------------
    df_original = pq.read_table(io.BytesIO(parquet_bytes)).to_pandas()

    # ---------------------------------------------------------
    # 6. Jämför DataFrames (frame-for-frame)
    # ---------------------------------------------------------
    assert df_original.equals(df_parquet)

    # ---------------------------------------------------------
    # 7. Round-trip: Parquet → CSV → DataFrame
    # ---------------------------------------------------------
    csv_bytes = df_parquet.to_csv(index=False).encode("utf-8")
    df_roundtrip = pd.read_csv(io.BytesIO(csv_bytes))

    # ---------------------------------------------------------
    # 8. Jämför CSV-roundtrip med original
    # ---------------------------------------------------------
    assert df_original.equals(df_roundtrip)
