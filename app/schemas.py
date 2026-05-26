from pydantic import BaseModel
from typing import List, Dict, Any

class UploadResponse(BaseModel):
  """Response model for dataset upload metadata."""
  rows: int
  columns: List[str]
  dtypes: Dict[str, str]

class StatsResponse(BaseModel):
  """Response model for descriptive statistics."""
  stats: Dict[str, Any]