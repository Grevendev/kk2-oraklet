from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class UploadResponse(BaseModel):
    """Response model for dataset upload metadata."""
    rows: int
    columns: List[str]
    dtypes: Dict[str, str]


class StatsResponse(BaseModel):
    """Response model for descriptive statistics."""
    stats: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Standardized error response model for all API errors."""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
