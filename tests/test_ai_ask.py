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

def test_ai_ask_cache_hit(client):
    csv = "city,temp\nMalmo,10\nLund,12\n"
    files = {"file": ("weather.csv", csv.encode(), "text/csv")}
    client.post("/data/upload", files=files)

    # First request
    resp1 = client.post("/ai/ask", json={"question": "Hej"})
    etag1 = resp1.headers["ETag"]

    # Second request (same question, same stats)
    resp2 = client.post("/ai/ask", json={"question": "Hej"})
    etag2 = resp2.headers["ETag"]

    assert etag1 == etag2
    assert resp2.json() == resp1.json()

def test_ai_ask_cache_invalidated_after_new_upload(client):
    csv1 = "city,temp\nMalmo,10\n"
    csv2 = "city,temp\nLund,20\n"

    client.post("/data/upload", files={"file": ("a.csv", csv1.encode(), "text/csv")})
    resp1 = client.post("/ai/ask", json={"question": "Hej"})
    etag1 = resp1.headers["ETag"]

    client.post("/data/upload", files={"file": ("b.csv", csv2.encode(), "text/csv")})
    resp2 = client.post("/ai/ask", json={"question": "Hej"})
    etag2 = resp2.headers["ETag"]

    assert etag1 != etag2

def test_ai_ask_rejects_empty_question(client):
    csv = "city,temp\nMalmo,10\n"
    client.post("/data/upload", files={"file": ("a.csv", csv.encode(), "text/csv")})

    resp = client.post("/ai/ask", json={"question": "   "})
    assert resp.status_code == 400
    assert resp.json()["error_type"] == "UserError"

def test_ai_ask_pipeline_validation_error(client, monkeypatch):
    from app.errors import ValidationError

    def fake_error(question):
        raise ValidationError("Invalid question")

    monkeypatch.setattr("app.api.ai.pipeline.run", fake_error)

    csv = "city,temp\nMalmo,10\n"
    client.post("/data/upload", files={"file": ("a.csv", csv.encode(), "text/csv")})

    resp = client.post("/ai/ask", json={"question": "Hej"})
    assert resp.status_code == 400
    assert resp.json()["error_type"] == "UserError"
