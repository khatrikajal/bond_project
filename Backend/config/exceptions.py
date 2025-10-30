# ruff: noqa: ERA001
import sentry_sdk
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def extract_error_messages(data):
    """
    Recursively extract error messages.

    If data is a dict without a sole "detail" key,
    build a list of field error dicts.
    """
    if isinstance(data, dict):
        if "detail" in data and len(data) == 1:
            return str(data["detail"])
        errors = []
        for key, value in data.items():
            error_message = extract_error_messages(value)
            errors.append({key: error_message})
        return errors
    if isinstance(data, list):
        if len(data) == 1:
            return extract_error_messages(data[0])
        return [extract_error_messages(item) for item in data]
    return str(data)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.

    It returns a consistent error response format.
    For a simple error:
    {
        "error": "Invalid OTP or OTP expired."
    }
    For field errors:
    {
        "error": [
            {"firstName": "This field is required"},
            {"lastName": "This field is required"}
        ]
    }
    """
    response = drf_exception_handler(exc, context)
    if response is not None:
        # Extract errors based on the structure of response.data
        message = extract_error_messages(response.data)
        response.data = {"error": message}
    else:
        if not settings.DEBUG:
            sentry_sdk.capture_exception(exc)

        # Fallback for exceptions not handled by DRF.
        message = str(exc) if settings.DEBUG else "An unexpected error occurred"
        response = Response(
            {"error": message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response["Content-Type"] = "application/json"
    return response
