# app/tests/test_parquet_schema_drift.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
from fastapi.testclient import TestClient

from app.main import app
from app.state import state


client = TestClient(app)


def make_parquet(data: dict):
    table = pa.table(data)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()


def upload_parquet(data: dict):
    raw = make_parquet(data)
    files = {"file": ("test.parquet", raw, "application/octet-stream")}
    return client.post("/data/upload", files=files)


def test_parquet_schema_drift_detection(monkeypatch):
    """
    Verifierar att schema-drift upptäcks för Parquet-filer och att
    blocking fungerar korrekt.
    """

    # ---------------------------------------------------------
    # 1. Reset state
    # ---------------------------------------------------------
    state.reset()

    # ---------------------------------------------------------
    # 2. Ladda upp baseline Parquet-schema
    # ---------------------------------------------------------
    res1 = upload_parquet({"city": ["Malmö", "Lund"], "temp": [10, 12]})
    assert res1.status_code == 200

    baseline_fp = state.schema_fingerprint
    assert baseline_fp is not None

    # ---------------------------------------------------------
    # 3. Ladda upp identiskt schema → ingen drift
    # ---------------------------------------------------------
    res2 = upload_parquet({"city": ["Göteborg", "Uppsala"], "temp": [14, 11]})
    assert res2.status_code == 200
    assert state.schema_fingerprint == baseline_fp

    # ---------------------------------------------------------
    # 4. Aktivera schema-drift-blockering
    # ---------------------------------------------------------
    monkeypatch.setattr(state, "schema_drift_blocking", True)

    # ---------------------------------------------------------
    # 5. Ladda upp Parquet med NYTT schema → drift ska blockeras
    # ---------------------------------------------------------
    res3 = upload_parquet(
        {"city": ["Malmö", "Lund"], "temp": [10, 12], "humidity": [80, 75]}
    )

    assert res3.status_code == 400
    assert "schema" in res3.text.lower() or "drift" in res3.text.lower()

    # fingerprint ska INTE ha uppdaterats
    assert state.schema_fingerprint == baseline_fp
