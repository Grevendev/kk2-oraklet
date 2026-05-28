from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.schemas import ErrorResponse
from app.config import logger


class ValidationError(Exception):
    """Raised when user input is syntactically correct but semantically invalid."""
    pass


class UserError(Exception):
    """Raised when the user performs an invalid action (e.g., requesting stats before upload)."""
    pass


class SystemError(Exception):
    """Raised when an unexpected internal error occurs."""
    pass


# ---------------------------------------
# HTTPException (FastAPI built-in)
# ---------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_type="HTTPException",
            message=str(exc.detail),
            details={"path": request.url.path}
        ).model_dump()
    )


# ---------------------------------------
# ValidationError (422)
# ---------------------------------------
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_type="ValidationError",
            message=str(exc),
            details={"path": request.url.path}
        ).model_dump()
    )


# ---------------------------------------
# UserError (400)
# ---------------------------------------
async def user_error_handler(request: Request, exc: UserError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_type="UserError",
            message=str(exc),
            details={"path": request.url.path}
        ).model_dump()
    )


# ---------------------------------------
# SystemError (500)
# ---------------------------------------
async def system_error_handler(request: Request, exc: SystemError):
    logger.error(f"SystemError: {exc}")

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_type="SystemError",
            message="Internal server error.",
            details={"error": str(exc)}
        ).model_dump()
    )
