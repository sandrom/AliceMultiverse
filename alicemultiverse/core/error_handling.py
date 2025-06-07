"""Enhanced error handling with helpful suggestions.

This module provides user-friendly error messages with actionable suggestions
for common issues in AliceMultiverse.
"""

import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    API_KEY = "api_key"
    FILE_PATH = "file_path"
    PERMISSION = "permission"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    COST_LIMIT = "cost_limit"
    DATABASE = "database"
    PROVIDER = "provider"
    UNKNOWN = "unknown"


class ErrorContext:
    """Context information for error handling."""
    
    def __init__(
        self,
        category: ErrorCategory,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.category = category
        self.operation = operation
        self.details = details or {}
        self.suggestions: List[str] = []


class UserFriendlyError(Exception):
    """Exception with user-friendly message and suggestions."""
    
    def __init__(
        self,
        message: str,
        context: ErrorContext,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.context = context
        self.original_error = original_error
        self.user_message = message
        
        # Generate suggestions based on context
        self.suggestions = self._generate_suggestions()
    
    def _generate_suggestions(self) -> List[str]:
        """Generate helpful suggestions based on error context."""
        suggestions = []
        
        if self.context.category == ErrorCategory.API_KEY:
            provider = self.context.details.get("provider", "unknown")
            suggestions.extend([
                f"Run 'alice keys setup' to configure your {provider} API key",
                f"Check if your {provider.upper()}_API_KEY environment variable is set",
                f"Verify your API key is valid at the {provider} dashboard",
                "Use a different provider with --providers flag"
            ])
            
        elif self.context.category == ErrorCategory.FILE_PATH:
            path = self.context.details.get("path", "unknown")
            suggestions.extend([
                f"Check if the path exists: {path}",
                "Use absolute paths instead of relative paths",
                "Ensure you have read permissions for the directory",
                f"Try: ls -la {Path(path).parent}" if path != "unknown" else "List the parent directory to check permissions"
            ])
            
        elif self.context.category == ErrorCategory.PERMISSION:
            path = self.context.details.get("path", "unknown")
            suggestions.extend([
                f"Check file permissions: ls -la {path}",
                f"Try: chmod +r {path}",
                "Run with appropriate user permissions",
                "Check if the file is locked by another process"
            ])
            
        elif self.context.category == ErrorCategory.DEPENDENCY:
            dependency = self.context.details.get("dependency", "unknown")
            suggestions.extend([
                f"Install missing dependency: pip install {dependency}",
                "Run: pip install -r requirements.txt",
                "Check if you're in the correct virtual environment",
                f"For {dependency}: check installation docs"
            ])
            
        elif self.context.category == ErrorCategory.CONFIGURATION:
            config_key = self.context.details.get("key", "unknown")
            suggestions.extend([
                "Check your settings.yaml file",
                f"Ensure '{config_key}' is properly configured",
                "Run with --debug to see configuration details",
                "Use 'alice config validate' to check configuration"
            ])
            
        elif self.context.category == ErrorCategory.NETWORK:
            url = self.context.details.get("url", "unknown")
            suggestions.extend([
                "Check your internet connection",
                f"Verify the service is accessible: {url}",
                "Check if you're behind a firewall or proxy",
                "Try again in a few moments (temporary issue)"
            ])
            
        elif self.context.category == ErrorCategory.COST_LIMIT:
            limit = self.context.details.get("limit", "unknown")
            spent = self.context.details.get("spent", "unknown")
            suggestions.extend([
                f"Current spending: ${spent}, Limit: ${limit}",
                "Increase limit with: alice set-budget --limit <amount>",
                "Use cheaper providers (e.g., --providers deepseek)",
                "Process fewer files or use --dry-run to preview"
            ])
            
        elif self.context.category == ErrorCategory.DATABASE:
            suggestions.extend([
                "Check if DuckDB file is corrupted",
                "Try rebuilding the index: alice index rebuild",
                "Delete search.duckdb and let it recreate",
                "Check disk space availability"
            ])
            
        elif self.context.category == ErrorCategory.PROVIDER:
            provider = self.context.details.get("provider", "unknown")
            suggestions.extend([
                f"Check {provider} service status",
                f"Verify {provider} API key is valid",
                "Try a different provider: --providers <other>",
                "Check rate limits for your account"
            ])
        
        # Add context-specific suggestions
        suggestions.extend(self.context.suggestions)
        
        return suggestions
    
    def format_error(self, include_traceback: bool = False) -> str:
        """Format error message with suggestions."""
        lines = [
            "❌ ERROR: " + self.user_message,
            ""
        ]
        
        if self.suggestions:
            lines.append("💡 Suggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"   {i}. {suggestion}")
            lines.append("")
        
        if self.context.details:
            lines.append("📋 Details:")
            for key, value in self.context.details.items():
                lines.append(f"   {key}: {value}")
            lines.append("")
        
        if include_traceback and self.original_error:
            lines.append("🔍 Technical Details:")
            lines.append("   " + str(self.original_error))
            if hasattr(self.original_error, "__traceback__"):
                tb_lines = traceback.format_tb(self.original_error.__traceback__)
                for line in tb_lines[-3:]:  # Show last 3 stack frames
                    lines.append("   " + line.strip())
        
        return "\n".join(lines)


def handle_api_key_error(provider: str, operation: str = "API call") -> UserFriendlyError:
    """Create user-friendly error for API key issues."""
    context = ErrorContext(
        ErrorCategory.API_KEY,
        operation,
        {"provider": provider}
    )
    
    return UserFriendlyError(
        f"Missing or invalid API key for {provider}",
        context
    )


def handle_file_not_found(path: Path, operation: str = "file access") -> UserFriendlyError:
    """Create user-friendly error for file not found."""
    context = ErrorContext(
        ErrorCategory.FILE_PATH,
        operation,
        {"path": str(path)}
    )
    
    # Add specific suggestions based on path
    if "test_data" in str(path):
        context.suggestions.append("Update your configuration to use real paths instead of test_data/")
    
    return UserFriendlyError(
        f"File or directory not found: {path}",
        context
    )


def handle_permission_error(path: Path, operation: str = "file access") -> UserFriendlyError:
    """Create user-friendly error for permission issues."""
    context = ErrorContext(
        ErrorCategory.PERMISSION,
        operation,
        {"path": str(path)}
    )
    
    return UserFriendlyError(
        f"Permission denied accessing: {path}",
        context
    )


def handle_dependency_error(dependency: str, operation: str = "import") -> UserFriendlyError:
    """Create user-friendly error for missing dependencies."""
    context = ErrorContext(
        ErrorCategory.DEPENDENCY,
        operation,
        {"dependency": dependency}
    )
    
    # Add specific suggestions for common dependencies
    if dependency == "mcp":
        context.suggestions.insert(0, "MCP is optional - use REST API mode if not needed")
    elif dependency == "redis":
        context.suggestions.insert(0, "Redis is optional - file-based events work without it")
    
    return UserFriendlyError(
        f"Missing required dependency: {dependency}",
        context
    )


def handle_cost_limit_error(
    spent: float,
    limit: float,
    operation: str = "processing"
) -> UserFriendlyError:
    """Create user-friendly error for cost limit exceeded."""
    context = ErrorContext(
        ErrorCategory.COST_LIMIT,
        operation,
        {"spent": f"{spent:.2f}", "limit": f"{limit:.2f}"}
    )
    
    return UserFriendlyError(
        f"Cost limit exceeded: ${spent:.2f} > ${limit:.2f}",
        context
    )


def wrap_error(error: Exception, operation: str = "operation") -> UserFriendlyError:
    """Wrap any exception in a user-friendly error."""
    # Try to categorize the error
    error_str = str(error).lower()
    
    if "api" in error_str and "key" in error_str:
        # Extract provider if possible
        provider = "unknown"
        for p in ["anthropic", "openai", "google", "deepseek"]:
            if p in error_str:
                provider = p
                break
        return handle_api_key_error(provider, operation)
    
    elif "file not found" in error_str or "no such file" in error_str:
        # Try to extract path
        import re
        path_match = re.search(r"['\"]([^'\"]+)['\"]", str(error))
        path = Path(path_match.group(1)) if path_match else Path("unknown")
        return handle_file_not_found(path, operation)
    
    elif "permission denied" in error_str:
        # Try to extract path
        import re
        path_match = re.search(r"['\"]([^'\"]+)['\"]", str(error))
        path = Path(path_match.group(1)) if path_match else Path("unknown")
        return handle_permission_error(path, operation)
    
    elif "no module named" in error_str:
        # Extract module name
        import re
        module_match = re.search(r"no module named ['\"]([^'\"]+)['\"]", error_str)
        module = module_match.group(1) if module_match else "unknown"
        return handle_dependency_error(module, operation)
    
    elif "cost limit" in error_str or "budget" in error_str:
        # Try to extract amounts
        import re
        amounts = re.findall(r"\$?([\d.]+)", str(error))
        spent = float(amounts[0]) if len(amounts) > 0 else 0.0
        limit = float(amounts[1]) if len(amounts) > 1 else 0.0
        return handle_cost_limit_error(spent, limit, operation)
    
    else:
        # Generic error
        context = ErrorContext(
            ErrorCategory.UNKNOWN,
            operation,
            {"error_type": type(error).__name__}
        )
        context.suggestions = [
            "Check the logs for more details",
            "Run with --debug flag for verbose output",
            "Report this issue if it persists"
        ]
        
        return UserFriendlyError(
            str(error),
            context,
            error
        )


def format_error_for_user(
    error: Exception,
    operation: str = "operation",
    include_traceback: bool = False
) -> str:
    """Format any error for user display."""
    if isinstance(error, UserFriendlyError):
        return error.format_error(include_traceback)
    else:
        wrapped = wrap_error(error, operation)
        return wrapped.format_error(include_traceback)