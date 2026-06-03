import time
import app.main as main_module


def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_circuit_breaker_opens_after_repeated_validation_errors(client, monkeypatch):
    cb = main_module.GLOBAL_CIRCUIT_BREAKER

    # Sänk tröskeln så CB öppnar efter 3 fel
    monkeypatch.setattr(cb, "max_failures", 3, raising=False)

    # Gör återhämtning snabbare
    monkeypatch.setattr(cb, "recovery_time_sec", 1, raising=False)

    # Säkerställ att CB börjar i CLOSED
    cb.reset()

    # Skicka 3 valideringsfel
    for _ in range(3):
        files = {"file": ("data.txt", _csv_bytes("not,csv\n1,2\n"), "text/plain")}
        resp = client.post("/data/upload", files=files)
        assert resp.status_code == 422

    # Nu ska CB vara OPEN → SystemError → 500
    files = {"file": ("data.txt", _csv_bytes("not,csv\n1,2\n"), "text/plain")}
    resp_blocked = client.post("/data/upload", files=files)
    assert resp_blocked.status_code == 500

    body = resp_blocked.json()
    assert "Circuit breaker is OPEN" in str(body)

    # Vänta tills CB återhämtar sig
    time.sleep(1.2)

    # Nu ska upload fungera igen
    files_ok = {"file": ("data.csv", _csv_bytes("a,b\n1,2\n"), "text/csv")}
    resp_ok = client.post("/data/upload", files=files_ok)
    assert resp_ok.status_code == 200
