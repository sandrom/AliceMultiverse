"""Common decorators for MCP tools."""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from ..base import ServiceError, ValidationError, create_tool_response, services

ToolFunc = TypeVar("ToolFunc", bound=Callable[..., Any])


def require_service(service_name: str) -> Callable[[ToolFunc], ToolFunc]:
    """Decorator to ensure a service is available before tool execution.
    
    Args:
        service_name: Name of required service
        
    Returns:
        Decorator function
    """
    def decorator(func: ToolFunc) -> ToolFunc:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Ensure service is available
                service = services.get(service_name)
                if service is None:
                    raise ServiceError(f"{service_name} service not available")
                
                # Call original function
                return await func(*args, **kwargs)
                
            except ServiceError as e:
                return create_tool_response(
                    success=False,
                    error=str(e),
                    message=f"Required service '{service_name}' is not available"
                )
        
        return wrapper
    return decorator


def validate_params(**validators: Dict[str, Callable[[Any], Any]]) -> Callable[[ToolFunc], ToolFunc]:
    """Decorator to validate tool parameters.
    
    Args:
        **validators: Mapping of parameter names to validation functions
        
    Returns:
        Decorator function
        
    Example:
        @validate_params(
            limit=lambda x: validate_positive_int(x, "limit"),
            path=lambda x: validate_path(x, must_exist=True)
        )
        async def my_tool(limit: int, path: str):
            ...
    """
    def decorator(func: ToolFunc) -> ToolFunc:
        @wraps(func)
        async def wrapper(**kwargs):
            # Validate each parameter
            validated_params = {}
            
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    try:
                        validated_params[param_name] = validator(kwargs[param_name])
                    except ValidationError:
                        raise  # Re-raise validation errors
                    except Exception as e:
                        raise ValidationError(f"Invalid {param_name}: {e}")
                else:
                    # Pass through if not in kwargs (might be optional)
                    pass
            
            # Merge validated params back
            kwargs.update(validated_params)
            
            # Call original function
            return await func(**kwargs)
        
        return wrapper
    return decorator