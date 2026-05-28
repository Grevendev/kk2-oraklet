from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================
# Validator Edge Case Tests
# ============================================================

def test_upload_whitespace_column_names():
    """CSV med whitespace-only kolumnnamn ska returnera 422 ValidationError."""
    csv = b"city,   \nMalmo,10"
    response = client.post(
        "/data/upload",
        files={"file": ("bad.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_duplicate_columns():
    """CSV med duplicerade kolumnnamn ska returnera 422 ValidationError."""
    csv = b"city,city\nMalmo,10"
    response = client.post(
        "/data/upload",
        files={"file": ("dup.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_invalid_datatypes():
    """CSV med ogiltiga datatyper ska returnera 422 ValidationError."""
    csv = b"city,temp\nMalmo,not_a_number"
    response = client.post(
        "/data/upload",
        files={"file": ("badtype.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_nan_column():
    """CSV med NaN-kolumnnamn ska returnera 422 ValidationError."""
    csv = b"city,,temp\nMalmo,10,20"
    response = client.post(
        "/data/upload",
        files={"file": ("nan.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_empty_column_name():
    """CSV med tomt kolumnnamn ska returnera 422 ValidationError."""
    csv = b",temp\nMalmo,10"
    response = client.post(
        "/data/upload",
        files={"file": ("emptycol.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_too_many_columns():
    """CSV med fler kolumner än tillåtet ska returnera 422 ValidationError."""
    csv = b"a,b,c,d,e,f,g,h,i,j,k\n1,2,3,4,5,6,7,8,9,10,11"
    response = client.post(
        "/data/upload",
        files={"file": ("toomany.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_unknown_columns():
    """CSV med okända kolumner ska returnera 422 ValidationError."""
    csv = b"city,temp,unknown_col\nMalmo,10,999"
    response = client.post(
        "/data/upload",
        files={"file": ("unknown.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"


def test_upload_mixed_datatypes():
    """CSV med blandade datatyper i samma kolumn ska returnera 422 ValidationError."""
    csv = b"city,temp\nMalmo,10\nLund,not_a_number"
    response = client.post(
        "/data/upload",
        files={"file": ("mixed.csv", csv)}
    )
    assert response.status_code == 422
    assert response.json()["error_type"] == "ValidationError"
