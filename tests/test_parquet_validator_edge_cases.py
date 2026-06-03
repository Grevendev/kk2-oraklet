# app/tests/test_parquet_validator_edge_cases.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def upload_parquet(table: pa.Table):
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    files = {"file": ("test.parquet", buf.read(), "application/octet-stream")}
    return client.post("/data/upload", files=files)


def upload_raw(data: bytes, mime="application/octet-stream"):
    files = {"file": ("test.parquet", data, mime)}
    return client.post("/data/upload", files=files)


def test_invalid_parquet_magic_bytes():
    res = upload_raw(b"NOT_A_PARQUET_FILE")
    assert res.status_code == 422
    assert "parquet" in res.text.lower() or "invalid" in res.text.lower()


def test_wrong_mime_type():
    table = pa.table({"city": ["A"], "temp": [10]})
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)

    res = upload_raw(buf.read(), mime="text/plain")
    assert res.status_code == 422
    assert "mime" in res.text.lower() or "parquet" in res.text.lower()


def test_duplicate_columns():
    table = pa.table({"city": ["A"], "city": ["B"]})
    res = upload_parquet(table)
    assert res.status_code == 422
    assert "duplicate" in res.text.lower()


def test_empty_column_name():
    table = pa.table({"": ["A"], "temp": [10]})
    res = upload_parquet(table)
    assert res.status_code == 422
    assert "column" in res.text.lower()



@pytest.mark.xfail(reason="PyArrow kan inte skriva Parquet med mixed datatyper i en kolumn.")
def test_mixed_datatypes_in_column():
    table = pa.table({"temp": [10, "hej"]})
    res = upload_parquet(table)
    assert res.status_code == 422
    assert "type" in res.text.lower()




def test_unreadable_parquet_arrowinvalid(monkeypatch):
    def broken_read(*args, **kwargs):
        raise pa.ArrowInvalid("Corrupted parquet")

    monkeypatch.setattr(pq, "read_table", broken_read)

    res = upload_raw(b"FAKE_DATA")
    assert res.status_code == 422
    assert "parquet" in res.text.lower() or "invalid" in res.text.lower()
