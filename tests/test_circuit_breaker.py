import time
import app.main as main_module


def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_circuit_breaker_opens_after_repeated_validation_errors(client, monkeypatch):
    # Gör tröskeln lägre i test för att slippa 10+ requests
    monkeypatch.setattr(main_module, "MAX_FAILURES", 3, raising=False)
    monkeypatch.setattr(main_module, "VALIDATION_WINDOW", 5, raising=False)
    monkeypatch.setattr(main_module, "CIRCUIT_DURATION", 5, raising=False)

    # Skicka ogiltiga uploads (fel filtyp)
    for _ in range(3):
        files = {"file": ("data.txt", _csv_bytes("not,csv\n1,2\n"), "text/plain")}
        resp = client.post("/data/upload", files=files)
        assert resp.status_code == 422

    # Nu ska circuit breaker vara öppen
    files = {"file": ("data.txt", _csv_bytes("not,csv\n1,2\n"), "text/plain")}
    resp_blocked = client.post("/data/upload", files=files)
    assert resp_blocked.status_code == 503
    body = resp_blocked.json()
    assert body["error_type"] == "CircuitBreakerOpen"

    # Vänta tills den stänger igen
    time.sleep(5)
    files_ok = {"file": ("data.csv", _csv_bytes("a,b\n1,2\n"), "text/csv")}
    resp_ok = client.post("/data/upload", files=files_ok)
    assert resp_ok.status_code == 200
