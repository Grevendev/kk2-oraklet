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

from app.chain.steps import GLOBAL_CIRCUIT_BREAKER
from app.chain.errors import PipelineError


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
        name = name.lower()
        name = name.strip()

        import unicodedata
        name = unicodedata.normalize("NFKC", name)

        name = name.replace(" ", "_")

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

        for col in self._df.columns:
            s = self._df[col]

            col_stats: Dict[str, Any] = {
                "count": int(s.count()),
                "dtype": str(s.dtype),
            }

            if pd.api.types.is_numeric_dtype(s):
                col_stats.update(
                    {
                        "mean": float(s.mean()),
                        "min": float(s.min()),
                        "max": float(s.max()),
                        "std": float(s.std()),
                    }
                )
            else:
                has_unhashable = s.apply(
                    lambda v: isinstance(v, (list, tuple)) or getattr(v, "__array__", None) is not None
                ).any()
                if not has_unhashable:
                    col_stats["unique"] = int(s.nunique(dropna=True))

            stats[col] = col_stats

        stats["_metadata"] = {
            "rows": int(self._df.shape[0]),
            "columns": int(self._df.shape[1]),
            "generated_at": datetime.utcnow().isoformat(),
            "fingerprint": self._data_fingerprint,
        }

        self._stats_cache = stats
        self._stats_timestamp = datetime.utcnow()
        return stats

    def get_stats_etag(self) -> str:
        if self._data_fingerprint is None:
            raise ValidationError("No dataset uploaded yet.")
        return self._data_fingerprint

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
    # PARQUET VALIDATOR WITH LOGGING
    # ---------------------------------------------------------
    def validate_and_clean_parquet(self, file_bytes: bytes) -> pd.DataFrame:
        try:
            if not file_bytes or len(file_bytes) < 4:
                raise ValidationError("Invalid Parquet file: too small.")

            if file_bytes[:4] != b"PAR1":
                raise ValidationError("Invalid Parquet magic bytes.")

            # LOGGING 1 — ParquetFile()
            logger.error("DEBUG: entering ParquetFile()")
            parquet_file = pq.ParquetFile(pa.BufferReader(file_bytes))
            logger.error("DEBUG: ParquetFile() OK")

            schema = parquet_file.schema_arrow
            names = schema.names

            if any(n is None or str(n).strip() == "" for n in names):
                raise ValidationError("Empty or null column name.")

            if len(names) != len(set(names)):
                raise ValidationError("Duplicate columns detected.")

            # LOGGING 2 — read()
            logger.error("DEBUG: entering parquet_file.read()")
            table = parquet_file.read()
            logger.error("DEBUG: read() OK")

            # Mixed int/float detection BEFORE pandas
            for col_idx in range(table.num_columns):
                column = table.column(col_idx)

                seen_int = False
                seen_float = False

                for chunk in column.chunks:
                    arrow_type = chunk.type

                    if pa.types.is_integer(arrow_type):
                        seen_int = True
                    elif pa.types.is_floating(arrow_type):
                        seen_float = True

                    if seen_int and seen_float:
                        raise ValidationError("Mixed int and float values.")

            # LOGGING 3 — to_pandas()
            logger.error("DEBUG: entering table.to_pandas()")
            df = table.to_pandas()
            logger.error("DEBUG: to_pandas() OK")

            
            # Mixed int/float AFTER pandas
            for col in df.columns:
                s = df[col]

                if pd.api.types.is_float_dtype(s):
                    non_null = s.dropna()
                    if non_null.empty:
                        continue

                    is_int_like = non_null.apply(lambda v: float(v).is_integer())
                    if is_int_like.any() and (~is_int_like).any():
                        raise ValidationError("Mixed int and float values.")

            # Column cleanup + normalization
            cleaned = []
            for col in df.columns:
                if col is None or str(col).strip() == "":
                    raise ValidationError("Empty or null column name.")
                cleaned.append(str(col).strip())
            df.columns = cleaned
            df.columns = [self._normalize(col) for col in df.columns]

            # Nested list inconsistent types
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

            # Mixed numeric + string
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

            # Nullability check
            for col in df.columns:
                if df[col].isna().all():
                    raise ValidationError(f"Column '{col}' contains only null values.")

            return df

        except ValidationError as e:
            GLOBAL_CIRCUIT_BREAKER.after_failure()
            raise


# ============================================================
# CSV VALIDATOR (unchanged)
# ============================================================
def validate_and_clean_csv(file_bytes: bytes) -> pd.DataFrame:
    try:
        if not file_bytes or not file_bytes.strip():
            raise ValidationError("CSV file is empty.")

        MAX_SIZE_MB = 10
        MAX_COLUMNS = 50
        MIN_NUMERIC_COLUMNS = 1

        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            raise ValidationError(f"File exceeds maximum allowed size of {MAX_SIZE_MB} MB.")

        sample = file_bytes[:2048].decode("utf-8", errors="ignore")
        delimiter = ","
        if sample.count(";") > sample.count(","):
            delimiter = ";"
        elif sample.count("\t") > sample.count(","):
            delimiter = "\t"

        logger.info(f"Detected delimiter: '{delimiter}'")

        header_line = sample.split("\n", 1)[0]
        raw_cols = [c.strip() for c in header_line.split(delimiter)]
        if len(raw_cols) != len(set(raw_cols)):
            raise ValidationError("Duplicate column names detected.")

        try:
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="utf-8", delimiter=delimiter)
        except UnicodeDecodeError:
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding="latin-1", delimiter=delimiter)

        if df.columns.duplicated().any():
            raise ValidationError("Duplicate column names detected.")

        for col in df.columns:
            if df[col].astype(str).str.match(r"^-?\d+(\.\d+)?$").all():
                df[col] = pd.to_numeric(df[col], errors="coerce")

        cleaned_columns = []
        for col in df.columns:
            new_col = str(col).strip()

            if (
                new_col == ""
                or new_col.lower().startswith("unnamed")
                or new_col.lower() in {"nan", "none", "null"}
            ):
                raise ValidationError(f"Invalid column name detected: '{col}'")

            cleaned_columns.append(new_col)

        df.columns = cleaned_columns

        df = df.dropna(axis=1, how="all")

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
            raise ValidationError("Dataset must contain at least one number column for analysis.")

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

    except ValidationError as e:
        GLOBAL_CIRCUIT_BREAKER.after_failure()
        raise


# ============================================================
# Global instance
# ============================================================
data_service = DataService()
