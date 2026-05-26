from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.schemas import ErrorResponse
from app.config import logger


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPExceptions with a standardized error model."""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_type="HTTPException",
            message=str(exc.detail),
            details={"path": request.url.path}
        ).dict()
    )


async def validation_exception_handler(request: Request, exc: Exception):
    """Handle validation and unexpected errors with a consistent structure."""
    logger.error(f"Unhandled error: {exc}")

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_type="InternalServerError",
            message="An unexpected error occurred.",
            details={"error": str(exc)}
        ).dict()
    )
