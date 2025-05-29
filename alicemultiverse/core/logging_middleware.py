"""Middleware for structured logging and correlation IDs."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .structured_logging import (
    get_logger, 
    set_correlation_id, 
    set_request_id,
    CorrelationContext,
    RequestContext
)

logger = get_logger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs and structured logging to requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        request_id = str(uuid.uuid4())
        
        # Set context variables
        set_correlation_id(correlation_id)
        set_request_id(request_id)
        
        # Add to request state for access in handlers
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
            correlation_id=correlation_id,
            request_id=request_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration,
                correlation_id=correlation_id,
                request_id=request_id
            )
            
            # Add correlation ID to response headers
            response.headers['X-Correlation-ID'] = correlation_id
            response.headers['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                duration_seconds=duration,
                error_type=type(e).__name__,
                error_message=str(e),
                correlation_id=correlation_id,
                request_id=request_id,
                exc_info=True
            )
            
            # Re-raise to let FastAPI handle it
            raise


class DatabaseQueryLoggingMiddleware:
    """Middleware to log slow database queries."""
    
    def __init__(self, slow_query_threshold: float = 1.0):
        """Initialize middleware.
        
        Args:
            slow_query_threshold: Threshold in seconds for slow query logging
        """
        self.slow_query_threshold = slow_query_threshold
        self.logger = get_logger(__name__)
    
    def __call__(self, execute, sql, parameters, context):
        """Log database queries."""
        start_time = time.time()
        
        try:
            result = execute(sql, parameters, context)
            duration = time.time() - start_time
            
            # Log slow queries
            if duration > self.slow_query_threshold:
                self.logger.warning(
                    "Slow database query detected",
                    query=str(sql)[:200],  # First 200 chars
                    duration_seconds=duration,
                    parameter_count=len(parameters) if parameters else 0
                )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            self.logger.error(
                "Database query failed",
                query=str(sql)[:200],
                duration_seconds=duration,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise


def setup_sqlalchemy_logging(engine):
    """Setup SQLAlchemy query logging.
    
    Args:
        engine: SQLAlchemy engine
    """
    from sqlalchemy import event
    
    middleware = DatabaseQueryLoggingMiddleware()
    
    @event.listens_for(engine, "before_execute")
    def before_execute(conn, clauseelement, multiparams, params, execution_options):
        conn.info['query_start_time'] = time.time()
        conn.info['sql'] = str(clauseelement)
    
    @event.listens_for(engine, "after_execute")
    def after_execute(conn, clauseelement, multiparams, params, execution_options, result):
        duration = time.time() - conn.info.get('query_start_time', time.time())
        
        if duration > middleware.slow_query_threshold:
            logger.warning(
                "Slow query detected",
                query=conn.info.get('sql', str(clauseelement))[:200],
                duration_seconds=duration,
                rows_returned=result.rowcount if hasattr(result, 'rowcount') else None
            )