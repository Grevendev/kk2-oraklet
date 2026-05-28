from fastapi.testclient import TestClient
from app.main import app
from app.state import state

client = TestClient(app)


# ============================================================
# Schema Drift Tests
# ============================================================

def test_schema_drift_no_change():
    """
    Uploading two CSVs with identical schema should NOT trigger schema drift.
    """

    # Reset state
    state.data_service._df = None
    state.data_service._schema_fingerprint = None

    csv1 = b"city,temp\nMalmo,10\nLund,12"
    csv2 = b"city,temp\nStockholm,15\nUppsala,14"

    # First upload
    r1 = client.post("/data/upload", files={"file": ("data.csv", csv1)})
    assert r1.status_code == 200

    old_fp = state.data_service._schema_fingerprint

    # Second upload with same schema
    r2 = client.post("/data/upload", files={"file": ("data.csv", csv2)})
    assert r2.status_code == 200

    new_fp = state.data_service._schema_fingerprint

    # Fingerprint must be identical
    assert old_fp == new_fp


def test_schema_drift_detected():
    """
    Uploading a CSV with a changed schema should trigger schema drift detection.
    Upload is still allowed by default.
    """

    # Reset state
    state.data_service._df = None
    state.data_service._schema_fingerprint = None

    csv1 = b"city,temp\nMalmo,10"
    csv2 = b"city,humidity\nMalmo,55"

    # First upload
    r1 = client.post("/data/upload", files={"file": ("data.csv", csv1)})
    assert r1.status_code == 200

    old_fp = state.data_service._schema_fingerprint

    # Second upload with changed schema
    r2 = client.post("/data/upload", files={"file": ("data.csv", csv2)})
    assert r2.status_code == 200

    new_fp = state.data_service._schema_fingerprint

    # Fingerprint must change
    assert old_fp != new_fp


def test_schema_drift_block_upload(monkeypatch):
    """
    If schema drift blocking is enabled, upload should return 400 UserError.
    """

    # Reset state
    state.data_service._df = None
    state.data_service._schema_fingerprint = None

    # Enable blocking via monkeypatch
    monkeypatch.setattr("app.chain.steps.LLMRunner.BLOCK_SCHEMA_DRIFT", True, raising=False)

    csv1 = b"city,temp\nMalmo,10"
    csv2 = b"city,humidity\nMalmo,55"

    # First upload
    r1 = client.post("/data/upload", files={"file": ("data.csv", csv1)})
    assert r1.status_code == 200

    # Second upload with changed schema → should be blocked
    r2 = client.post("/data/upload", files={"file": ("data.csv", csv2)})
    assert r2.status_code == 400
    assert r2.json()["error_type"] == "UserError"
