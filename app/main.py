from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.exceptions import RequestValidationError

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

# Register global exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, validation_exception_handler)

app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(UserError, user_error_handler)
app.add_exception_handler(SystemError, system_error_handler)


@app.get("/health")
def health_chech():
    """Return basic health status for the API."""
    return {"status": "ok"}


@app.post("/data/upload", response_model=UploadResponse)
async def upload_data(file: UploadFile = File(...)):
    """Upload a CSV file, validate it, clean it and store it in memory."""
    if not file.filename.endswith(".csv"):
        raise ValidationError("File must be a CSV.")

    file_bytes = await file.read()

    try:
        df = validate_and_clean_csv(file_bytes)
    except ValidationError as e:
        logger.error(f"CSV validation failed: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected CSV parsing error: {e}")
        raise SystemError(str(e))

    data_service.set_dataset(df)

    return UploadResponse(
        rows=df.shape[0],
        columns=list(df.columns),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()}
    )


@app.get("/data/stats", response_model=StatsResponse)
def get_stats():
    """Return descriptive statistics for the uploaded dataset."""
    try:
        stats = data_service.get_stats()
    except ValidationError as e:
        raise UserError(str(e))

    return StatsResponse(stats=stats)


@app.get("/data/download/csv")
def download_csv():
    """Return the stored dataset as a downloadable CSV file."""
    try:
        csv_bytes = data_service.get_csv()
    except ValidationError as e:
        raise UserError(str(e))

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dataset.csv"}
    )


@app.get("/data/download/parquet")
def download_parquet():
    """Return the stored dataset as a downloadable Parquet file."""
    try:
        parquet_bytes = data_service.get_parquet()
    except ValidationError as e:
        raise UserError(str(e))

    return StreamingResponse(
        iter([parquet_bytes]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=dataset.parquet"}
    )
