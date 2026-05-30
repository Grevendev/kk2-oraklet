# app/data.py

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.config import logger
from app.errors import ValidationError


# ============================================================
# DataService
# ============================================================
class DataService:
    STATS_TTL_SECONDS = 60

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._parquet_bytes: Optional[bytes] = None

        self._stats_cache: Optional[Dict[str, Any]] = None
        self._stats_timestamp: Optional[datetime] = None

        self._schema_fingerprint: Optional[str] = None
        self._data_fingerprint: Optional[str] = None

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------
    def clear(self):
        self._df = None
        self._parquet_bytes = None
        self._stats_cache = None
        self._stats_timestamp = None
        self._schema_fingerprint = None
        self._data_fingerprint = None

    # ---------------------------------------------------------
    # Schema fingerprint
    # ---------------------------------------------------------

    def _normalize(self, name: str) -> str:
    # Lowercase
        name = name.lower()

        # Trim whitespace
        name = name.strip()

        # Unicode normalize (NFKC)
        import unicodedata
        name = unicodedata.normalize("NFKC", name)

        # Replace spaces with underscores
        name = name.replace(" ", "_")

        # Collapse multiple underscores
        while "__" in name:
            name = name.replace("__", "_")

        return name


    def compute_schema_fingerprint(self, df: pd.DataFrame) -> str:
        schema = {
            "columns": [self._normalize(col) for col in df.columns],
            "dtypes": {col: str(df[col].dtype) for col in df.columns}
        }
        raw = json.dumps(schema, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def is_schema_changed(self, df: pd.DataFrame) -> bool:
        if self._schema_fingerprint is None:
            return False
        return self.compute_schema_fingerprint(df) != self._schema_fingerprint

    # ---------------------------------------------------------
    # Store dataset
    # ---------------------------------------------------------
    def set_dataset(self, df: pd.DataFrame) -> None:
        df.columns = [self._normalize(col) for col in df.columns]
        self._df = df
        self._stats_cache = None
        self._stats_timestamp = None

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        self._data_fingerprint = hashlib.sha256(csv_bytes).hexdigest()
        self._schema_fingerprint = self.compute_schema_fingerprint(df)

        table = pa.Table.from_pandas(df)
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink)
        self._parquet_bytes = sink.getvalue().to_pybytes()

    # ---------------------------------------------------------
    # Stats
    # ---------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        if self._df is None:
            raise ValidationError("No dataset uploaded yet.")

        if (
            self._stats_cache is not None
            and self._stats_timestamp is not None
            and datetime.utcnow() - self._stats_timestamp < timedelta(seconds=self.STATS_TTL_SECONDS)
        ):
            return self._stats_cache

        stats: Dict[str, Any] = {}
        for col in self._df.select_dtypes(include=["number"]).columns:
            s = self._df[col]
            stats[col] = {
                "mean": float(s.mean()),
                "min": float(s.min()),
                "max": float(s.max()),
                "std": float(s.std()),
                "count": int(s.count()),
            }

        stats["_metadata"] = {
            "rows": int(self._df.shape[0]),
            "columns": int(self._df.shape[1]),
            "generated_at": datetime.utcnow().isoformat(),
            "fingerprint": self._data_fingerprint,
        }

        self._stats_cache = stats
        self._stats_timestamp = datetime.utcnow()
        return stats

    # ---------------------------------------------------------
    # CSV / Parquet getters
    # ---------------------------------------------------------
    def get_csv(self) -> bytes:
        if self._df is None:
            raise ValidationError("No dataset uploaded yet.")
        return self._df.to_csv(index=False).encode("utf-8")

    def get_parquet(self) -> bytes:
        if self._parquet_bytes is None:
            raise ValidationError("No dataset uploaded yet.")
        return self._parquet_bytes

    # ---------------------------------------------------------
    # PARQUET VALIDATOR (INSIDE CLASS)
    # ---------------------------------------------------------
    def validate_and_clean_parquet(self, file_bytes: bytes) -> pd.DataFrame:

        if not file_bytes or len(file_bytes) < 4:
            raise ValidationError("Invalid Parquet file: too small.")

        if file_bytes[:4] != b"PAR1":
            raise ValidationError("Invalid Parquet magic bytes.")

        # ---------------------------------------------------------
        # READ METADATA FIRST (avoid PyArrow auto-errors)
        # ---------------------------------------------------------
        try:
            parquet_file = pq.ParquetFile(pa.BufferReader(file_bytes))
        except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
            raise ValidationError("Invalid Parquet data: " + str(e))

        schema = parquet_file.schema_arrow

        # ---------------------------------------------------------
        # Duplicate column detection BEFORE reading table
        # ---------------------------------------------------------
        names = schema.names
        if len(names) != len(set(names)):
            raise ValidationError("Duplicate columns detected.")

        # ---------------------------------------------------------
        # READ TABLE (catch mixed datatype errors)
        # ---------------------------------------------------------
        try:
            table = parquet_file.read()
        except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
            raise ValidationError("Invalid Parquet data: " + str(e))

        df = table.to_pandas()

        # ---------------------------------------------------------
        # Column name validation
        # ---------------------------------------------------------
        cleaned = []
        for col in df.columns:
            if col is None or str(col).strip() == "":
                raise ValidationError("Empty or null column name.")
            cleaned.append(str(col).strip())
        df.columns = cleaned

        # ---------------------------------------------------------
        # Nested list type consistency
        # ---------------------------------------------------------
        for col in df.columns:
            s = df[col]
            if s.apply(lambda x: isinstance(x, list)).any():
                types = set()
                for v in s:
                    if isinstance(v, list):
                        for item in v:
                            types.add(type(item))
                if len(types) > 1:
                    raise ValidationError("Nested list contains mixed types.")

        # ---------------------------------------------------------
        # Mixed numeric + string
        # ---------------------------------------------------------
        for col in df.columns:
            s = df[col]
            if s.apply(lambda x: isinstance(x, (int, float))).any() and \
               s.apply(lambda x: isinstance(x, str)).any():
                raise ValidationError("Mixed numeric and string values.")

        # Bool + int → promote to int
        for col in df.columns:
            s = df[col]
            if s.apply(lambda x: isinstance(x, bool)).any() and \
               s.apply(lambda x: isinstance(x, int)).any():
                df[col] = s.astype(int)

        # Int + float → promote to float
        for col in df.columns:
            s = df[col]
            if s.apply(lambda x: isinstance(x, int)).any() and \
               s.apply(lambda x: isinstance(x, float)).any():
                df[col] = s.astype(float)

        # Nullability
        for col in df.columns:
            if df[col].isna().all():
                raise ValidationError(f"Column '{col}' contains only null values.")

        return df


# ============================================================
# CSV VALIDATOR (TOP LEVEL)
# ============================================================
def validate_and_clean_csv(file_bytes: bytes) -> pd.DataFrame:
    """Validate CSV content, enforce size limits, encoding, clean column names,
    auto-detect delimiter and auto-convert types."""

    if not file_bytes or not file_bytes.strip():
        raise ValidationError("CSV file is empty.")

    MAX_SIZE_MB = 10
    MAX_COLUMNS = 100
    MIN_NUMERIC_COLUMNS = 1

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise ValidationError(f"File exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

    # Detect delimiter
    sample = file_bytes[:2048].decode("utf-8", errors="ignore")
    delimiter = ","
    if sample.count(";") > sample.count(","):
        delimiter = ";"
    elif sample.count("\t") > sample.count(","):
        delimiter = "\t"

    logger.info(f"Detected delimiter: '{delimiter}'")

    try:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="utf-8", delimiter=delimiter)
    except UnicodeDecodeError:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="latin-1", delimiter=delimiter)

    if df.empty:
        raise ValidationError("CSV file is empty or contains no rows.")

    # Early numeric inference
    for col in df.columns:
        if df[col].astype(str).str.match(r"^-?\d+(\.\d+)?$").all():
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

    # Dangerous unicode removal
    dangerous_unicode = [
        "\u202E", "\u202D",
        "\u2066", "\u2067", "\u2068", "\u2069",
        "\u200B", "\u200C", "\u200D",
    ]

    for col in df.columns:
        if df[col].dtype == object:
            for char in dangerous_unicode:
                df[col] = df[col].astype(str).str.replace(char, "", regex=False)

    # Control characters
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.replace(r"[\x00-\x1F\x7F]", "", regex=True)

    # Excel formula escaping
    def escape_excel_formula(value):
        if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(escape_excel_formula)

    # Clean column names again
    safe_columns = []
    for col in df.columns:
        col = col.replace("=", "").replace("+", "").replace("-", "").replace("@", "")
        col = "".join(ch for ch in col if ch.isprintable())
        safe_columns.append(col)

    df.columns = safe_columns

    # Memory guard
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

    # Automatic type conversion
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

    # Analysis readiness
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

    if len(numeric_cols) < MIN_NUMERIC_COLUMNS:
        raise ValidationError("Dataset must contain at least one numeric column for analysis.")

    id_like_columns = [col for col in df.columns if df[col].nunique() == df.shape[0]]

    MIN_ROWS_FOR_ID_CHECK = 50
    if df.shape[0] >= MIN_ROWS_FOR_ID_CHECK and len(id_like_columns) == df.shape[1]:
        raise ValidationError(
            "Dataset appears to contain only ID-like columns (all values unique). "
            "At least one column must contain repeated or aggregatable values."
        )

    null_columns = [col for col in df.columns if df[col].isna().all()]
    if null_columns:
        raise ValidationError(f"Dataset contains columns with only null values: {null_columns}")

    return df


# ============================================================
# Global instance
# ============================================================
data_service = DataService()
