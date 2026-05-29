# app/tests/test_schema_drift_detection.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.state import state


client = TestClient(app)


def test_schema_drift_detection(monkeypatch):
    """
    Verifierar att schema-drift upptäcks när kolumnstruktur ändras.
    """

    # ---------------------------------------------------------
    # 1. Säkerställ ren state
    # ---------------------------------------------------------
    state.reset()

    # ---------------------------------------------------------
    # 2. Ladda upp dataset med baseline-schema
    # ---------------------------------------------------------
    csv1 = "city,temp\nMalmö,10\nLund,12\n"
    files1 = {"file": ("test1.csv", csv1, "text/csv")}

    res1 = client.post("/data/upload", files=files1)
    assert res1.status_code == 200

    baseline_fp = state.schema_fingerprint
    assert baseline_fp is not None

    # ---------------------------------------------------------
    # 3. Ladda upp dataset med IDENTISKT schema → ingen drift
    # ---------------------------------------------------------
    csv2 = "city,temp\nGöteborg,14\nUppsala,11\n"
    files2 = {"file": ("test2.csv", csv2, "text/csv")}

    res2 = client.post("/data/upload", files=files2)
    assert res2.status_code == 200

    assert state.schema_fingerprint == baseline_fp

    # ---------------------------------------------------------
    # 4. Aktivera schema-drift-blockering
    # ---------------------------------------------------------
    monkeypatch.setattr(state, "schema_drift_blocking", True)

    # ---------------------------------------------------------
    # 5. Ladda upp dataset med ÄNDRAT schema → drift ska upptäckas
    # ---------------------------------------------------------
    csv3 = "city,temp,humidity\nMalmö,10,80\nLund,12,75\n"
    files3 = {"file": ("test3.csv", csv3, "text/csv")}

    res3 = client.post("/data/upload", files=files3)

    # Schema-drift ska blockeras → 400 UserError
    assert res3.status_code == 400
    assert "schema" in res3.text.lower() or "drift" in res3.text.lower()
