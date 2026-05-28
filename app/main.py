import os
import uuid
import time
from collections import deque
import math

import pandas as pd

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.concurrency import run_in_threadpool

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi.middleware.gzip import GZipMiddleware

from app.api.ai import router as ai_router

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

#  global state import
from app.state import state


# -----------------------------------
# ENV FLAG FOR TEST MODE
# -----------------------------------
TESTING = os.getenv("TESTING") == "1"


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
    """Record a validation failure and possibly open the circuit."""
    global circuit_open_until
    now = time.time()
    validation_failures.append(now)

    # keep only failures in the last VALIDATION_WINDOW_SECONDS
    recent = [t for t in validation_failures if t > now - VALIDATION_WINDOW_SECONDS]
    validation_failures[:] = recent

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
    logger.info({
        "event": "server_startup",
        "message": "API is starting up"
    })


@app.on_event("shutdown")
async def on_shutdown():
    logger.info({
        "event": "server_shutdown",
        "message": "API is shutting down gracefully"
    })
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
# RATE LIMITER (AKTIV ÄVEN I TEST)
# -----------------------------------
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


# -----------------------------------
# SECURITY HEADERS
# -----------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
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
            logger.warning({
                "event": "global_rate_anomaly_detected",
                "request_id": request.state.request_id,
                "client_ip": request.client.host,
                "requests_last_10s": len(recent_requests),
                "limit": MAX_REQUESTS_IN_WINDOW
            })

            return JSONResponse(
                status_code=429,
                content={
                    "error_type": "GlobalRateAnomaly",
                    "message": "Traffic spike detected. Please slow down.",
                    "request_id": request.state.request_id
                }
            )

        return await call_next(request)


# Global anomaly kan vara avstängd i test om du vill
if not TESTING:
    app.add_middleware(GlobalRateAnomalyMiddleware)


# -----------------------------------
# CIRCUIT BREAKER MIDDLEWARE (AKTIV ÄVEN I TEST)
# -----------------------------------
class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        now = time.time()

        if now < circuit_open_until and request.url.path.startswith("/data/upload"):
            logger.warning({
                "event": "circuit_breaker_blocked_request",
                "request_id": getattr(request.state, "request_id", None),
                "client_ip": request.client.host,
                "blocked_until": circuit_open_until
            })
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


@app.exception_handler(TimeoutError)
def timeout_handler(request: Request, exc: TimeoutError):
    logger.warning({
        "event": "request_timeout",
        "request_id": request.state.request_id,
        "client_ip": request.client.host,
        "path": request.url.path
    })

    return JSONResponse(
        status_code=504,
        content={
            "error_type": "RequestTimeout",
            "message": "The request took too long to process.",
            "request_id": request.state.request_id
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
    if not file.filename.endswith(".csv"):
        record_validation_failure()
        raise ValidationError("File must be a CSV.")

    file_bytes = await file.read()
    file_size = len(file_bytes)

    MAX_UPLOAD_SIZE = 50 * 1024 * 1024

    if file_size > MAX_UPLOAD_SIZE:
        logger.warning({
            "event": "upload_too_large",
            "request_id": request.state.request_id,
            "filename": file.filename,
            "file_size_bytes": file_size,
            "max_allowed_bytes": MAX_UPLOAD_SIZE,
            "client_ip": request.client.host
        })
        raise UserError(
            f"Uploaded file is too large ({file_size} bytes). "
            f"Max allowed size is {MAX_UPLOAD_SIZE} bytes."
        )

    logger.info({
        "event": "csv_upload_attempt",
        "request_id": request.state.request_id,
        "filename": file.filename,
        "file_size_bytes": file_size,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("User-Agent", "unknown")
    })

    try:
        df = await run_in_threadpool(validate_and_clean_csv, file_bytes)

    except ValidationError as e:
        record_validation_failure()
        raise e

    except UserError:
        # UserError är 400, men räknas inte som valideringsfel för circuit breaker
        raise

    except Exception as e:
        import traceback
        logger.error({
            "event": "unexpected_internal_error",
            "traceback": traceback.format_exc(),
            "error_type": type(e).__name__,
            "error": str(e),
            "request_id": request.state.request_id,
            "filename": file.filename,
            "client_ip": request.client.host
        })
        raise SystemError("Unexpected internal error")

    # -----------------------------------
    # SCHEMA FINGERPRINTING / DRIFT
    # -----------------------------------
    if data_service._df is not None:
        if data_service.is_schema_changed(df):
            logger.warning({
                "event": "schema_changed",
                "request_id": request.state.request_id,
                "client_ip": request.client.host,
                "old_fingerprint": data_service._schema_fingerprint,
                "new_fingerprint": data_service.compute_schema_fingerprint(df),
                "message": "Uploaded dataset schema differs from previous dataset."
            })
            # schema drift ska ge 400
            raise UserError("Schema drift detected")

    # -----------------------------------
    # STORE DATASET
    # -----------------------------------
    data_service.set_dataset(df)

    # update global state for AI pipeline
    state.dataset = df
    state.stats = data_service.get_stats()

    logger.info({
        "event": "csv_upload_success",
        "request_id": request.state.request_id,
        "filename": file.filename,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "client_ip": request.client.host
    })

    return UploadResponse(
        rows=df.shape[0],
        columns=list(df.columns),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()}
    )


# -----------------------------------
# STATS ENDPOINT (ETag caching)
# -----------------------------------
@app.get("/data/stats", response_model=StatsResponse)
@limiter.limit("20/minute")
def get_stats(request: Request):
    logger.info({
        "event": "stats_requested",
        "request_id": request.state.request_id,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("User-Agent", "unknown")
    })

    if data_service._df is None:
        raise UserError("No dataset uploaded")

    stats = data_service.get_stats()

    # ersätt NaN med None för JSON‑kompatibilitet
    safe_stats = {}
    for k, v in stats.items():
        if isinstance(v, float) and math.isnan(v):
            safe_stats[k] = None
        else:
            safe_stats[k] = v

    etag = data_service.get_stats_etag()
    quoted_etag = f'"{etag}"'
    client_etag = request.headers.get("If-None-Match")

    if client_etag == quoted_etag:
        return Response(status_code=304)

    response_model = StatsResponse(stats=safe_stats)
    response = JSONResponse(content=response_model.model_dump())
    response.headers["ETag"] = quoted_etag
    return response


@app.get("/data/download/csv")
@limiter.limit("10/minute")
def download_csv(request: Request):
    logger.info({
        "event": "csv_download_requested",
        "request_id": request.state.request_id,
        "client_ip": request.client.host
    })

    if data_service._df is None:
        raise ValidationError("No dataset uploaded")

    csv_bytes = data_service.get_csv()

    # normalisera radslut till LF för testerna
    csv_bytes = csv_bytes.replace(b"\r\n", b"\n")

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dataset.csv"}
    )


@app.get("/data/download/parquet")
@limiter.limit("10/minute")
def download_parquet(request: Request):
    logger.info({
        "event": "parquet_download_requested",
        "request_id": request.state.request_id,
        "client_ip": request.client.host
    })

    if data_service._df is None:
        raise ValidationError("No dataset uploaded")

    parquet_bytes = data_service.get_parquet()

    return StreamingResponse(
        iter([parquet_bytes]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=dataset.parquet"}
    )
