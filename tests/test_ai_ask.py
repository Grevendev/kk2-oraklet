def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_ai_ask_requires_dataset(client):
    resp = client.post("/ai/ask", json={"question": "Hej"})
    assert resp.status_code == 400
    assert resp.json()["error_type"] == "UserError"


def test_ai_ask_returns_mocked_response(client):
    csv = "city,temp\nMalmo,10\nLund,12\n"
    files = {"file": ("weather.csv", _csv_bytes(csv), "text/csv")}
    client.post("/data/upload", files=files)

    resp = client.post("/ai/ask", json={"question": "Vad är medeltemperaturen?"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["question"] == "Vad är medeltemperaturen?"
    assert body["answer"] == "Detta är ett mockat AI‑svar."
    assert body["reasoning"] == "Mockad reasoning."
    assert "stats_used" in body

    assert "ETag" in resp.headers


def test_ai_ask_etag_304(client):
    csv = "city,temp\nMalmo,10\nLund,12\n"
    files = {"file": ("weather.csv", _csv_bytes(csv), "text/csv")}
    client.post("/data/upload", files=files)

    resp1 = client.post("/ai/ask", json={"question": "Hej"})
    etag = resp1.headers["ETag"]

    resp2 = client.post("/ai/ask", json={"question": "Hej"}, headers={"If-None-Match": etag})
    assert resp2.status_code == 304
