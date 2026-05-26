import pandas as pd
from typing import Optional
from app.config import logger


class DataService:
    """Service responsible for storing and validating uploaded datasets."""

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None

    def set_dataset(self, df: pd.DataFrame) -> None:
        """Store the cleaned dataset in memory."""
        logger.info(f"Dataset stored with {df.shape[0]} rows and {df.shape[1]} columns.")
        self._df = df

    def get_dataset(self) -> pd.DataFrame:
        """Return the stored dataset or raise an error if none exists."""
        if self._df is None:
            raise ValueError("No dataset has been uploaded yet.")
        return self._df

    def get_stats(self) -> dict:
        """Return descriptive statistics for the stored dataset."""
        if self._df is None:
            raise ValueError("No dataset has been uploaded yet.")
        return self._df.describe(include="all").to_dict()


# Singleton instance used by the application
data_service = DataService()


def validate_and_clean_csv(file_bytes: bytes) -> pd.DataFrame:
    """Validate CSV content, enforce size limits, encoding, and clean column names."""

    MAX_SIZE_MB = 10
    size_mb = len(file_bytes) / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        raise ValueError(f"File exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

    # Try reading with UTF-8 first, fallback to latin-1
    try:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="latin-1")

    if df.empty:
        raise ValueError("CSV file is empty or contains no rows.")

    # Clean column names
    cleaned_columns = []
    for col in df.columns:
        new_col = str(col).strip()
        if new_col == "" or new_col.lower().startswith("unnamed"):
            raise ValueError(f"Invalid column name detected: '{col}'")
        cleaned_columns.append(new_col)

    df.columns = cleaned_columns

    # Drop fully empty columns
    df = df.dropna(axis=1, how="all")

    return df
