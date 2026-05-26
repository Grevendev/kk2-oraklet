import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.config import logger
from app.errors import ValidationError


class DataService:
    """
    Service responsible for storing, validating and converting datasets.
    Stores both DataFrame and Parquet bytes for optimal performance.
    Includes production-grade statistics caching.
    """

    STATS_TTL_SECONDS = 60  # Cache stats for 1 minute

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._parquet_bytes: Optional[bytes] = None

        # Stats cache
        self._stats_cache: Optional[Dict[str, Any]] = None
        self._stats_timestamp: Optional[datetime] = None

    # -----------------------------
    # Dataset storage
    # -----------------------------
    def set_dataset(self, df: pd.DataFrame) -> None:
        """Store the cleaned dataset and generate Parquet bytes."""
        self._df = df

        # Reset stats cache
        self._stats_cache = None
        self._stats_timestamp = None

        # Convert DataFrame to Parquet bytes
        table = pa.Table.from_pandas(df)
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink)
        self._parquet_bytes = sink.getvalue().to_pybytes()

        logger.info(
            f"Dataset stored: {df.shape[0]} rows, {df.shape[1]} columns, "
            f"Parquet size: {len(self._parquet_bytes)} bytes."
        )

    # -----------------------------
    # Dataset access
    # -----------------------------
    def get_dataset(self) -> pd.DataFrame:
        if self._df is None:
            raise ValidationError("No dataset has been uploaded yet.")
        return self._df

    def get_parquet(self) -> bytes:
        if self._parquet_bytes is None:
            raise ValidationError("No dataset has been uploaded yet.")
        return self._parquet_bytes

    def get_csv(self) -> bytes:
        if self._df is None:
            raise ValidationError("No dataset has been uploaded yet.")
        return self._df.to_csv(index=False).encode("utf-8")

    # -----------------------------
    # Stats with caching
    # -----------------------------
    def _is_stats_cache_valid(self) -> bool:
        """Check if cached stats are still valid based on TTL."""
        if self._stats_cache is None or self._stats_timestamp is None:
            return False

        age = datetime.utcnow() - self._stats_timestamp
        return age < timedelta(seconds=self.STATS_TTL_SECONDS)

    def get_stats(self) -> dict:
        """Return cached or newly computed descriptive statistics."""
        if self._df is None:
            raise ValidationError("No dataset has been uploaded yet.")

        # Return cached stats if valid
        if self._is_stats_cache_valid():
            logger.info("Returning cached statistics.")
            return self._stats_cache

        # Compute new stats
        logger.info("Computing new statistics.")
        stats = self._df.describe(include="all").to_dict()

        # Add metadata
        stats["_metadata"] = {
            "rows": self._df.shape[0],
            "columns": self._df.shape[1],
            "generated_at": datetime.utcnow().isoformat(),
            "cache_ttl_seconds": self.STATS_TTL_SECONDS,
        }

        # Store in cache
        self._stats_cache = stats
        self._stats_timestamp = datetime.utcnow()

        return stats


# Singleton instance
data_service = DataService()


# -----------------------------
# CSV validation
# -----------------------------
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
