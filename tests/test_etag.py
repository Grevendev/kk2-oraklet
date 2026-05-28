from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================
# ETag Tests for /data/stats
# ============================================================

def test_stats_returns_etag():
    """First stats request should return 200 and include an ETag header."""

    # Upload dataset
    csv = b"city,temp\nMalmo,10\nLund,12"
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert upload.status_code == 200

    # First stats call
    response = client.get("/data/stats")
    assert response.status_code == 200
    assert "ETag" in response.headers

    etag = response.headers["ETag"]
    assert etag.startswith('"') and etag.endswith('"')  # must be quoted


def test_stats_etag_not_modified():
    """Second stats request with matching If-None-Match should return 304."""

    # Upload dataset
    csv = b"city,temp\nMalmo,10\nLund,12"
    upload = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv)}
    )
    assert upload.status_code == 200

    # First stats call
    first = client.get("/data/stats")
    assert first.status_code == 200
    etag = first.headers["ETag"]

    # Second call with If-None-Match
    second = client.get("/data/stats", headers={"If-None-Match": etag})
    assert second.status_code == 304
    assert second.content == b""  # no body allowed in 304


def test_stats_etag_changes_after_new_upload():
    """Uploading a new dataset should invalidate the old ETag."""

    # Upload dataset A
    csv_a = b"city,temp\nMalmo,10"
    upload_a = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv_a)}
    )
    assert upload_a.status_code == 200

    first = client.get("/data/stats")
    etag_a = first.headers["ETag"]

    # Upload dataset B (different)
    csv_b = b"city,temp\nMalmo,99"
    upload_b = client.post(
        "/data/upload",
        files={"file": ("data.csv", csv_b)}
    )
    assert upload_b.status_code == 200

    second = client.get("/data/stats")
    etag_b = second.headers["ETag"]

    # ETag must change when dataset changes
    assert etag_a != etag_b
