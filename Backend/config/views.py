from django.http import JsonResponse


def custom_page_not_found(request, exception, template_name=None):
    """
    Custom 404 handler that returns a JSON response for API requests
    and falls back to the default handler for other requests.
    """
    return JsonResponse({
        "error": "Not Found",
        "message": "The requested resource was not found.",
        "status_code": 404,
    }, status=404)
