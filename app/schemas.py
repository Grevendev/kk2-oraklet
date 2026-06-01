# app/schemas.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class UploadResponse(BaseModel):
    """
    Response model for dataset upload metadata.
    Matches testsvitens krav exakt.
    """
    rows: int
    columns: List[str]
    dtypes: Dict[str, str]


class StatsResponse(BaseModel):
    """
    Response model for descriptive statistics.
    """
    stats: Dict[str, Any]


class ErrorResponse(BaseModel):
    """
    Standardized error response model for all API errors.
    """
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class AIResponse(BaseModel):
    """
    Standardized response model for AI answers.
    """
    question: str
    answer: str
    reasoning: str
    stats_used: Dict[str, Any]
