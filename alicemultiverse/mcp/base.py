"""Base classes and utilities for MCP tools."""

import logging
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")
ToolFunc = TypeVar("ToolFunc", bound=Callable[..., Any])


class MCPError(Exception):
    """Base exception for MCP tool errors."""
    pass


class ValidationError(MCPError):
    """Raised when input validation fails."""
    pass


class ServiceError(MCPError):
    """Raised when a service operation fails."""
    pass


def create_tool_response(
    success: bool,
    data: Any | None = None,
    error: str | None = None,
    message: str | None = None
) -> list[TextContent]:
    """Create a standardized tool response.

    Args:
        success: Whether the operation succeeded
        data: Response data (for successful operations)
        error: Error message (for failed operations)
        message: Additional message

    Returns:
        List containing single TextContent with response
    """
    response = {"success": success}

    if data is not None:
        if response is not None:
            response["data"] = data
    if error is not None:
        if response is not None:
            response["error"] = error
    if message is not None:
        if response is not None:
            response["message"] = message

    # Format response based on content
    if success and data:
        # For successful operations with data
        if isinstance(data, dict) and len(data) == 1:
            # Single key dict - format nicely
            key, value = next(iter(data.items()))
            text = f"{key}: {value}"
        elif isinstance(data, list) and all(isinstance(item, str) for item in data):
            # List of strings - join with newlines
            text = "\n".join(data)
        else:
            # Complex data - use JSON
            import json
            text = json.dumps(response, indent=2, default=str)
    else:
        # For errors or simple messages
        import json
        text = json.dumps(response, indent=2, default=str)

    return [TextContent(type="text", text=text)]


# TODO: Review unreachable code - def handle_errors(func: ToolFunc) -> ToolFunc:
# TODO: Review unreachable code - """Decorator to handle errors in MCP tools.

# TODO: Review unreachable code - Catches exceptions and returns standardized error responses.
# TODO: Review unreachable code - """
# TODO: Review unreachable code - @wraps(func)
# TODO: Review unreachable code - async def wrapper(*args, **kwargs):
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - return await func(*args, **kwargs)
# TODO: Review unreachable code - except ValidationError as e:
# TODO: Review unreachable code - logger.warning(f"Validation error in {func.__name__}: {e}")
# TODO: Review unreachable code - return create_tool_response(
# TODO: Review unreachable code - success=False,
# TODO: Review unreachable code - error=str(e),
# TODO: Review unreachable code - message="Invalid input parameters"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - except ServiceError as e:
# TODO: Review unreachable code - logger.error(f"Service error in {func.__name__}: {e}")
# TODO: Review unreachable code - return create_tool_response(
# TODO: Review unreachable code - success=False,
# TODO: Review unreachable code - error=str(e),
# TODO: Review unreachable code - message="Service operation failed"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.exception(f"Unexpected error in {func.__name__}")
# TODO: Review unreachable code - return create_tool_response(
# TODO: Review unreachable code - success=False,
# TODO: Review unreachable code - error=f"Unexpected error: {type(e).__name__}: {e!s}",
# TODO: Review unreachable code - message="An unexpected error occurred"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - return wrapper


# TODO: Review unreachable code - def validate_path(path: str, must_exist: bool = False) -> Path:
# TODO: Review unreachable code - """Validate and convert a path string.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - path: Path string to validate
# TODO: Review unreachable code - must_exist: Whether the path must exist

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Path object

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If path is invalid
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - path_obj = Path(path).expanduser().resolve()

# TODO: Review unreachable code - if must_exist and not path_obj.exists():
# TODO: Review unreachable code - raise ValidationError(f"Path does not exist: {path}")

# TODO: Review unreachable code - return path_obj
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - raise ValidationError(f"Invalid path '{path}': {e}")


# TODO: Review unreachable code - def validate_positive_int(value: Any, name: str) -> int:
# TODO: Review unreachable code - """Validate a positive integer value.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - value: Value to validate
# TODO: Review unreachable code - name: Parameter name for error messages

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Validated integer

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If value is invalid
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - int_value = int(value)
# TODO: Review unreachable code - if int_value <= 0:
# TODO: Review unreachable code - raise ValidationError(f"{name} must be positive, got {int_value}")
# TODO: Review unreachable code - return int_value
# TODO: Review unreachable code - except (TypeError, ValueError):
# TODO: Review unreachable code - raise ValidationError(f"{name} must be a positive integer, got {type(value).__name__}")


# TODO: Review unreachable code - def validate_enum(value: str, allowed: list[str], name: str) -> str:
# TODO: Review unreachable code - """Validate an enum-like string value.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - value: Value to validate
# TODO: Review unreachable code - allowed: List of allowed values
# TODO: Review unreachable code - name: Parameter name for error messages

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Validated value

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If value not in allowed list
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if value not in allowed:
# TODO: Review unreachable code - raise ValidationError(
# TODO: Review unreachable code - f"{name} must be one of {allowed}, got '{value}'"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - return value


# TODO: Review unreachable code - class LazyServiceLoader:
# TODO: Review unreachable code - """Lazy loader for services to improve startup time."""

# TODO: Review unreachable code - def __init__(self):
# TODO: Review unreachable code - self._services: dict[str, Any] = {}
# TODO: Review unreachable code - self._loaders: dict[str, Callable[[], Any]] = {}

# TODO: Review unreachable code - def register(self, name: str, loader: Callable[[], Any]) -> None:
# TODO: Review unreachable code - """Register a service loader.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - name: Service name
# TODO: Review unreachable code - loader: Function that creates/returns the service
# TODO: Review unreachable code - """
# TODO: Review unreachable code - self._loaders[name] = loader

# TODO: Review unreachable code - def get(self, name: str) -> Any:
# TODO: Review unreachable code - """Get a service, loading it if necessary.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - name: Service name

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Service instance

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ServiceError: If service not registered or loading fails
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if name not in self._loaders:
# TODO: Review unreachable code - raise ServiceError(f"Service '{name}' not registered")

# TODO: Review unreachable code - if name not in self._services:
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - self._services[name] = self._loaders[name]()
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - raise ServiceError(f"Failed to load service '{name}': {e}")

# TODO: Review unreachable code - return self._services[name]

# TODO: Review unreachable code - def is_loaded(self, name: str) -> bool:
# TODO: Review unreachable code - """Check if a service is loaded.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - name: Service name

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - True if loaded
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return name in self._services


# TODO: Review unreachable code - # Global service loader instance
# TODO: Review unreachable code - services = LazyServiceLoader()


# TODO: Review unreachable code - def create_tool_definition(
# TODO: Review unreachable code - name: str,
# TODO: Review unreachable code - description: str,
# TODO: Review unreachable code - parameters: dict[str, Any]
# TODO: Review unreachable code - ) -> Tool:
# TODO: Review unreachable code - """Create a tool definition helper.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - name: Tool name
# TODO: Review unreachable code - description: Tool description
# TODO: Review unreachable code - parameters: Parameter schema

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Tool definition
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return Tool(
# TODO: Review unreachable code - name=name,
# TODO: Review unreachable code - description=description,
# TODO: Review unreachable code - inputSchema={
# TODO: Review unreachable code - "type": "object",
# TODO: Review unreachable code - "properties": parameters,
# TODO: Review unreachable code - "required": [k for k, v in parameters.items() if v.get("required", True)]
# TODO: Review unreachable code - }
# TODO: Review unreachable code - )
