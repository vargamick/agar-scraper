"""
Authentication middleware (placeholder for future use).

Currently authentication is handled via dependencies.
This middleware could be used for additional auth processing.
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware (placeholder).

    Note: Currently authentication is handled via FastAPI dependencies.
    This middleware is reserved for additional authentication processing
    if needed in the future.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize authentication middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request (currently just passes through).

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response from the handler
        """
        # Currently just pass through
        # Can add global auth logic here if needed
        response = await call_next(request)
        return response
