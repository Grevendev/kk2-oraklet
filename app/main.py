from fastapi import FastAPI
# Basic FastAPI app initialization
# This file will later include routes for data upload, stats and AI queries.
app = FastAPI()

@app.get("/health")
def health_chech():
  """Return basic health status for the API."""
  return {"status": "ok"}