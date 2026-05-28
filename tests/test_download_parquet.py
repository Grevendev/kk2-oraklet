def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_download_parquet_without_upload_returns_validation_error(client):
    resp = client.get("/data/download/parquet")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_type"] == "ValidationError"


def test_download_parquet_after_upload(client):
    csv = "city,temp\nMalmo,10\nLund,12\n"
    files = {"file": ("weather.csv", _csv_bytes(csv), "text/csv")}
    upload = client.post("/data/upload", files=files)
    assert upload.status_code == 200

    resp = client.get("/data/download/parquet")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("application/octet-stream")
    assert "attachment; filename=dataset.parquet" in resp.headers["Content-Disposition"]
    assert len(resp.content) > 0
