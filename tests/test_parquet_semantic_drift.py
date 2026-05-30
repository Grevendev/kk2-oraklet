# app/tests/test_parquet_semantic_drift.py

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


def test_semantic_drift_value_domain_change(monkeypatch):
    """
    temp går från numerisk temperatur → kategoriska etiketter.
    Typen är densamma (string), men semantiken ändras → semantic drift.
    """

    state.reset()

    # Baseline: kategoriska temperaturer i °C
    res1 = upload_parquet({"temp": ["10", "12", "14"]})
    assert res1.status_code == 200
    fp1 = state.semantic_fingerprint["temp"]

    monkeypatch.setattr(state, "semantic_drift_blocking", True)

    # Semantic drift: temp blir kategorier
    res2 = upload_parquet({"temp": ["low", "medium", "high"]})
    assert res2.status_code == 400
    assert "semantic" in res2.text.lower()

    assert state.semantic_fingerprint["temp"] == fp1


def test_semantic_drift_numeric_to_categorical(monkeypatch):
    """
    Kolumn går från numerisk → kategorisk trots samma typ (string).
    """

    state.reset()

    res1 = upload_parquet({"status": ["1", "2", "3"]})
    assert res1.status_code == 200
    fp1 = state.semantic_fingerprint["status"]

    monkeypatch.setattr(state, "semantic_drift_blocking", True)

    # Semantic drift: numeriska etiketter → kategoriska labels
    res2 = upload_parquet({"status": ["ok", "fail", "ok"]})
    assert res2.status_code == 400
    assert "semantic" in res2.text.lower()

    assert state.semantic_fingerprint["status"] == fp1


def test_semantic_drift_continuous_to_discrete(monkeypatch):
    """
    Kolumn går från kontinuerlig → diskret distribution.
    """

    state.reset()

    # Kontinuerlig baseline
    res1 = upload_parquet({"value": [1.1, 1.2, 1.3, 1.4]})
    assert res1.status_code == 200
    fp1 = state.semantic_fingerprint["value"]

    monkeypatch.setattr(state, "semantic_drift_blocking", True)

    # Diskret distribution
    res2 = upload_parquet({"value": [1.0, 2.0, 3.0, 1.0]})
    assert res2.status_code == 400
    assert "semantic" in res2.text.lower()

    assert state.semantic_fingerprint["value"] == fp1


def test_semantic_drift_allowed_when_blocking_disabled(monkeypatch):
    """
    Semantic drift tillåts när semantic_drift_blocking=False.
    """

    state.reset()

    res1 = upload_parquet({"temp": ["10", "12", "14"]})
    assert res1.status_code == 200
    fp1 = state.semantic_fingerprint["temp"]

    monkeypatch.setattr(state, "semantic_drift_blocking", False)

    # Semantic drift: numeriska → kategoriska
    res2 = upload_parquet({"temp": ["low", "medium", "high"]})
    assert res2.status_code == 200

    assert state.semantic_fingerprint["temp"] != fp1
