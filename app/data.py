import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Optional
from app.config import logger
from app.errors import ValidationError  # <-- viktigt


class DataService:
    """
    Service responsible for storing, validating and converting datasets.
    Stores both DataFrame and Parquet bytes for optimal performance.
    """

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._parquet_bytes: Optional[bytes] = None
        self._stats_cache: Optional[dict] = None

    def set_dataset(self, df: pd.DataFrame) -> None:
        """Store the cleaned dataset and generate Parquet bytes."""
        self._df = df
        self._stats_cache = None  # reset cache

        # Convert DataFrame to Parquet bytes
        table = pa.Table.from_pandas(df)
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink)
        self._parquet_bytes = sink.getvalue().to_pybytes()

        logger.info(
            f"Dataset stored: {df.shape[0]} rows, {df.shape[1]} columns, "
            f"Parquet size: {len(self._parquet_bytes)} bytes."
        )

    def get_dataset(self) -> pd.DataFrame:
        """Return the stored DataFrame."""
        if self._df is None:
            raise ValidationError("No dataset has been uploaded yet.")
        return self._df

    def get_parquet(self) -> bytes:
        """Return the stored Parquet bytes."""
        if self._parquet_bytes is None:
            raise ValidationError("No dataset has been uploaded yet.")
        return self._parquet_bytes

    def get_csv(self) -> bytes:
        """Return the dataset as CSV bytes."""
        if self._df is None:
            raise ValidationError("No dataset has been uploaded yet.")
        return self._df.to_csv(index=False).encode("utf-8")

    def get_stats(self) -> dict:
        """Return cached or newly computed descriptive statistics."""
        if self._df is None:
            raise ValidationError("No dataset has been uploaded yet.")

        if self._stats_cache is None:
            self._stats_cache = self._df.describe(include="all").to_dict()

        return self._stats_cache


# Singleton instance
data_service = DataService()


def validate_and_clean_csv(file_bytes: bytes) -> pd.DataFrame:
    """Validate CSV content, enforce size limits, encoding, and clean column names."""

    MAX_SIZE_MB = 10
    size_mb = len(file_bytes) / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        raise ValidationError(f"File exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

    # Try reading with UTF-8 first, fallback to latin-1
    try:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="latin-1")

    if df.empty:
        raise ValidationError("CSV file is empty or contains no rows.")

    # Clean column names
    cleaned_columns = []
    for col in df.columns:
        new_col = str(col).strip()
        if new_col == "" or new_col.lower().startswith("unnamed"):
            raise ValidationError(f"Invalid column name detected: '{col}'")
        cleaned_columns.append(new_col)

    df.columns = cleaned_columns

    # Drop fully empty columns
    df = df.dropna(axis=1, how="all")

    return df
