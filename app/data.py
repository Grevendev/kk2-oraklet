import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.config import logger
from app.errors import ValidationError


class DataService:
    """
    Service responsible for storing, validating and converting datasets.
    Stores both DataFrame and Parquet bytes for optimal performance.
    Includes production-grade statistics caching and schema fingerprinting.
    """

    STATS_TTL_SECONDS = 60  # Cache stats for 1 minute

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._parquet_bytes: Optional[bytes] = None

        # Stats cache
        self._stats_cache: Optional[Dict[str, Any]] = None
        self._stats_timestamp: Optional[datetime] = None

        # Schema fingerprint
        self._schema_fingerprint: Optional[str] = None

    # -----------------------------
    # Cleanup
    # -----------------------------
    def clear(self):
        self._df = None
        self._parquet_bytes = None
        self._stats_cache = None
        self._stats_timestamp = None
        self._schema_fingerprint = None

    # -----------------------------
    # ETag generation
    # -----------------------------
    def get_stats_etag(self) -> str:
        """Return a stable ETag hash for the current stats cache."""
        if self._stats_cache is None:
            return ""

        payload = {
            "rows": self._stats_cache["_metadata"]["rows"],
            "columns": self._stats_cache["_metadata"]["columns"],
            "generated_at": self._stats_cache["_metadata"]["generated_at"],
        }

        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    # -----------------------------
    # Schema fingerprinting
    # -----------------------------
    def compute_schema_fingerprint(self, df: pd.DataFrame) -> str:
        """Compute a stable fingerprint for the dataset schema."""
        schema = {
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns}
        }
        raw = json.dumps(schema, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def is_schema_changed(self, df: pd.DataFrame) -> bool:
        """Return True if the new dataset schema differs from the stored one."""
        if self._schema_fingerprint is None:
            return False

        new_fp = self.compute_schema_fingerprint(df)
        return new_fp != self._schema_fingerprint

    # -----------------------------
    # Store dataset + compute fingerprint
    # -----------------------------
    def set_dataset(self, df: pd.DataFrame) -> None:
        """Store the cleaned dataset, compute schema fingerprint and generate Parquet bytes."""
        self._df = df

        # Reset stats cache
        self._stats_cache = None
        self._stats_timestamp = None

        # Compute schema fingerprint
        self._schema_fingerprint = self.compute_schema_fingerprint(df)

        # Convert DataFrame to Parquet bytes
        table = pa.Table.from_pandas(df)
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink)
        self._parquet_bytes = sink.getvalue().to_pybytes()

        logger.info(
            f"Dataset stored: {df.shape[0]} rows, {df.shape[1]} columns, "
            f"Parquet size: {len(self._parquet_bytes)} bytes, "
            f"schema_fingerprint: {self._schema_fingerprint}"
        )

    # -----------------------------
    # Get stats (with caching)
    # -----------------------------
    def get_stats(self) -> Dict[str, Any]:
        """Return cached stats or compute new ones."""
        if self._df is None:
            raise ValidationError("No dataset uploaded yet.")

        # Return cached stats if still valid
        if (
            self._stats_cache is not None
            and self._stats_timestamp is not None
            and datetime.utcnow() - self._stats_timestamp < timedelta(seconds=self.STATS_TTL_SECONDS)
        ):
            return self._stats_cache

        # Compute new stats
        stats = {}
        for col in self._df.select_dtypes(include=["number"]).columns:
            series = self._df[col]
            stats[col] = {
                "mean": float(series.mean()),
                "min": float(series.min()),
                "max": float(series.max()),
                "std": float(series.std()),
                "count": int(series.count()),
            }

        # Metadata
        metadata = {
            "rows": int(self._df.shape[0]),
            "columns": int(self._df.shape[1]),
            "generated_at": datetime.utcnow().isoformat(),
        }

        stats["_metadata"] = metadata

        # Cache
        self._stats_cache = stats
        self._stats_timestamp = datetime.utcnow()

        return stats

    # -----------------------------
    # Get CSV bytes
    # -----------------------------
    def get_csv(self) -> bytes:
        if self._df is None:
            raise ValidationError("No dataset uploaded yet.")
        return self._df.to_csv(index=False).encode("utf-8")

    # -----------------------------
    # Get Parquet bytes
    # -----------------------------
    def get_parquet(self) -> bytes:
        if self._parquet_bytes is None:
            raise ValidationError("No dataset uploaded yet.")
        return self._parquet_bytes


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

    # -----------------------------------
    # EARLY TYPE INFERENCE
    # -----------------------------------
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

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
    # INPUT SANITIZATION
    # -----------------------------------
    dangerous_unicode = [
        "\u202E", "\u202D",
        "\u2066", "\u2067", "\u2068", "\u2069",
        "\u200B", "\u200C", "\u200D",
    ]

    for col in df.columns:
        if df[col].dtype == object:
            for char in dangerous_unicode:
                df[col] = df[col].astype(str).str.replace(char, "", regex=False)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.replace(r"[\x00-\x1F\x7F]", "", regex=True)

    def escape_excel_formula(value):
        if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(escape_excel_formula)

    safe_columns = []
    for col in df.columns:
        col = col.replace("=", "").replace("+", "").replace("-", "").replace("@", "")
        col = "".join(ch for ch in col if ch.isprintable())
        safe_columns.append(col)

    df.columns = safe_columns

    # -----------------------------------
    # MEMORY USAGE GUARD — STEP 2
    # -----------------------------------
    max_rows = 5_000_000
    max_columns = 200
    max_memory_bytes = 500 * 1024 * 1024

    df_memory = df.memory_usage(deep=True).sum()

    if df.shape[0] > max_rows:
        raise ValidationError(f"Dataset has too many rows ({df.shape[0]}). Max allowed is {max_rows}.")

    if df.shape[1] > max_columns:
        raise ValidationError(f"Dataset has too many columns ({df.shape[1]}). Max allowed is {max_columns}.")

    if df_memory > max_memory_bytes:
        raise ValidationError(f"Dataset uses too much memory ({df_memory} bytes). Max allowed is {max_memory_bytes}.")

    logger.info({
    "event": "memory_guard_passed",
    "rows": df.shape[0],
    "columns": df.shape[1],
    "memory_bytes": int(df_memory)
    })


    # -----------------------------------
    # AUTOMATIC TYPE CONVERSION
    # -----------------------------------
    for col in df.columns:
        if df[col].dtype == object and df[col].astype(str).str.endswith("%").any():
            df[col] = df[col].astype(str).str.replace("%", "", regex=False).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce") / 100

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False).str.replace(" ", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    BOOL_TRUE = {"true", "yes", "1", "y", "ja"}
    BOOL_FALSE = {"false", "no", "0", "n", "nej"}

    for col in df.columns:
        if df[col].dtype == object:
            lowered = df[col].astype(str).str.lower()
            if lowered.isin(BOOL_TRUE | BOOL_FALSE).any():
                df[col] = lowered.map(lambda x: True if x in BOOL_TRUE else False if x in BOOL_FALSE else None)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = pd.to_datetime(df[col], errors="ignore")

    # -----------------------------------
    # ANALYSIS READINESS VALIDATION
    # -----------------------------------
    logger.warning({
        "event": "debug_dtypes_before_numeric_check",
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "head": df.head().to_dict()
    })

    numeric_cols = df.select_dtypes(include=["number"]).columns

    if df.shape[0] < 1:
        raise ValidationError("Dataset must contain at least one data row.")

    if df.shape[1] > MAX_COLUMNS:
        raise ValidationError(f"Dataset has {df.shape[1]} columns, exceeding the limit of {MAX_COLUMNS}.")

    MAX_ROWS = 200_000
    if df.shape[0] > MAX_ROWS:
        raise ValidationError(f"Dataset has {df.shape[0]} rows, exceeding the limit of {MAX_ROWS}.")

    MAX_CELLS = 1_000_000
    total_cells = df.shape[0] * df.shape[1]
    if total_cells > MAX_CELLS:
        raise ValidationError(f"Dataset contains {total_cells:,} cells, exceeding the limit of {MAX_CELLS:,}.")

    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) < MIN_NUMERIC_COLUMNS:
        raise ValidationError("Dataset must contain at least one numeric column for analysis.")

    id_like_columns = [col for col in df.columns if df[col].nunique() == df.shape[0]]

    MIN_ROWS_FOR_ID_CHECK = 50  # eller 100 om du vill vara ännu försiktigare

    if df.shape[0] >= MIN_ROWS_FOR_ID_CHECK and len(id_like_columns) == df.shape[1]:
        raise ValidationError(
            "Dataset appears to contain only ID-like columns (all values unique). "
            "At least one column must contain repeated or aggregatable values."
        )


    null_columns = [col for col in df.columns if df[col].isna().all()]
    if null_columns:
        raise ValidationError(f"Dataset contains columns with only null values: {null_columns}")

    return df


# Global service instance
data_service = DataService()
