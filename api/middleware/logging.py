"""
Logging middleware for the API.

Logs all incoming requests and outgoing responses.
"""

import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.

    Logs request method, path, processing time, and response status.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize logging middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response from the handler
        """
        # Start timer
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log successful request
            logger.info(
                f"{method} {path} - {response.status_code} - "
                f"{process_time:.3f}s - {client_host}"
            )

            # Add custom header with processing time
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log failed request
            logger.error(
                f"{method} {path} - ERROR - {process_time:.3f}s - "
                f"{client_host} - {str(e)}"
            )

            # Re-raise exception to be handled by exception handlers
            raise
