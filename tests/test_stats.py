import math


def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_stats_without_upload_returns_user_error(client):
    resp = client.get("/data/stats")
    assert resp.status_code in (400, 422)
    body = resp.json()
    assert body["error_type"] in ("UserError", "ValidationError")


def test_stats_after_upload_returns_structure_and_etag(client):
    csv = "city,temp\nMalmo,10\nLund,12\n"
    files = {"file": ("weather.csv", _csv_bytes(csv), "text/csv")}
    upload = client.post("/data/upload", files=files)
    assert upload.status_code == 200

    resp = client.get("/data/stats")
    assert resp.status_code == 200

    body = resp.json()
    assert "stats" in body
    assert "_metadata" in body["stats"]
    meta = body["stats"]["_metadata"]
    assert meta["rows"] == 2
    assert meta["columns"] == 2

    # ETag ska finnas och vara citerad
    etag = resp.headers.get("ETag")
    assert etag is not None
    assert etag.startswith('"') and etag.endswith('"')

    # 304 när If-None-Match matchar
    resp2 = client.get("/data/stats", headers={"If-None-Match": etag})
    assert resp2.status_code == 304
