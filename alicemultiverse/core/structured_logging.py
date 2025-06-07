"""Structured logging with correlation IDs for distributed tracing."""

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

import structlog
from structlog.processors import CallsiteParameter

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_correlation_id() -> str:
    """Get current correlation ID or generate a new one."""
    correlation_id = correlation_id_var.get()
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return request_id_var.get()


def set_request_id(request_id: str):
    """Set request ID for current context."""
    request_id_var.set(request_id)


class StructuredLogger:
    """Structured logger with correlation ID support."""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
        self.name = name
    
    def _add_context(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Add context information to log event."""
        # Add correlation and request IDs
        event_dict['correlation_id'] = get_correlation_id()
        request_id = get_request_id()
        if request_id:
            event_dict['request_id'] = request_id
        
        # Add service metadata
        event_dict['service'] = 'alicemultiverse'
        event_dict['logger'] = self.name
        
        return event_dict
    
    def bind(self, **kwargs) -> 'StructuredLogger':
        """Bind additional context to logger."""
        self.logger = self.logger.bind(**kwargs)
        return self
    
    def info(self, msg: str, **kwargs):
        """Log info message."""
        event_dict = self._add_context(kwargs)
        self.logger.info(msg, **event_dict)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        event_dict = self._add_context(kwargs)
        self.logger.warning(msg, **event_dict)
    
    def error(self, msg: str, exc_info: bool = False, **kwargs):
        """Log error message."""
        event_dict = self._add_context(kwargs)
        if exc_info:
            event_dict['exc_info'] = True
        self.logger.error(msg, **event_dict)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        event_dict = self._add_context(kwargs)
        self.logger.debug(msg, **event_dict)
    
    def critical(self, msg: str, **kwargs):
        """Log critical message."""
        event_dict = self._add_context(kwargs)
        self.logger.critical(msg, **event_dict)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


# Custom processors for structlog
def add_timestamp(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO timestamp to log event."""
    event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return event_dict


def add_log_level(_, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add log level to event dict."""
    event_dict['level'] = method_name.upper()
    return event_dict


def censor_sensitive_data(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Censor sensitive data in logs."""
    sensitive_keys = {
        'password', 'api_key', 'secret', 'token', 'authorization',
        'credit_card', 'ssn', 'private_key'
    }
    
    def censor_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        censored = {}
        for key, value in d.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                censored[key] = '***REDACTED***'
            elif isinstance(value, dict):
                censored[key] = censor_dict(value)
            else:
                censored[key] = value
        return censored
    
    return censor_dict(event_dict)


def setup_structured_logging(
    log_level: str = 'INFO',
    json_logs: bool = True,
    include_caller_info: bool = True
):
    """Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Output logs as JSON (for production)
        include_caller_info: Include file/function/line info
    """
    # Configure processors
    processors = [
        structlog.stdlib.filter_by_level,
        add_timestamp,
        add_log_level,
        structlog.stdlib.add_logger_name,
        censor_sensitive_data,
    ]
    
    if include_caller_info:
        processors.extend([
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    CallsiteParameter.FILENAME,
                    CallsiteParameter.FUNC_NAME,
                    CallsiteParameter.LINENO,
                ]
            ),
        ])
    
    processors.extend([
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ])
    
    # Configure output format
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Redirect standard logging to structlog
    logging.getLogger().handlers = [
        logging.StreamHandler(sys.stdout)
    ]
    
    # Log initialization
    logger = get_logger(__name__)
    logger.info(
        "Structured logging initialized",
        log_level=log_level,
        json_logs=json_logs,
        include_caller_info=include_caller_info
    )


# Decorators for tracing
def trace_operation(operation_name: str):
    """Decorator to trace function execution with timing."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            logger.info(
                f"Starting {operation_name}",
                operation=operation_name,
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Completed {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    duration_seconds=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Failed {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    duration_seconds=duration,
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            logger.info(
                f"Starting {operation_name}",
                operation=operation_name,
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Completed {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    duration_seconds=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Failed {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    duration_seconds=duration,
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_api_call(provider: str, model: str, operation: str):
    """Log API call details."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            correlation_id = get_correlation_id()
            
            logger.info(
                "API call started",
                provider=provider,
                model=model,
                operation=operation,
                correlation_id=correlation_id
            )
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Extract cost if available
                cost = None
                if hasattr(result, 'cost'):
                    cost = result.cost
                
                logger.info(
                    "API call completed",
                    provider=provider,
                    model=model,
                    operation=operation,
                    duration_seconds=duration,
                    cost=cost,
                    correlation_id=correlation_id,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "API call failed",
                    provider=provider,
                    model=model,
                    operation=operation,
                    duration_seconds=duration,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    correlation_id=correlation_id,
                    success=False,
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar implementation for sync functions
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Context managers for correlation IDs
class CorrelationContext:
    """Context manager for correlation ID."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.token = None
    
    def __enter__(self):
        self.token = correlation_id_var.set(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            correlation_id_var.reset(self.token)


class RequestContext:
    """Context manager for request ID."""
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.token = None
    
    def __enter__(self):
        self.token = request_id_var.set(self.request_id)
        return self.request_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            request_id_var.reset(self.token)