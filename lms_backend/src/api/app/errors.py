from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .logging_config import get_logger

logger = get_logger(__name__)


class ErrorCode:
    """Canonical error codes for API responses."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTH_ERROR"
    AUTHORIZATION_ERROR = "AUTHZ_ERROR"
    NOT_FOUND = "NOT_FOUND"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ApplicationError(Exception):
    """Base application error that yields a standardized JSON response."""

    def __init__(self, message: str, status_code: int = 400, code: str = ErrorCode.INTERNAL_ERROR, details: Dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_response(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "timestamp": self.timestamp,
                "details": self.details,
            }
        }


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the application."""

    @app.exception_handler(ApplicationError)
    async def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
        logger.warning("ApplicationError occurred")
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        # Mask details; don't leak internals
        logger.warning(f"HTTPException: {exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR if exc.status_code >= 500 else ErrorCode.VALIDATION_ERROR,
                    "message": exc.detail if isinstance(exc.detail, str) else "Request failed",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        # Log internal details but do not expose to client
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR,
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "details": {},
                }
            },
        )
