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