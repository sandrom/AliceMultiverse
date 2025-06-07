"""Base classes and utilities for MCP tools."""

import logging
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

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
    data: Optional[Any] = None,
    error: Optional[str] = None,
    message: Optional[str] = None
) -> List[TextContent]:
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
        response["data"] = data
    if error is not None:
        response["error"] = error
    if message is not None:
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


def handle_errors(func: ToolFunc) -> ToolFunc:
    """Decorator to handle errors in MCP tools.
    
    Catches exceptions and returns standardized error responses.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            return create_tool_response(
                success=False,
                error=str(e),
                message="Invalid input parameters"
            )
        except ServiceError as e:
            logger.error(f"Service error in {func.__name__}: {e}")
            return create_tool_response(
                success=False,
                error=str(e),
                message="Service operation failed"
            )
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return create_tool_response(
                success=False,
                error=f"Unexpected error: {type(e).__name__}: {str(e)}",
                message="An unexpected error occurred"
            )
    
    return wrapper


def validate_path(path: str, must_exist: bool = False) -> Path:
    """Validate and convert a path string.
    
    Args:
        path: Path string to validate
        must_exist: Whether the path must exist
        
    Returns:
        Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    try:
        path_obj = Path(path).expanduser().resolve()
        
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}")
        
        return path_obj
    except Exception as e:
        raise ValidationError(f"Invalid path '{path}': {e}")


def validate_positive_int(value: Any, name: str) -> int:
    """Validate a positive integer value.
    
    Args:
        value: Value to validate
        name: Parameter name for error messages
        
    Returns:
        Validated integer
        
    Raises:
        ValidationError: If value is invalid
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValidationError(f"{name} must be positive, got {int_value}")
        return int_value
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a positive integer, got {type(value).__name__}")


def validate_enum(value: str, allowed: List[str], name: str) -> str:
    """Validate an enum-like string value.
    
    Args:
        value: Value to validate
        allowed: List of allowed values
        name: Parameter name for error messages
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If value not in allowed list
    """
    if value not in allowed:
        raise ValidationError(
            f"{name} must be one of {allowed}, got '{value}'"
        )
    return value


class LazyServiceLoader:
    """Lazy loader for services to improve startup time."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._loaders: Dict[str, Callable[[], Any]] = {}
    
    def register(self, name: str, loader: Callable[[], Any]) -> None:
        """Register a service loader.
        
        Args:
            name: Service name
            loader: Function that creates/returns the service
        """
        self._loaders[name] = loader
    
    def get(self, name: str) -> Any:
        """Get a service, loading it if necessary.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            ServiceError: If service not registered or loading fails
        """
        if name not in self._loaders:
            raise ServiceError(f"Service '{name}' not registered")
        
        if name not in self._services:
            try:
                self._services[name] = self._loaders[name]()
            except Exception as e:
                raise ServiceError(f"Failed to load service '{name}': {e}")
        
        return self._services[name]
    
    def is_loaded(self, name: str) -> bool:
        """Check if a service is loaded.
        
        Args:
            name: Service name
            
        Returns:
            True if loaded
        """
        return name in self._services


# Global service loader instance
services = LazyServiceLoader()


def create_tool_definition(
    name: str,
    description: str,
    parameters: Dict[str, Any]
) -> Tool:
    """Create a tool definition helper.
    
    Args:
        name: Tool name
        description: Tool description
        parameters: Parameter schema
        
    Returns:
        Tool definition
    """
    return Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": parameters,
            "required": [k for k, v in parameters.items() if v.get("required", True)]
        }
    )