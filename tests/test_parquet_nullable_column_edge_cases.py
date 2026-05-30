# app/tests/test_parquet_nullable_column_edge_cases.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def make_parquet(table: pa.Table) -> bytes:
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()


def upload_parquet_bytes(raw: bytes):
    files = {"file": ("test.parquet", raw, "application/octet-stream")}
    return client.post("/data/upload", files=files)


def test_all_null_column_rejected():
    # En kolumn som är 100% null → ska inte accepteras
    table = pa.table({"city": ["Malmö", "Lund"], "temp": [None, None]})
    raw = make_parquet(table)

    res = upload_parquet_bytes(raw)
    assert res.status_code == 422
    assert "null" in res.text.lower() or "empty" in res.text.lower()


def test_mixed_null_and_values_allowed_but_type_checked():
    # Null + värden → OK, men typ måste vara konsekvent
    table = pa.table({"temp": [10, None, 12]})
    raw = make_parquet(table)

    res = upload_parquet_bytes(raw)
    # Detta ska vara OK eftersom typen är konsekvent (int + null)
    assert res.status_code == 200


def test_null_causes_type_inference_conflict():
    # Arrow kan inferera fel typ om null dominerar → validatorn ska stoppa det
    arr = pa.array([None, None, "hej"], type=pa.string())
    table = pa.table({"col": arr})
    raw = make_parquet(table)

    res = upload_parquet_bytes(raw)
    assert res.status_code == 422
    assert "type" in res.text.lower()


def test_nested_list_with_nulls():
    # Nested lists med nulls → ska valideras korrekt
    list_array = pa.array([[1, 2], None, [3, 4]], type=pa.list_(pa.int64()))
    table = pa.table({"values": list_array})
    raw = make_parquet(table)

    res = upload_parquet_bytes(raw)
    # Detta ska vara OK eftersom typen är konsekvent
    assert res.status_code == 200


def test_explicit_nullable_schema_field():
    # Explicit schema med nullable kolumn
    schema = pa.schema(
        [
            pa.field("city", pa.string(), nullable=False),
            pa.field("temp", pa.int64(), nullable=True),
        ]
    )

    table = pa.Table.from_pydict(
        {"city": ["Malmö", "Lund"], "temp": [10, None]},
        schema=schema,
    )

    raw = make_parquet(table)
    res = upload_parquet_bytes(raw)

    # Detta ska vara OK eftersom schema är explicit och korrekt
    assert res.status_code == 200


def test_null_column_name_rejected():
    # Null som kolumnnamn → ska blockeras
    table = pa.table({None: [1, 2], "temp": [10, 12]})
    raw = make_parquet(table)

    res = upload_parquet_bytes(raw)
    assert res.status_code == 422
    assert "column" in res.text.lower()
