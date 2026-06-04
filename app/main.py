# app/main.py

import os
import uuid
import time
from collections import deque
import math
import sys

import pyarrow as pa
import unicodedata
from app.canonicalization import get_schema_fingerprint

from app.chain.steps import GLOBAL_CIRCUIT_BREAKER
from app.chain.errors import PipelineError

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.concurrency import run_in_threadpool

from slowapi.errors import RateLimitExceeded

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi.middleware.gzip import GZipMiddleware

from app.api.ai import router as ai_router
from app.api.ai import clear_ai_cache

from app.errors import (
    http_exception_handler,
    ValidationError,
    UserError,
    SystemError,
    validation_error_handler,
    user_error_handler,
    system_error_handler
)
from app.data import data_service, validate_and_clean_csv
from app.schemas import UploadResponse, StatsResponse
from app.config import logger
from app.state import state
from app.chain.pipeline import OrakletPipeline


# -----------------------------------
# TEST MODE
# -----------------------------------
TESTING = os.getenv("TESTING") == "1"
if "pytest" in sys.argv[0]:
    TESTING = True

if TESTING:
    class NoOpLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    limiter = NoOpLimiter()
else:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)


app = FastAPI()


# -----------------------------------
# GLOBAL RATE ANOMALY TRACKER
# -----------------------------------
REQUEST_WINDOW_SECONDS = 10
MAX_REQUESTS_IN_WINDOW = 200
recent_requests = deque()


# -----------------------------------
# CIRCUIT BREAKER STATE
# -----------------------------------
circuit_open_until = 0
validation_failures = []
VALIDATION_WINDOW_SECONDS = 30
MAX_VALIDATION_FAILURES = 10
CIRCUIT_BREAKER_DURATION = 30


def record_validation_failure():
    global circuit_open_until
    now = time.time()
    validation_failures.append(now)

    validation_failures[:] = [
        t for t in validation_failures
        if t > now - VALIDATION_WINDOW_SECONDS
    ]

    if len(validation_failures) >= MAX_VALIDATION_FAILURES:
        circuit_open_until = now + CIRCUIT_BREAKER_DURATION
        logger.warning({
            "event": "circuit_breaker_opened",
            "opened_until": circuit_open_until,
            "failures_in_window": len(validation_failures),
            "window_seconds": VALIDATION_WINDOW_SECONDS,
        })


# -----------------------------------
# STARTUP & SHUTDOWN EVENTS
# -----------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info({"event": "server_startup"})
    # Pipeline skapas inte här längre
    pass



@app.on_event("shutdown")
async def on_shutdown():
    logger.info({"event": "server_shutdown"})
    data_service.clear()


# -----------------------------------
# CORS POLICY
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------
# SECURITY HEADERS
# -----------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        return response


# -----------------------------------
# REQUEST ID MIDDLEWARE
# -----------------------------------
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIDMiddleware)


# -----------------------------------
# GLOBAL RATE ANOMALY DETECTION
# -----------------------------------
class GlobalRateAnomalyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        now = time.time()
        recent_requests.append(now)

        while recent_requests and recent_requests[0] < now - REQUEST_WINDOW_SECONDS:
            recent_requests.popleft()

        if len(recent_requests) > MAX_REQUESTS_IN_WINDOW:
            return JSONResponse(
                status_code=429,
                content={
                    "error_type": "GlobalRateAnomaly",
                    "message": "Traffic spike detected. Please slow down.",
                    "request_id": request.state.request_id
                }
            )

        return await call_next(request)


if not TESTING:
    app.add_middleware(GlobalRateAnomalyMiddleware)


# -----------------------------------
# CIRCUIT BREAKER MIDDLEWARE
# -----------------------------------
class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        now = time.time()
        if now < circuit_open_until and request.url.path.startswith("/data/upload"):
            return JSONResponse(
                status_code=503,
                content={
                    "error_type": "CircuitBreakerOpen",
                    "message": "Service temporarily unavailable due to repeated validation failures.",
                    "retry_after_seconds": int(circuit_open_until - now),
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
        return await call_next(request)


if not TESTING:
    app.add_middleware(CircuitBreakerMiddleware)


# -----------------------------------
# AI ROUTER
# -----------------------------------
app.include_router(ai_router)


# -----------------------------------
# RESPONSE COMPRESSION
# -----------------------------------
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(SecurityHeadersMiddleware)


# -----------------------------------
# GLOBAL EXCEPTION HANDLERS
# -----------------------------------
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(UserError, user_error_handler)
app.add_exception_handler(SystemError, system_error_handler)


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error_type": "RateLimitExceeded",
            "message": "Too many requests. Please slow down.",
            "details": {"limit": str(exc.detail)}
        }
    )

@app.exception_handler(PipelineError)
async def pipeline_error_handler(request, exc: PipelineError):
    return JSONResponse(
        status_code=503,
        content={
            "error": exc.message,
            "step": exc.step_name,
        }
    )

# -----------------------------------
# HEALTH CHECK
# -----------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}





# -----------------------------------
# UPLOAD ENDPOINT
# -----------------------------------
@app.post("/data/upload", response_model=UploadResponse)
@limiter.limit("5/minute")
async def upload_data(request: Request, file: UploadFile = File(...)):
    # ---------------------------------------------------------
    # 0. Circuit Breaker: blockera direkt om OPEN
    # ---------------------------------------------------------
    try:
        GLOBAL_CIRCUIT_BREAKER.before_call()
    except PipelineError as e:
        # CB är OPEN → returnera 503
        raise SystemError(str(e))

    filename = file.filename.lower()
    content_type = (file.content_type or "").lower()

    is_csv = filename.endswith(".csv")
    is_parquet = filename.endswith(".parquet")

    # ---------------------------------------------------------
    # 1. Filtyp-validering → ticka CB vid fel
    # ---------------------------------------------------------
    if not (is_csv or is_parquet):
        GLOBAL_CIRCUIT_BREAKER.after_failure()
        record_validation_failure()
        raise ValidationError("Unsupported file type.")

    if is_parquet and content_type not in [
        "application/octet-stream",
        "application/x-parquet",
        "application/vnd.apache.parquet"
    ]:
        GLOBAL_CIRCUIT_BREAKER.after_failure()
        record_validation_failure()
        raise ValidationError("Invalid Parquet MIME type.")

    file_bytes = await file.read()

    # ---------------------------------------------------------
    # 2. CSV/Parquet validering → ticka CB vid valideringsfel
    # ---------------------------------------------------------
    try:
        if is_csv:
            df = await run_in_threadpool(validate_and_clean_csv, file_bytes)
        else:
            df = await run_in_threadpool(data_service.validate_and_clean_parquet, file_bytes)

        # Ny Kontroll, stoppa ogiltiga kolumnnamn
        for col in df.columns:
            col_str = str(col).strip()
            if col is None or col_str in ["None", "", "nan", "null"] or "unnamed" in col_str.lower():
                raise ValidationError("Invalid file format: Column name cannot be null or empty.")
            
        # Kanonisering: Sortera kolumerna alfabetiskt efter namn
        for col in df.columns:
            if df[col].dtype in ["int32", "int16", "int8"]:
                df[col] = df[col].astype("int64")
            


    except ValidationError:
        GLOBAL_CIRCUIT_BREAKER.after_failure()
        record_validation_failure()
        raise

    except UserError:
        # UserError är inte systemfel → ticka inte CB
        raise

    except Exception:
        # Okänt fel → ticka CB
        GLOBAL_CIRCUIT_BREAKER.after_failure()
        raise SystemError("Unexpected internal error")

    # ---------------------------------------------------------
    # 3. Normalisera kolumnnamn
    # ---------------------------------------------------------
    df.columns = [data_service._normalize(col) for col in df.columns]

    # ---------------------------------------------------------
    # 4. Schema drift → UserError (tickar inte CB)
    # ---------------------------------------------------------
    if data_service._df is not None:
        # Skapa en temporärt sorterad kopia för schema drift-kontrollen
        # så att ordningen inte triggar "Schema drift detected"
        df_sorted_for_drift = df[sorted(list(df.columns), key=lambda c: unicodedata.normalize("NFC", str(c)))]
        if data_service.is_schema_changed(df_sorted_for_drift):
            if state.schema_drift_blocking:
                raise UserError("Schema drift detected")

   # ---------------------------------------------------------
    # ---------------------------------------------------------
    # 5. Spara dataset & Kanonisera fingeravtryck
    # ---------------------------------------------------------
    # Vi sparar original-df utan permanent sortering för att hålla round-trips lossless
    data_service.set_dataset(df)
    state.dataset = df
    state.stats = data_service.get_stats()

    # Skapa PyArrow-schema från vår original-df och generera kanoniskt fingeravtryck
    pa_schema = pa.Schema.from_pandas(df, preserve_index=False)
    state.schema_fingerprint = get_schema_fingerprint(pa_schema)

    # ---------------------------------------------------------
    # 6. Column lineage
    # ---------------------------------------------------------
    if not hasattr(state, "column_lineage") or state.column_lineage is None:
        state.column_lineage = {}

    for col in df.columns:
        normalized = data_service._normalize(col)
        dtype = str(df[col].dtype)
        state.column_lineage[normalized] = dtype

    clear_ai_cache()

    # ---------------------------------------------------------
    # 7. SUCCESS → nollställ CB
    # ---------------------------------------------------------
    GLOBAL_CIRCUIT_BREAKER.after_success()

    return UploadResponse(
        rows=df.shape[0],
        columns=list(df.columns),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()}
    )


# -----------------------------------
# STATS ENDPOINT
# -----------------------------------
@app.get("/data/stats", response_model=StatsResponse)
@limiter.limit("20/minute")
def get_stats(request: Request):
    if data_service._df is None:
        raise UserError("No dataset uploaded")

    stats = data_service.get_stats()

    def clean(v):
        if isinstance(v, float) and math.isnan(v):
            return None
        if isinstance(v, dict):
            return {kk: clean(vv) for kk, vv in v.items()}
        return v

    safe_stats = {k: clean(v) for k, v in stats.items()}

    etag_value = data_service.get_stats_etag()
    etag = f'"{etag_value}"'

    if request.headers.get("If-None-Match") == etag:
        return Response(status_code=304)

    response = JSONResponse(content=StatsResponse(stats=safe_stats).model_dump())
    response.headers["ETag"] = etag
    return response


# -----------------------------------
# DOWNLOAD CSV
# -----------------------------------
@app.get("/data/download/csv")
@limiter.limit("10/minute")
def download_csv(request: Request):
    if data_service._df is None:
        raise ValidationError("No dataset uploaded")

    csv_bytes = data_service.get_csv().replace(b"\r\n", b"\n")

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dataset.csv"}
    )


# -----------------------------------
# DOWNLOAD PARQUET
# -----------------------------------
@app.get("/data/download/parquet")
@limiter.limit("10/minute")
def download_parquet(request: Request):
    if data_service._df is None:
        raise ValidationError("No dataset uploaded")

    parquet_bytes = data_service.get_parquet()

    return StreamingResponse(
        iter([parquet_bytes]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=dataset.parquet"}
    )
