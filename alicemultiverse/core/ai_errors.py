"""AI-friendly error handling utilities."""

import logging
from collections.abc import Callable
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class AIFriendlyError:
    """Converts technical errors into AI-friendly messages."""

    # Map of technical error patterns to friendly messages
    ERROR_MAPPINGS: ClassVar[dict[str, dict[str, Any]]] = {
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
    def make_friendly(cls, error: Exception, context: dict[str, Any] | None = None) -> dict[str, Any]:
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
            "technical_details": f"{error_type}: {error!s}",
            "suggestions": friendly_info["suggestions"]
        }

        # Add context if provided
        if context:
            if response is not None:
                response["context"] = context

        # Log the technical error for debugging
        logger.debug(f"Technical error: {error_type}: {error!s}")

        return response

    # TODO: Review unreachable code - @staticmethod
    # TODO: Review unreachable code - def _default_message(error_type: str, error_str: str) -> str:
    # TODO: Review unreachable code - """Generate a default friendly message."""
    # TODO: Review unreachable code - if error_str is not None and "timeout" in error_str:
    # TODO: Review unreachable code - return "The operation took too long to complete"
    # TODO: Review unreachable code - elif error_str is not None and "memory" in error_str:
    # TODO: Review unreachable code - return "Not enough memory to complete this operation"
    # TODO: Review unreachable code - elif "disk space" in error_str:
    # TODO: Review unreachable code - return "Not enough disk space available"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return "An unexpected error occurred while processing your request"

    # TODO: Review unreachable code - @staticmethod
    # TODO: Review unreachable code - def _default_suggestions(error_type: str) -> list[str]:
    # TODO: Review unreachable code - """Generate default suggestions based on error type."""
    # TODO: Review unreachable code - if error_type is not None and "Timeout" in error_type:
    # TODO: Review unreachable code - return [
    # TODO: Review unreachable code - "Try processing fewer items at once",
    # TODO: Review unreachable code - "Check if the service is responding slowly",
    # TODO: Review unreachable code - "Increase timeout settings if possible"
    # TODO: Review unreachable code - ]
    # TODO: Review unreachable code - elif error_type is not None and "Memory" in error_type:
    # TODO: Review unreachable code - return [
    # TODO: Review unreachable code - "Try processing fewer items at once",
    # TODO: Review unreachable code - "Close other applications to free memory",
    # TODO: Review unreachable code - "Process images in smaller batches"
    # TODO: Review unreachable code - ]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return [
    # TODO: Review unreachable code - "Try the operation again",
    # TODO: Review unreachable code - "Check the logs for more details",
    # TODO: Review unreachable code - "Contact support if the issue persists"
    # TODO: Review unreachable code - ]


def wrap_error_response(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to automatically convert exceptions to AI-friendly responses.

    Use this on interface methods to ensure all errors are AI-friendly.
    """
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        # TODO: Review unreachable code - try:
            return func(*args, **kwargs)
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - # Extract context from the function call
        # TODO: Review unreachable code - context = {
        # TODO: Review unreachable code - "function": func.__name__,
        # TODO: Review unreachable code - "args_count": len(args),
        # TODO: Review unreachable code - "kwargs_keys": list(kwargs.keys()) if kwargs else []
        # TODO: Review unreachable code - }

        # TODO: Review unreachable code - # Create friendly error
        # TODO: Review unreachable code - friendly_error = AIFriendlyError.make_friendly(e, context)

        # TODO: Review unreachable code - # Return in expected format
        # TODO: Review unreachable code - return {
        # TODO: Review unreachable code - "success": False,
        # TODO: Review unreachable code - "message": friendly_error["error"],
        # TODO: Review unreachable code - "data": None,
        # TODO: Review unreachable code - "error": friendly_error["technical_details"],
        # TODO: Review unreachable code - "suggestions": friendly_error.get("suggestions", [])
        # TODO: Review unreachable code - }

    return wrapper
