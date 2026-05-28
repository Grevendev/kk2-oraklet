def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_ai_stream_requires_dataset(client):
    resp = client.post("/ai/ask/stream", json={"question": "Hej"})
    assert resp.status_code == 400
    assert resp.json()["error_type"] == "UserError"


def test_ai_stream_returns_chunks(client):
    csv = "city,temp\nMalmo,10\nLund,12\n"
    files = {"file": ("weather.csv", _csv_bytes(csv), "text/csv")}
    client.post("/data/upload", files=files)

    resp = client.post("/ai/ask/stream", json={"question": "Hej"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")

    chunks = b"".join(resp.iter_bytes())
    assert b"Detta \xc3\xa4r ett mockat AI" in chunks

def test_ai_stream_uses_cache(client):
    csv = "city,temp\nMalmo,10\n"
    client.post("/data/upload", files={"file": ("a.csv", csv.encode(), "text/csv")})

    # First call (cache miss)
    resp1 = client.post("/ai/ask/stream", json={"question": "Hej"})
    chunks1 = b"".join(resp1.iter_bytes())

    # Second call (cache hit)
    resp2 = client.post("/ai/ask/stream", json={"question": "Hej"})
    chunks2 = b"".join(resp2.iter_bytes())

    assert chunks1 == chunks2
