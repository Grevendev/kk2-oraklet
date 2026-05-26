from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
  """Ensure the health endpoint returns OK."""
  response = client.get("/health")
  assert response.status_code == 200
  assert response.json() == {"status": "ok"}

def test_upload_invalid_file():
  """Uploading a non-CSV file should return 400."""
  response = client.post(
    "/data/upload",
    files={"file": ("test.txt", b"hello")}
  )
  assert response.status_code == 400

def test_upload_and_stats():
  """Upload a valid CSV and then restrieve stats."""
  csv_content = b"city,temp\nMalmo,10\nLund,12"

  upload_response = client.post(
    "/data/upload",
    files={"file": ("data.csv", csv_content)}
  )
  assert upload_response.status_code == 200

  stats_response = client.get("/data/stats")
  assert stats_response.status_code == 200
  assert "stats" in stats_response.json()

def test_upload_too_large_file():
    """Uploading a file larger than allowed should return 400."""
    big_content = b"a" * (11 * 1024 * 1024)  # 11 MB
    response = client.post(
        "/data/upload",
        files={"file": ("big.csv", big_content)}
    )
    assert response.status_code == 400


def test_upload_invalid_columns():
    """Uploading a CSV with invalid column names should return 400."""
    csv_content = b"Unnamed: 0,temp\n1,10"
    response = client.post(
        "/data/upload",
        files={"file": ("bad.csv", csv_content)}
    )
    assert response.status_code == 400

def test_download_csv_without_upload():
   """Downloading CSV without uploading should return 404."""
   response = client.get("/data/download/csv")
   assert response.status_code == 404

def test_download_parquet_without_upload():
   """Downloading Parquet without uploading should return 404."""
   response = client.get("/data/download/parquet")
   assert response.status_code == 404

def test_upload_and_download_parquet():
   """Upload CSV and ensure Parquet download works."""
   csv_content = b"city,temp\nMalmo,10\nLund,12"

   upload_response = client.post(
      "/data/upload",
      files={"file": ("data.csv", csv_content)}
   )
   assert upload_response.status_code == 200

   parquet_response = client.get("/data/download/parquet")
   assert parquet_response.status_code == 200
   assert parquet_response.headers["Content-Disposition"] == "attachment; filename=dataset.parquet"

def test_error_model_structure():
    """Ensure error responses follow the standardized ErrorResponse model."""
    response = client.get("/data/stats")  # no dataset uploaded
    assert response.status_code == 404

    body = response.json()
    assert "error_type" in body
    assert "message" in body
    assert "details" in body
