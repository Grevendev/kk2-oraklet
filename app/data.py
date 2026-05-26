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
        """Return cached or newly computed descriptive statistics with column profiling."""
        if self._df is None:
            raise ValidationError("No dataset has been uploaded yet.")

        # Return cached stats if valid
        if self._is_stats_cache_valid():
            logger.info("Returning cached statistics.")
            return self._stats_cache

        logger.info("Computing new statistics.")
        df = self._df

        # Base descriptive statistics
        stats = df.describe(include="all").to_dict()

        # -----------------------------
        # COLUMN PROFILING
        # -----------------------------
        profiling = {}

        for col in df.columns:
            series = df[col]

            profiling[col] = {
                "dtype": str(series.dtype),
                "unique_values": int(series.nunique()),
                "null_count": int(series.isna().sum()),
                "null_percentage": float((series.isna().mean() * 100)),
            }

            # Numeric profiling
            if pd.api.types.is_numeric_dtype(series):
                profiling[col]["min"] = float(series.min())
                profiling[col]["max"] = float(series.max())
                profiling[col]["mean"] = float(series.mean())
                profiling[col]["distribution_type"] = "numeric"

            # Datetime profiling
            elif pd.api.types.is_datetime64_any_dtype(series):
                profiling[col]["min"] = str(series.min())
                profiling[col]["max"] = str(series.max())
                profiling[col]["distribution_type"] = "datetime"

            # Boolean profiling
            elif pd.api.types.is_bool_dtype(series):
                profiling[col]["true_count"] = int(series.sum())
                profiling[col]["false_count"] = int((~series).sum())
                profiling[col]["distribution_type"] = "boolean"

            # String profiling
            else:
                profiling[col]["avg_string_length"] = float(
                    series.astype(str).str.len().mean()
                )
                profiling[col]["distribution_type"] = "categorical"

        # Attach profiling to stats
        stats["_column_profile"] = profiling

        # Metadata
        stats["_metadata"] = {
            "rows": df.shape[0],
            "columns": df.shape[1],
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
    """Validate CSV content, enforce size limits, encoding, clean column names,
    auto-detect delimiter and auto-convert types."""

    MAX_SIZE_MB = 10
    MAX_COLUMNS = 100
    MIN_NUMERIC_COLUMNS = 1

    size_mb = len(file_bytes) / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        raise ValidationError(f"File exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

    # -----------------------------------
    # AUTO-DETECT DELIMITER
    # -----------------------------------
    sample = file_bytes[:2048].decode("utf-8", errors="ignore")

    delimiter = ","
    if sample.count(";") > sample.count(","):
        delimiter = ";"
    elif sample.count("\t") > sample.count(","):
        delimiter = "\t"

    logger.info(f"Detected delimiter: '{delimiter}'")

    # Try reading with UTF-8 first, fallback to latin-1
    try:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="utf-8", delimiter=delimiter)
    except UnicodeDecodeError:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="latin-1", delimiter=delimiter)

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

    # -----------------------------------
    # AUTOMATIC TYPE CONVERSION (unchanged)
    # -----------------------------------

    # 1. Convert percentage strings to floats
    for col in df.columns:
        if df[col].dtype == object and df[col].astype(str).str.endswith("%").any():
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce") / 100

    # 2. Convert numeric strings (including Swedish decimals)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="ignore")

    # 3. Convert boolean-like strings
    BOOL_TRUE = {"true", "yes", "1", "y", "ja"}
    BOOL_FALSE = {"false", "no", "0", "n", "nej"}

    for col in df.columns:
        if df[col].dtype == object:
            lowered = df[col].astype(str).str.lower()
            if lowered.isin(BOOL_TRUE | BOOL_FALSE).any():
                df[col] = lowered.map(
                    lambda x: True if x in BOOL_TRUE else False if x in BOOL_FALSE else None
                )

    # 4. Convert date-like strings
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = pd.to_datetime(df[col], errors="ignore")

    # -----------------------------------
    # ANALYSIS READINESS VALIDATION (unchanged)
    # -----------------------------------

    if df.shape[0] < 1:
        raise ValidationError("Dataset must contain at least one data row.")

    if df.shape[1] > MAX_COLUMNS:
        raise ValidationError(
            f"Dataset has {df.shape[1]} columns, exceeding the limit of {MAX_COLUMNS}."
        )

    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) < MIN_NUMERIC_COLUMNS:
        raise ValidationError(
            "Dataset must contain at least one numeric column for analysis."
        )

    id_like_columns = [
        col for col in df.columns if df[col].nunique() == df.shape[0]
    ]

    if len(id_like_columns) == df.shape[1]:
        raise ValidationError(
            "Dataset appears to contain only ID-like columns (all values unique). "
            "At least one column must contain repeated or aggregatable values."
        )

    null_columns = [col for col in df.columns if df[col].isna().all()]
    if null_columns:
        raise ValidationError(
            f"Dataset contains columns with only null values: {null_columns}"
        )

    return df
