import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

from config.websocket import websocket_application

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR / "apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

django_application = get_asgi_application()


async def application(scope, receive, send):
    """
    ASGI entry point to the application.

    This function determines whether the request is for HTTP or WebSocket
    and calls the appropriate application. If the request type is unknown,
    it raises a NotImplementedError.

    """

    if scope["type"] == "http":
        # Call the Django ASGI application to handle the request.
        await django_application(scope, receive, send)
    elif scope["type"] == "websocket":
        # Call the WebSocket application to handle the request.
        await websocket_application(scope, receive, send)
    else:
        # Raise an error for unknown request types.
        msg = f"Unknown scope type {scope['type']}"
        raise NotImplementedError(msg)
