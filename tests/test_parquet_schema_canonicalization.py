# app/tests/test_parquet_schema_canonicalization.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
import unicodedata
from fastapi.testclient import TestClient

from app.main import app
from app.state import state


client = TestClient(app)


def make_parquet(data: dict, schema: pa.Schema | None = None) -> bytes:
    table = pa.table(data, schema=schema) if schema else pa.table(data)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()


def upload_parquet_bytes(raw: bytes):
    files = {"file": ("test.parquet", raw, "application/octet-stream")}
    return client.post("/data/upload", files=files)


def upload_parquet(data: dict, schema: pa.Schema | None = None):
    return upload_parquet_bytes(make_parquet(data, schema))


def test_canonicalization_column_order_irrelevant():
    """
    Canonicalization ska sortera kolumner deterministiskt.
    """

    state.reset()

    res1 = upload_parquet({"b": [1], "a": [2]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    # Samma kolumner, annan ordning
    res2 = upload_parquet({"a": [3], "b": [4]})
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_canonicalization_type_equivalence():
    """
    int32 och int64 ska canonicaliseras till samma typ om backend definierar
    en canonical numeric type.
    """

    state.reset()

    schema1 = pa.schema([("value", pa.int32())])
    schema2 = pa.schema([("value", pa.int64())])

    res1 = upload_parquet({"value": [1, 2]}, schema=schema1)
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    res2 = upload_parquet({"value": [3, 4]}, schema=schema2)
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_canonicalization_unicode_equivalence():
    """
    Unicode canonicalization: NFC vs NFD ska ge samma canonical schema.
    """

    state.reset()

    col1 = "temp"
    col2 = unicodedata.normalize("NFD", "temp")

    res1 = upload_parquet({col1: [10]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    res2 = upload_parquet({col2: [12]})
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_canonicalization_nullability_equivalence():
    """
    nullable=True vs nullable=False ska canonicaliseras om backend definierar
    en canonical nullability policy.
    """

    state.reset()

    schema1 = pa.schema([pa.field("temp", pa.int64(), nullable=True)])
    schema2 = pa.schema([pa.field("temp", pa.int64(), nullable=False)])

    res1 = upload_parquet({"temp": [10]}, schema=schema1)
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    res2 = upload_parquet({"temp": [12]}, schema=schema2)
    assert res2.status_code == 200

    assert state.schema_fingerprint == fp1


def test_canonicalization_detects_true_semantic_difference():
    """
    Canonicalization ska INTE maskera äkta semantiska skillnader.
    Ex: int64 vs string.
    """

    state.reset()

    res1 = upload_parquet({"temp": [10]})
    assert res1.status_code == 200
    fp1 = state.schema_fingerprint

    # Äkta typkonflikt
    res2 = upload_parquet({"temp": ["hej"]})
    assert res2.status_code == 400
    assert "schema" in res2.text.lower() or "canonical" in res2.text.lower()

    assert state.schema_fingerprint == fp1
