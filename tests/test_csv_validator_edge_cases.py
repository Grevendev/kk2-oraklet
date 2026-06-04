# app/tests/test_csv_validator_edge_cases.py

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def upload(csv: str):
    files = {"file": ("test.csv", csv, "text/csv")}
    return client.post("/data/upload", files=files)


def test_whitespace_column_names():
    res = upload("   ,temp\nA,10\nB,12\n")
    assert res.status_code == 422
    assert "column" in res.text.lower()


def test_empty_column_name():
    res = upload(",temp\nA,10\nB,12\n")
    assert res.status_code == 422
    assert "column" in res.text.lower()


def test_nan_column_name():
    res = upload("NaN,temp\nA,10\nB,12\n")
    assert res.status_code == 422
    assert "column" in res.text.lower()


def test_duplicate_columns():
    res = upload("city,city\nA,B\nC,D\n")
    assert res.status_code == 422
    assert "duplicate" in res.text.lower()


def test_unknown_columns():
    res = upload("city,temp,unknown_col\nA,10,x\nB,12,y\n")
    assert res.status_code == 200
    # Verifiera att den okända kolumnen faktiskt har processats och finns med i svaret
    assert "unknown_col" in res.json()["columns"]


def test_too_many_columns():
    cols = ",".join([f"c{i}" for i in range(60)])
    row = ",".join(["1"] * 60)
    res = upload(f"{cols}\n{row}\n")
    assert res.status_code == 422
    assert "too many" in res.text.lower() or "exceed" in res.text.lower()


def test_mixed_datatypes_in_column():
    res = upload("city,temp\nA,10\nB,hej\n")
    assert res.status_code == 422
    assert "type" in res.text.lower()


def test_invalid_datatype():
    res = upload("city,temp\nA,not_a_number\nB,12\n")
    assert res.status_code == 422
    assert "number" in res.text.lower()
