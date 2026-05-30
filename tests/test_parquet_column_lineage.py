# app/tests/test_parquet_column_lineage.py

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


def test_column_lineage_initialization():
    """
    Första uploaden ska skapa lineage-fingerprint per kolumn.
    """

    state.reset()

    res = upload_parquet({"city": ["Malmö"], "temp": [10]})
    assert res.status_code == 200

    assert "city" in state.column_lineage
    assert "temp" in state.column_lineage

    assert state.column_lineage["city"] is not None
    assert state.column_lineage["temp"] is not None


def test_column_lineage_stable_when_types_match():
    """
    Samma kolumner och samma typer → lineage ska vara stabil.
    """

    state.reset()

    upload_parquet({"city": ["Malmö"], "temp": [10]})
    fp1_city = state.column_lineage["city"]
    fp1_temp = state.column_lineage["temp"]

    res = upload_parquet({"city": ["Lund"], "temp": [12]})
    assert res.status_code == 200

    assert state.column_lineage["city"] == fp1_city
    assert state.column_lineage["temp"] == fp1_temp


def test_column_lineage_detects_type_change(monkeypatch):
    """
    Typändring i en kolumn → lineage-brott → blockeras om blocking=True.
    """

    state.reset()

    upload_parquet({"temp": [10, 12]})
    fp1 = state.column_lineage["temp"]

    monkeypatch.setattr(state, "schema_drift_blocking", True)

    # Typändring: int → str
    res = upload_parquet({"temp": ["hej", "då"]})
    assert res.status_code == 400
    assert "lineage" in res.text.lower() or "schema" in res.text.lower()

    # Fingerprint ska INTE ändras
    assert state.column_lineage["temp"] == fp1


def test_column_lineage_type_change_allowed(monkeypatch):
    """
    Typändring → lineage-brott → tillåts om blocking=False.
    """

    state.reset()

    upload_parquet({"temp": [10, 12]})
    fp1 = state.column_lineage["temp"]

    monkeypatch.setattr(state, "schema_drift_blocking", False)

    res = upload_parquet({"temp": ["hej", "då"]})
    assert res.status_code == 200

    # Fingerprint ska ha uppdaterats
    assert state.column_lineage["temp"] != fp1


def test_column_lineage_new_column(monkeypatch):
    """
    Ny kolumn → lineage ska skapas för den kolumnen.
    """

    state.reset()

    upload_parquet({"city": ["Malmö"], "temp": [10]})
    assert "humidity" not in state.column_lineage

    monkeypatch.setattr(state, "schema_drift_blocking", False)

    res = upload_parquet({"city": ["Lund"], "temp": [12], "humidity": [80]})
    assert res.status_code == 200

    assert "humidity" in state.column_lineage
    assert state.column_lineage["humidity"] is not None


def test_column_lineage_missing_column(monkeypatch):
    """
    En kolumn försvinner → lineage-brott → blockeras om blocking=True.
    """

    state.reset()

    upload_parquet({"city": ["Malmö"], "temp": [10]})
    fp_city = state.column_lineage["city"]
    fp_temp = state.column_lineage["temp"]

    monkeypatch.setattr(state, "schema_drift_blocking", True)

    # temp saknas → lineage-brott
    res = upload_parquet({"city": ["Lund"]})
    assert res.status_code == 400
    assert "lineage" in res.text.lower() or "schema" in res.text.lower()

    # Fingerprints ska vara oförändrade
    assert state.column_lineage["city"] == fp_city
    assert state.column_lineage["temp"] == fp_temp
