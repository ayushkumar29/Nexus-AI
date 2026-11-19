"""Centralized exception handling for Nexus AI."""

import logging
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("nexus_ai")


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized custom exception handlers onto the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.error(f"Application error at {request.url.path}: {exc.message} (details: {exc.details})")
        content: Dict[str, Any] = {
            "success": False,
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
            },
        }
        if exc.details is not None:
            content["error"]["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning(f"HTTP exception at {request.url.path}: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": str(exc.detail),
                    "status_code": exc.status_code,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Validation error at {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "message": "Validation error",
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "details": exc.errors(),
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled error at {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "message": "Internal server error occurred",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
            },
        )
