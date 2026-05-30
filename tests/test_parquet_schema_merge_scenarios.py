# app/tests/test_parquet_schema_merge_scenarios.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
from fastapi.testclient import TestClient

from app.main import app
from app.state import state


client = TestClient(app)


def make_parquet(data: dict) -> bytes:
    table = pa.table(data)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()


def upload_parquet(data: dict):
    raw = make_parquet(data)
    files = {"file": ("test.parquet", raw, "application/octet-stream")}
    return client.post("/data/upload", files=files)


def test_parquet_schema_merge_superset(monkeypatch):
    """
    Superset-schema: baseline har färre kolumner, nytt schema har fler.
    Blocking=False → auto-merge ska ske.
    """

    state.reset()

    # Baseline
    res1 = upload_parquet({"city": ["Malmö"], "temp": [10]})
    assert res1.status_code == 200
    baseline_fp = state.schema_fingerprint

    # Tillåt merge
    monkeypatch.setattr(state, "schema_drift_blocking", False)

    # Superset-schema
    res2 = upload_parquet({"city": ["Lund"], "temp": [12], "humidity": [80]})
    assert res2.status_code == 200

    # Fingerprint ska ha uppdaterats
    assert state.schema_fingerprint != baseline_fp


def test_parquet_schema_merge_subset(monkeypatch):
    """
    Subset-schema: baseline har fler kolumner än nytt schema.
    Blocking=False → auto-merge ska ske.
    """

    state.reset()

    # Baseline
    res1 = upload_parquet({"city": ["Malmö"], "temp": [10], "humidity": [80]})
    assert res1.status_code == 200
    baseline_fp = state.schema_fingerprint

    monkeypatch.setattr(state, "schema_drift_blocking", False)

    # Subset-schema
    res2 = upload_parquet({"city": ["Lund"], "temp": [12]})
    assert res2.status_code == 200

    # Fingerprint ska ha uppdaterats
    assert state.schema_fingerprint != baseline_fp


def test_parquet_schema_merge_column_reorder(monkeypatch):
    """
    Kolumnordning ändras men schema är identiskt → ingen drift.
    """

    state.reset()

    res1 = upload_parquet({"city": ["Malmö"], "temp": [10]})
    assert res1.status_code == 200
    baseline_fp = state.schema_fingerprint

    # Samma kolumner, annan ordning
    res2 = upload_parquet({"temp": [12], "city": ["Lund"]})
    assert res2.status_code == 200

    # Fingerprint ska vara identiskt
    assert state.schema_fingerprint == baseline_fp


def test_parquet_schema_merge_type_change_blocked(monkeypatch):
    """
    Typändring → drift → blockeras när schema_drift_blocking=True.
    """

    state.reset()

    res1 = upload_parquet({"temp": [10, 12]})
    assert res1.status_code == 200
    baseline_fp = state.schema_fingerprint

    monkeypatch.setattr(state, "schema_drift_blocking", True)

    # Typändring: int → str
    res2 = upload_parquet({"temp": ["hej", "då"]})
    assert res2.status_code == 400
    assert "schema" in res2.text.lower() or "drift" in res2.text.lower()

    # Fingerprint ska INTE ändras
    assert state.schema_fingerprint == baseline_fp


def test_parquet_schema_merge_type_change_allowed(monkeypatch):
    """
    Typändring → drift → auto-merge när schema_drift_blocking=False.
    """

    state.reset()

    res1 = upload_parquet({"temp": [10, 12]})
    assert res1.status_code == 200
    baseline_fp = state.schema_fingerprint

    monkeypatch.setattr(state, "schema_drift_blocking", False)

    # Typändring: int → str
    res2 = upload_parquet({"temp": ["hej", "då"]})
    assert res2.status_code == 200

    # Fingerprint ska ha uppdaterats
    assert state.schema_fingerprint != baseline_fp
