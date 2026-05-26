from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.concurrency import run_in_threadpool
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


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
# CORS POLICY
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Byt till specifika domäner i produktion
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

app.add_middleware(SecurityHeadersMiddleware)


# Register global exception handlers
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


@app.get("/health")
def health_chech():
    """Return basic health status for the API."""
    return {"status": "ok"}


@app.post("/data/upload", response_model=UploadResponse)
@limiter.limit("5/minute")
async def upload_data(request: Request, file: UploadFile = File(...)):
    """Upload a CSV file, validate it asynchronously and store it in memory."""

    if not file.filename.endswith(".csv"):
        raise ValidationError("File must be a CSV.")

    # Read file asynchronously
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Audit log: upload attempt
    logger.info({
        "event": "csv_upload_attempt",
        "filename": file.filename,
        "file_size_bytes": file_size,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("User-Agent", "unknown")
    })

    # Run CPU-bound validation in a background thread
    try:
        df = await run_in_threadpool(validate_and_clean_csv, file_bytes)
    except ValidationError as e:
        logger.warning({
            "event": "csv_upload_validation_failed",
            "filename": file.filename,
            "reason": str(e),
            "client_ip": request.client.host
        })
        raise e
    except Exception as e:
        logger.error({
            "event": "csv_upload_unexpected_error",
            "filename": file.filename,
            "error": str(e),
            "client_ip": request.client.host
        })
        raise SystemError(str(e))

    # Store dataset
    data_service.set_dataset(df)

    # Audit log: successful upload
    logger.info({
        "event": "csv_upload_success",
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



@app.get("/data/stats", response_model=StatsResponse)
@limiter.limit("20/minute")
def get_stats(request: Request):
    """Return descriptive statistics for the uploaded dataset."""

    logger.info({
        "event": "stats_requested",
        "client_ip": request.client.host,
        "user_agent": request.headers.get("User-Agent", "unknown")
    })

    try:
        stats = data_service.get_stats()
    except ValidationError as e:
        raise UserError(str(e))

    logger.info({
        "event": "stats_returned",
        "client_ip": request.client.host
    })

    return StatsResponse(stats=stats)


@app.get("/data/download/csv")
@limiter.limit("10/minute")
def download_csv(request: Request):
    """Return the stored dataset as a downloadable CSV file."""

    logger.info({
        "event": "csv_download_requested",
        "client_ip": request.client.host
    })

    try:
        csv_bytes = data_service.get_csv()
    except ValidationError as e:
        raise UserError(str(e))

    logger.info({
        "event": "csv_download_success",
        "client_ip": request.client.host,
        "size_bytes": len(csv_bytes)
    })

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dataset.csv"}
    )



@app.get("/data/download/parquet")
@limiter.limit("10/minute")
def download_parquet(request: Request):
    """Return the stored dataset as a downloadable Parquet file."""

    logger.info({
        "event": "parquet_download_requested",
        "client_ip": request.client.host
    })

    try:
        parquet_bytes = data_service.get_parquet()
    except ValidationError as e:
        raise UserError(str(e))

    logger.info({
        "event": "parquet_download_success",
        "client_ip": request.client.host,
        "size_bytes": len(parquet_bytes)
    })

    return StreamingResponse(
        iter([parquet_bytes]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=dataset.parquet"}
    )

