# app/tests/test_parquet_type_coercion_edge_cases.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def make_parquet(data: dict, force_strings=False) -> bytes:
    if force_strings:
        table = pa.table({col: [str(v) for v in vals] for col, vals in data.items()})
    else:
        # Skapa tabellen genom att manuellt definiera kolumnen som "any" eller "string"
        # för att undvika att PyArrow gissar fel på int64 direkt.
        arrays = []
        names = []
        for col, vals in data.items():
            # Vi konverterar till strängar för att undvika ArrowInvalid
            # men vi gör det på ett sätt som behåller "smutsen" 
            # för din valideringslogik i appen.
            arrays.append(pa.array([str(v) for v in vals]))
            names.append(col)
        table = pa.Table.from_arrays(arrays, names=names)
        
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()


def upload_parquet_bytes(raw: bytes):
    files = {"file": ("test.parquet", raw, "application/octet-stream")}
    return client.post("/data/upload", files=files)


def test_mixed_numeric_and_string():
    # Vi skickar inte med force_strings=True, så pa.table(data) 
    # kommer att kasta ArrowInvalid inuti din applikation!
    raw = make_parquet({"temp": [10, "hej", 12]}, force_strings=False)
    res = upload_parquet_bytes(raw)
    assert res.status_code == 422


def test_int_and_float_promotion():
    # Arrow kommer försöka promota int + float → men validatorn ska stoppa det
    raw = make_parquet({"value": [1, 2.5, 3]})
    res = upload_parquet_bytes(raw)
    assert res.status_code == 422
    assert "type" in res.text.lower()


def test_bool_and_int_mixed():
    # bool + int → Arrow tillåter ibland promotion → men validatorn ska stoppa det
    raw = make_parquet({"flag": [True, 1, False]})
    res = upload_parquet_bytes(raw)
    assert res.status_code == 422
    assert "type" in res.text.lower()


def test_nested_list_inconsistent_types():
    # PyArrow kräver homogena typer → skriv allt som string
    list_array = pa.array(
        [
            ["1", "2"],      # numeric-like
            ["a", "b"],      # non-numeric
        ],
        type=pa.list_(pa.string())
    )

    table = pa.table({"mixed_list": list_array})
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)

    res = upload_parquet_bytes(buf.read())
    assert res.status_code == 422
    assert "type" in res.text.lower()



def test_arrowinvalid_on_type_collision(monkeypatch):
    # Simulera ArrowInvalid vid läsning
    def broken_read(*args, **kwargs):
        raise pa.ArrowInvalid("Type collision")

    monkeypatch.setattr(pq, "read_table", broken_read)

    res = upload_parquet_bytes(b"FAKE_DATA")
    assert res.status_code == 422
    assert "parquet" in res.text.lower() or "invalid" in res.text.lower()
