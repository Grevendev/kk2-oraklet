from fastapi import FastAPI, UploadFile, File, HTTPException
# Basic FastAPI app initialization
# This file will later include routes for data upload, stats and AI queries.
app = FastAPI()

@app.get("/health")
def health_chech():
  """Return basic health status for the API."""
  return {"status": "ok"}

@app.post("/data/upload", response_model=UploadResponse)
async def upload_data(file: UploadFile = File(...)):
  """Upload a CSV file, validate it, load it into Pandas and store it in memory."""
  if not file.filename.endswith(".csv"):
    raise HTTPException(status_code=400, detail="File must be a CSV.")

    try: 
      df = pd.read_csv(file.file)
    except Exception:
      raise HTTPException(status_code=400, detail="Failed to read CSV file.")
    
    set_dataset(df)

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