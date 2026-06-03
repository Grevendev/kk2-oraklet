import time
import app.main as main_module


def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_circuit_breaker_opens_after_repeated_validation_errors(client, monkeypatch):
    # Sänk tröskeln för GLOBAL_CIRCUIT_BREAKER
    monkeypatch.setattr(main_module.GLOBAL_CIRCUIT_BREAKER, "max_failures", 3, raising=False)
    monkeypatch.setattr(main_module.GLOBAL_CIRCUIT_BREAKER, "reset_timeout", 5, raising=False)

    # Skicka ogiltiga uploads (fel filtyp)
    for _ in range(3):
        files = {"file": ("data.txt", _csv_bytes("not,csv\n1,2\n"), "text/plain")}
        resp = client.post("/data/upload", files=files)
        assert resp.status_code == 422

    # Nu ska GLOBAL_CIRCUIT_BREAKER vara öppen → SystemError → 500
    files = {"file": ("data.txt", _csv_bytes("not,csv\n1,2\n"), "text/plain")}
    resp_blocked = client.post("/data/upload", files=files)
    assert resp_blocked.status_code == 500

    body = resp_blocked.json()
    assert "Circuit breaker is OPEN" in body["error"]

    # Vänta tills CB stänger igen
    time.sleep(5)

    files_ok = {"file": ("data.csv", _csv_bytes("a,b\n1,2\n"), "text/csv")}
    resp_ok = client.post("/data/upload", files=files_ok)
    assert resp_ok.status_code == 200
