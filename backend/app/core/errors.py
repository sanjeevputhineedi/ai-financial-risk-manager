import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.logging import logger


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED"
        )


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_DENIED"
        )


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND"
        )


class InsufficientBalanceError(AppException):
    def __init__(self, message: str = "Insufficient account balance"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INSUFFICIENT_BALANCE"
        )


class InvalidStateTransitionError(AppException):
    def __init__(self, message: str = "Invalid transaction state transition"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_STATE_TRANSITION"
        )


class DuplicateIdempotencyError(AppException):
    def __init__(self, message: str = "Duplicate transaction request detected"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_IDEMPOTENCY_KEY"
        )


class HeldPaymentActionError(AppException):
    def __init__(self, message: str = "Cannot process action on held payment"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="HELD_PAYMENT_ACTION_ERROR"
        )


class MLServiceError(AppException):
    def __init__(self, message: str = "ML Risk Assessment Engine unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="ML_SERVICE_UNAVAILABLE"
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(f"AppException on {request.method} {request.url.path}: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request parameters or payload failed validation",
                "details": {"errors": exc.errors()},
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {},
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred",
                "details": {},
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )
