"""AI-friendly error handling utilities."""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AIFriendlyError:
    """Converts technical errors into AI-friendly messages."""
    
    # Map of technical error patterns to friendly messages
    ERROR_MAPPINGS = {
        # File system errors
        "No such file or directory": {
            "message": "The specified file or folder doesn't exist",
            "suggestions": [
                "Check if the path is spelled correctly",
                "Ensure the file hasn't been moved or deleted",
                "Try using a different location"
            ]
        },
        "Read-only file system": {
            "message": "Cannot write to this location - it's read-only",
            "suggestions": [
                "Choose a different folder with write permissions",
                "Check if the disk is full",
                "Ensure you have permission to write here"
            ]
        },
        "Permission denied": {
            "message": "You don't have permission to access this file or folder",
            "suggestions": [
                "Check file permissions",
                "Try running with appropriate permissions",
                "Choose a location you have access to"
            ]
        },
        "File exists": {
            "message": "A file with this name already exists",
            "suggestions": [
                "Choose a different name",
                "Delete the existing file first",
                "Use the --force flag to overwrite"
            ]
        },
        
        # API errors
        "rate limit": {
            "message": "API rate limit reached - too many requests",
            "suggestions": [
                "Wait a few minutes before trying again",
                "Reduce the number of images being processed",
                "Consider upgrading your API plan"
            ]
        },
        "API key": {
            "message": "API authentication failed",
            "suggestions": [
                "Check if your API key is configured correctly",
                "Run 'alice keys setup' to configure API keys",
                "Verify your API key hasn't expired"
            ]
        },
        "connection": {
            "message": "Cannot connect to the service",
            "suggestions": [
                "Check your internet connection",
                "Verify the service is available",
                "Try again in a few moments"
            ]
        },
        
        # Media processing errors
        "not a valid image": {
            "message": "This file isn't a valid image format",
            "suggestions": [
                "Supported formats: PNG, JPG, WebP, HEIC",
                "Check if the file is corrupted",
                "Try converting to a supported format"
            ]
        },
        "corrupt": {
            "message": "This file appears to be corrupted",
            "suggestions": [
                "Try downloading or generating the file again",
                "Check if the file was fully transferred",
                "Use a file repair tool if available"
            ]
        },
        
        # Configuration errors
        "configuration": {
            "message": "There's an issue with the configuration",
            "suggestions": [
                "Check your settings.yaml file",
                "Ensure all required settings are present",
                "Use default settings by removing custom config"
            ]
        },
        "missing required": {
            "message": "A required setting or parameter is missing",
            "suggestions": [
                "Check the documentation for required settings",
                "Provide all necessary parameters",
                "Use --help to see available options"
            ]
        }
    }
    
    @classmethod
    def make_friendly(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert an exception to an AI-friendly error response.
        
        Args:
            error: The exception to convert
            context: Optional context about what was being attempted
            
        Returns:
            Dictionary with friendly error information
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Find matching error pattern
        friendly_info = None
        for pattern, info in cls.ERROR_MAPPINGS.items():
            if pattern.lower() in error_str:
                friendly_info = info
                break
        
        # Default friendly message if no pattern matches
        if not friendly_info:
            friendly_info = {
                "message": cls._default_message(error_type, error_str),
                "suggestions": cls._default_suggestions(error_type)
            }
        
        # Build response
        response = {
            "error": friendly_info["message"],
            "technical_details": f"{error_type}: {str(error)}",
            "suggestions": friendly_info["suggestions"]
        }
        
        # Add context if provided
        if context:
            response["context"] = context
            
        # Log the technical error for debugging
        logger.debug(f"Technical error: {error_type}: {str(error)}")
        
        return response
    
    @staticmethod
    def _default_message(error_type: str, error_str: str) -> str:
        """Generate a default friendly message."""
        if "timeout" in error_str:
            return "The operation took too long to complete"
        elif "memory" in error_str:
            return "Not enough memory to complete this operation"
        elif "disk space" in error_str:
            return "Not enough disk space available"
        else:
            return f"An unexpected error occurred while processing your request"
    
    @staticmethod
    def _default_suggestions(error_type: str) -> List[str]:
        """Generate default suggestions based on error type."""
        if "Timeout" in error_type:
            return [
                "Try processing fewer items at once",
                "Check if the service is responding slowly",
                "Increase timeout settings if possible"
            ]
        elif "Memory" in error_type:
            return [
                "Try processing fewer items at once",
                "Close other applications to free memory",
                "Process images in smaller batches"
            ]
        else:
            return [
                "Try the operation again",
                "Check the logs for more details",
                "Contact support if the issue persists"
            ]


def wrap_error_response(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to automatically convert exceptions to AI-friendly responses.
    
    Use this on interface methods to ensure all errors are AI-friendly.
    """
    def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Extract context from the function call
            context = {
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()) if kwargs else []
            }
            
            # Create friendly error
            friendly_error = AIFriendlyError.make_friendly(e, context)
            
            # Return in expected format
            return {
                "success": False,
                "message": friendly_error["error"],
                "data": None,
                "error": friendly_error["technical_details"],
                "suggestions": friendly_error.get("suggestions", [])
            }
    
    return wrapper