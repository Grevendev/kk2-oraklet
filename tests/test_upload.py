import io
import pytest
from app.data import data_service


def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_upload_valid_csv(client):
    csv = "city,temp\nMalmo,10\nLund,12\n"
    files = {"file": ("weather.csv", _csv_bytes(csv), "text/csv")}

    resp = client.post("/data/upload", files=files)
    assert resp.status_code == 200

    body = resp.json()
    assert body["rows"] == 2
    assert body["columns"] == ["city", "temp"]
    assert "temp" in body["dtypes"]


def test_upload_rejects_non_csv_extension(client):
    files = {"file": ("data.txt", _csv_bytes("a,b\n1,2\n"), "text/plain")}
    resp = client.post("/data/upload", files=files)
    assert resp.status_code == 422
    assert resp.json()["error_type"] == "ValidationError"


def test_upload_empty_csv_raises_validation_error(client):
    files = {"file": ("empty.csv", _csv_bytes(""), "text/csv")}
    resp = client.post("/data/upload", files=files)
    assert resp.status_code == 422
    assert resp.json()["error_type"] == "ValidationError"
