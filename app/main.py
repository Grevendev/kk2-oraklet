import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.concurrency import run_in_threadpool

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.middleware.compression import CompressionMiddleware
from starlette.middleware.timeout import TimeoutMiddleware

from app.errors import (
    http_exception_handler,
    validation_exception_handler,
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


app = FastAPI()

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

    # Cleanup: clear dataset and stats cache
    data_service.clear()


# -----------------------------------
# CORS POLICY
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Byt till specifika domäner i produktion
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# RATE LIMITER
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
# REQUEST TIMEOUT PROTECTION
# -----------------------------------
app.add_middleware(
    TimeoutMiddleware,
    timeout=10  # 10 sekunder per request
)



# -----------------------------------
# RESPONSE COMPRESSION (Brotli + GZip)
# -----------------------------------
app.add_middleware(
    CompressionMiddleware,
    minimum_size=500,
    gzip=True,
    brotli=True
)

app.add_middleware(SecurityHeadersMiddleware)


# -----------------------------------
# GLOBAL EXCEPTION HANDLERS
# -----------------------------------
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, validation_exception_handler)

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
        raise ValidationError("File must be a CSV.")

    # Read file asynchronously
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # -----------------------------------
    # MEMORY USAGE GUARD — STEP 1
    # -----------------------------------
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

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

    # Audit log: upload attempt
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
        logger.warning({
            "event": "csv_upload_validation_failed",
            "request_id": request.state.request_id,
            "filename": file.filename,
            "reason": str(e),
            "client_ip": request.client.host
        })
        raise e
    except Exception as e:
        logger.error({
            "event": "csv_upload_unexpected_error",
            "request_id": request.state.request_id,
            "filename": file.filename,
            "error": str(e),
            "client_ip": request.client.host
        })
        raise SystemError(str(e))

    data_service.set_dataset(df)

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

    try:
        stats = data_service.get_stats()
    except ValidationError as e:
        raise UserError(str(e))

    etag = data_service.get_stats_etag()
    client_etag = request.headers.get("If-None-Match")

    if client_etag == etag:
        logger.info({
            "event": "stats_not_modified",
            "request_id": request.state.request_id,
            "client_ip": request.client.host
        })
        return Response(status_code=304)

    response = StatsResponse(stats=stats)
    response = JSONResponse(content=response.model_dump())
    response.headers["ETag"] = etag

    logger.info({
        "event": "stats_returned",
        "request_id": request.state.request_id,
        "client_ip": request.client.host,
        "etag": etag
    })

    return response


# -----------------------------------
# CSV DOWNLOAD
# -----------------------------------
@app.get("/data/download/csv")
@limiter.limit("10/minute")
def download_csv(request: Request):
    logger.info({
        "event": "csv_download_requested",
        "request_id": request.state.request_id,
        "client_ip": request.client.host
    })

    try:
        csv_bytes = data_service.get_csv()
    except ValidationError as e:
        raise UserError(str(e))

    logger.info({
        "event": "csv_download_success",
        "request_id": request.state.request_id,
        "client_ip": request.client.host,
        "size_bytes": len(csv_bytes)
    })

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dataset.csv"}
    )


# -----------------------------------
# PARQUET DOWNLOAD
# -----------------------------------
@app.get("/data/download/parquet")
@limiter.limit("10/minute")
def download_parquet(request: Request):
    logger.info({
        "event": "parquet_download_requested",
        "request_id": request.state.request_id,
        "client_ip": request.client.host
    })

    try:
        parquet_bytes = data_service.get_parquet()
    except ValidationError as e:
        raise UserError(str(e))

    logger.info({
        "event": "parquet_download_success",
        "request_id": request.state.request_id,
        "client_ip": request.client.host,
        "size_bytes": len(parquet_bytes)
    })

    return StreamingResponse(
        iter([parquet_bytes]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=dataset.parquet"}
    )
