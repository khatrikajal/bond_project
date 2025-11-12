import logging
import traceback
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied as DjangoPermissionDenied
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    APIException,
)
from .response import APIResponse
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Centralized and production-grade exception handler for DRF.

    - Standardizes all API error responses using APIResponse
    - Captures Django and DRF exceptions
    - Logs unexpected server errors for debugging / monitoring
    """

    # First, let DRF handle its built-in exceptions
    response = exception_handler(exc, context)

    # ✅ CASE 1: DRF handled exception (ValidationError, NotAuthenticated, etc.)
    if response is not None:
        message, errors = _extract_error_message_and_details(exc, response.data)

        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=response.status_code,
        )

    # ✅ CASE 2: Handle Django Http404 / ObjectDoesNotExist
    if isinstance(exc, (Http404, ObjectDoesNotExist, NotFound)):
        return APIResponse.error(
            message="Resource not found",
            errors={"detail": str(exc)},
            status_code=404,
        )

    # ✅ CASE 3: Handle permission errors from Django (non-DRF)
    if isinstance(exc, DjangoPermissionDenied):
        return APIResponse.error(
            message="Permission denied",
            errors={"detail": str(exc)},
            status_code=403,
        )

    # ✅ CASE 4: Handle all unhandled exceptions (500 errors)
    _log_unexpected_exception(exc, context)
    return APIResponse.error(
        message="Internal server error" if settings.DEBUG is False else str(exc),
        errors={"detail": str(exc)} if settings.DEBUG else None,
        status_code=500,
    )


def _extract_error_message_and_details(exc, data):
    """
    Extracts a readable error message and details from DRF's exception response.
    """

    # Default fallback message
    message = "An error occurred"
    errors = data

    if isinstance(exc, ValidationError):
        message = "Validation failed"
    elif isinstance(exc, NotAuthenticated):
        message = "Authentication credentials were not provided"
    elif isinstance(exc, PermissionDenied):
        message = "Permission denied"
    elif isinstance(exc, NotFound):
        message = "Resource not found"
    elif isinstance(exc, APIException):
        # Many DRF exceptions have a `.detail` attribute
        if hasattr(exc, "detail"):
            if isinstance(exc.detail, dict):
                message = "Request failed"
            else:
                message = str(exc.detail)
    return message, errors


def _log_unexpected_exception(exc, context):
    """
    Logs unexpected exceptions with traceback for debugging or monitoring.
    Integrate with Sentry / Datadog / etc. here.
    """
    view = context.get("view")
    view_name = view.__class__.__name__ if view else "UnknownView"
    logger.error(
        f"Unhandled exception in {view_name}: {exc}",
        exc_info=True,  # includes full traceback
        extra={"context": context},
    )
