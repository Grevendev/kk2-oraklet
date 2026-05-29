# app/tests/test_schema_drift_auto_update.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.state import state


client = TestClient(app)


def test_schema_drift_auto_update(monkeypatch):
    """
    Verifierar att schema-fingerprint uppdateras automatiskt när
    schema-drift upptäcks och blocking är avstängd.
    """

    # ---------------------------------------------------------
    # 1. Reset state
    # ---------------------------------------------------------
    state.reset()

    # ---------------------------------------------------------
    # 2. Ladda upp baseline-schema
    # ---------------------------------------------------------
    csv1 = "city,temp\nMalmö,10\nLund,12\n"
    files1 = {"file": ("baseline.csv", csv1, "text/csv")}

    res1 = client.post("/data/upload", files=files1)
    assert res1.status_code == 200

    baseline_fp = state.schema_fingerprint
    assert baseline_fp is not None

    # ---------------------------------------------------------
    # 3. Stäng av schema-drift-blockering
    # ---------------------------------------------------------
    monkeypatch.setattr(state, "schema_drift_blocking", False)

    # ---------------------------------------------------------
    # 4. Ladda upp dataset med NYTT schema → drift ska upptäckas
    #    men INTE blockeras → fingerprint ska uppdateras
    # ---------------------------------------------------------
    csv2 = "city,temp,humidity\nMalmö,10,80\nLund,12,75\n"
    files2 = {"file": ("drift.csv", csv2, "text/csv")}

    res2 = client.post("/data/upload", files=files2)
    assert res2.status_code == 200

    updated_fp = state.schema_fingerprint
    assert updated_fp != baseline_fp  # fingerprint ska ha ändrats

    # ---------------------------------------------------------
    # 5. Ladda upp dataset med det NYA schemat igen → ingen drift
    # ---------------------------------------------------------
    csv3 = "city,temp,humidity\nGöteborg,14,70\nUppsala,11,65\n"
    files3 = {"file": ("new_schema.csv", csv3, "text/csv")}

    res3 = client.post("/data/upload", files=files3)
    assert res3.status_code == 200

    # fingerprint ska vara samma som efter auto-update
    assert state.schema_fingerprint == updated_fp
