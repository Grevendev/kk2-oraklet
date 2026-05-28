def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_schema_drift_detected_on_second_upload(client):
    csv1 = "city,temp\nMalmo,10\nLund,12\n"
    csv2 = "city,humidity\nMalmo,80\nLund,75\n"

    files1 = {"file": ("weather1.csv", _csv_bytes(csv1), "text/csv")}
    files2 = {"file": ("weather2.csv", _csv_bytes(csv2), "text/csv")}

    resp1 = client.post("/data/upload", files=files1)
    assert resp1.status_code == 200

    resp2 = client.post("/data/upload", files=files2)
    assert resp2.status_code == 400
    body = resp2.json()
    assert body["error_type"] == "UserError"
