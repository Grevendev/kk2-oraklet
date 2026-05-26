from fastapi import FastAPI, UploadFile, File, HTTPException
from app.data import data_service, validate_and_clean_csv
from app.schemas import UploadResponse, StatsResponse
from app.config import logger
# Basic FastAPI app initialization
# This file will later include routes for data upload, stats and AI queries.
app = FastAPI()

@app.get("/health")
def health_chech():
  """Return basic health status for the API."""
  return {"status": "ok"}

@app.post("/data/upload", response_model=UploadResponse)
async def upload_data(file: UploadFile = File(...)):
    """Upload a CSV file, validate it, clean it and store it in memory."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    file_bytes = await file.read()

    try:
        df = validate_and_clean_csv(file_bytes)
    except Exception as e:
        logger.error(f"CSV validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    data_service.set_dataset(df)

    return UploadResponse(
        rows=df.shape[0],
        columns=list(df.columns),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()}
    )
  
@app.get("/data/stats", response_model=StatsResponse)
def get_status():
  """Return descriptive statistics for the uploaded dataset."""
  try:
    df = get_dataset()
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
  
  stats = df.describe(include="all").to_dict()

  return StatsResponse(stats=stats)