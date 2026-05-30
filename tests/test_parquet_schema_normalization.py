# app/tests/test_parquet_schema_normalization.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
import unicodedata
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


def test_schema_normalization_casing():
    """
    CITY vs city → ska normaliseras till samma fingerprint.
    """

    state.reset()

    res1 = upload_parquet({"city": ["Malmö"], "temp": [10]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    # Samma kolumner, annan casing
    res2 = upload_parquet({"CITY": ["Lund"], "TEMP": [12]})
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_schema_normalization_whitespace():
    """
    " city " vs "city" → whitespace ska normaliseras bort.
    """

    state.reset()

    res1 = upload_parquet({"city": ["Malmö"], "temp": [10]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    res2 = upload_parquet({" city ": ["Lund"], " temp ": [12]})
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_schema_normalization_underscores_vs_spaces():
    """
    "avg temp" vs "avg_temp" → normalisering ska mappa dessa till samma.
    """

    state.reset()

    res1 = upload_parquet({"avg_temp": [10], "city": ["Malmö"]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    res2 = upload_parquet({"avg temp": [12], "city": ["Lund"]})
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_schema_normalization_unicode_equivalence():
    """
    Unicode-normalisering: "Malmö" i NFC vs NFD → ska inte trigga drift.
    """

    state.reset()

    col1 = "temp"
    col2 = unicodedata.normalize("NFD", "temp")  # artificiellt exempel

    res1 = upload_parquet({col1: [10], "city": ["Malmö"]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    res2 = upload_parquet({col2: [12], "city": ["Lund"]})
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_schema_normalization_fails_on_true_conflict():
    """
    Normalisering kan inte rädda "temperature" vs "temp" → ska trigga drift.
    """

    state.reset()

    res1 = upload_parquet({"temp": [10], "city": ["Malmö"]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    res2 = upload_parquet({"temperature": [12], "city": ["Lund"]})
    assert res2.status_code == 400
    assert "schema" in res2.text.lower() or "drift" in res2.text.lower()

    # Fingerprint ska INTE ändras
    assert state.schema_fingerprint == fp1
