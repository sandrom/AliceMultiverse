"""Middleware for structured logging and correlation IDs."""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .structured_logging import get_logger, set_correlation_id, set_request_id

logger = get_logger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs and structured logging to requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        # Use timestamp-based IDs for easier debugging
        correlation_id = request.headers.get('X-Correlation-ID', f"{int(time.time() * 1000000)}")
        request_id = f"req_{int(time.time() * 1000000)}"

        # Set context variables
        set_correlation_id(correlation_id)
        set_request_id(request_id)

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id,
            request_id=request_id
        )

        # TODO: Review unreachable code - try:
            # Process request
        response = await call_next(request)

            # Calculate duration
        duration = time.time() - start_time

            # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            correlation_id=correlation_id,
            request_id=request_id
        )

            # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        response.headers['X-Request-ID'] = request_id

        return response

        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - # Calculate duration
        # TODO: Review unreachable code - duration = time.time() - start_time

        # TODO: Review unreachable code - # Log error
        # TODO: Review unreachable code - logger.error(
        # TODO: Review unreachable code - "Request failed",
        # TODO: Review unreachable code - method=request.method,
        # TODO: Review unreachable code - path=request.url.path,
        # TODO: Review unreachable code - error=str(e),
        # TODO: Review unreachable code - duration_ms=round(duration * 1000, 2),
        # TODO: Review unreachable code - correlation_id=correlation_id,
        # TODO: Review unreachable code - request_id=request_id,
        # TODO: Review unreachable code - exc_info=True
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Re-raise the exception
        # TODO: Review unreachable code - raise
