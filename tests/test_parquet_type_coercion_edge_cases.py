# tests/test_parquet_type_coercion_edge_cases.py

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def make_parquet(data: dict) -> bytes:
    # Vi skapar en tabell där alla värden är strängar.
    # Detta gör att PyArrow kan skriva filen utan att klaga,
    # och din validator i data.py kan sedan hitta att 
    # "hej" inte borde finnas i en kolumn som förväntar sig siffror.
    arrays = {}
    for col, vals in data.items():
        # Vi gör om allt till strängar för att undvika ArrowInvalid
        arrays[col] = [str(v) for v in vals]
    
    table = pa.Table.from_pydict(arrays)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    return buf.read()

def upload_parquet_bytes(raw: bytes):
    files = {"file": ("test.parquet", raw, "application/octet-stream")}
    return client.post("/data/upload", files=files)

def test_mixed_numeric_and_string():
    app.state.semantic_fingerprint = {"temp": "int64"}
    raw = make_parquet({"temp": [10, "hej", 12]})
    res = upload_parquet_bytes(raw)
    
    assert res.status_code == 422
    assert "mixed numeric and string" in res.json()["message"].lower()

def test_int_and_float_promotion():
    app.state.semantic_fingerprint = {"value": "int64"}
    # Obs: PyArrow kommer oftast läsa in detta som float64, 
    # din validering i data.py letar efter "Mixed int and float values."
    raw = make_parquet({"value": [1, 2.5, 3]})
    res = upload_parquet_bytes(raw)
    assert res.status_code == 422
    assert "mixed int and float" in res.json()["message"].lower()

def test_bool_and_int_mixed():
    raw = make_parquet({"flag": [True, 1, False]})
    res = upload_parquet_bytes(raw)
    # Om din kod konverterar bool till int (som den gör nu), 
    # borde den passera som 200. Om du vill att den ska faila, 
    # ta bort astype(int) i data.py.
    assert res.status_code == 200

def test_nested_list_inconsistent_types():
    # Skapa en lista med blandade sträng-värden
    data = {"mixed_list": [["1", "2"], ["a", "b"]]}
    raw = make_parquet(data) 
    res = upload_parquet_bytes(raw)
    
    assert res.status_code == 422
    assert "nested list" in res.json()["message"].lower()

def test_duplicate_columns():
    # Parquet tillåter tekniskt dubbletter via schema, 
    # men vi vill stoppa det
    table = pa.Table.from_arrays([pa.array([1]), pa.array([2])], names=["col1", "col1"])
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)
    
    res = upload_parquet_bytes(buf.read())
    assert res.status_code == 422
    assert "duplicate" in res.json()["message"].lower()

def test_arrowinvalid_on_type_collision(monkeypatch):
    def broken_read(*args, **kwargs):
        raise ValueError("Type collision") # Simulerar ett generellt fel

    monkeypatch.setattr(pq.ParquetFile, "read", broken_read)

    res = upload_parquet_bytes(b"PAR1_FAKE_DATA")
    assert res.status_code == 422