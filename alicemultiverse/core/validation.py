"""Input validation utilities for security and data integrity."""

import re
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, TypeVar, Union
from urllib.parse import urlparse

from .exceptions import ValidationError

# Type variables
F = TypeVar('F', bound=Callable[..., Any])

# Security constants
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.gif', '.bmp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.mpg', '.mpeg'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
ALLOWED_URL_SCHEMES = {'http', 'https', 'file'}
MAX_PATH_LENGTH = 4096
MAX_FILENAME_LENGTH = 255

# Dangerous path patterns
DANGEROUS_PATH_PATTERNS = [
    r'\.\./',  # Parent directory traversal
    r'^/',     # Absolute paths when relative expected
    r'^~',     # Home directory expansion
    r'\0',     # Null bytes
    r'[\<\>"|?*]',  # Windows forbidden characters
]


def validate_path(
    must_exist: bool = False,
    allow_symlinks: bool = True,
    allowed_extensions: Optional[Set[str]] = None,
    base_path: Optional[Path] = None
) -> Callable[[F], F]:
    """Decorator to validate file paths.
    
    Args:
        must_exist: Whether the path must exist
        allow_symlinks: Whether to allow symbolic links
        allowed_extensions: Set of allowed file extensions
        base_path: Base path for relative path resolution
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find path arguments (assume first Path/str arg is the path)
            path_arg = None
            path_idx = None
            
            for i, arg in enumerate(args):
                if isinstance(arg, (str, Path)):
                    path_arg = arg
                    path_idx = i
                    break
            
            # Check kwargs if not found in args
            if path_arg is None:
                for key in ['path', 'file_path', 'filepath']:
                    if key in kwargs and isinstance(kwargs[key], (str, Path)):
                        path_arg = kwargs[key]
                        break
            
            if path_arg is None:
                raise ValidationError("No path argument found to validate")
            
            # Validate the path
            validated_path = validate_file_path(
                path_arg,
                must_exist=must_exist,
                allow_symlinks=allow_symlinks,
                allowed_extensions=allowed_extensions,
                base_path=base_path
            )
            
            # Replace with validated path
            if path_idx is not None:
                args = list(args)
                args[path_idx] = validated_path
                args = tuple(args)
            else:
                # Update kwargs
                for key in ['path', 'file_path', 'filepath']:
                    if key in kwargs:
                        kwargs[key] = validated_path
                        break
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_url(
    allowed_schemes: Optional[Set[str]] = None,
    allowed_domains: Optional[Set[str]] = None,
    require_https: bool = False
) -> Callable[[F], F]:
    """Decorator to validate URLs.
    
    Args:
        allowed_schemes: Set of allowed URL schemes
        allowed_domains: Set of allowed domains
        require_https: Whether to require HTTPS
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find URL arguments
            url_arg = None
            url_idx = None
            
            for i, arg in enumerate(args):
                if isinstance(arg, str) and ('://' in arg or arg.startswith('/')):
                    url_arg = arg
                    url_idx = i
                    break
            
            # Check kwargs
            if url_arg is None:
                for key in ['url', 'uri', 'endpoint']:
                    if key in kwargs and isinstance(kwargs[key], str):
                        url_arg = kwargs[key]
                        break
            
            if url_arg:
                # Validate the URL
                validated_url = validate_url_string(
                    url_arg,
                    allowed_schemes=allowed_schemes,
                    allowed_domains=allowed_domains,
                    require_https=require_https
                )
                
                # Replace with validated URL
                if url_idx is not None:
                    args = list(args)
                    args[url_idx] = validated_url
                    args = tuple(args)
                else:
                    for key in ['url', 'uri', 'endpoint']:
                        if key in kwargs:
                            kwargs[key] = validated_url
                            break
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_file_path(
    path: Union[str, Path],
    must_exist: bool = False,
    allow_symlinks: bool = True,
    allowed_extensions: Optional[Set[str]] = None,
    base_path: Optional[Path] = None
) -> Path:
    """Validate a file path for security and correctness.
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        allow_symlinks: Whether to allow symbolic links
        allowed_extensions: Set of allowed file extensions
        base_path: Base path for relative path resolution
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If validation fails
    """
    # Convert to string for pattern checking
    path_str = str(path)
    
    # Check length
    if len(path_str) > MAX_PATH_LENGTH:
        raise ValidationError(f"Path too long: {len(path_str)} > {MAX_PATH_LENGTH}")
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATH_PATTERNS:
        if re.search(pattern, path_str):
            raise ValidationError(f"Dangerous path pattern detected: {pattern}")
    
    # Convert to Path object
    try:
        path_obj = Path(path_str)
    except Exception as e:
        raise ValidationError(f"Invalid path: {e}")
    
    # Check filename length
    if path_obj.name and len(path_obj.name) > MAX_FILENAME_LENGTH:
        raise ValidationError(f"Filename too long: {len(path_obj.name)} > {MAX_FILENAME_LENGTH}")
    
    # Resolve path (handles .. and symlinks)
    try:
        if base_path:
            # Resolve relative to base path
            full_path = (Path(base_path) / path_obj).resolve()
            # Ensure it's within base path
            if not str(full_path).startswith(str(Path(base_path).resolve())):
                raise ValidationError("Path escapes base directory")
        else:
            full_path = path_obj.resolve()
    except Exception as e:
        raise ValidationError(f"Cannot resolve path: {e}")
    
    # Check symlinks
    if not allow_symlinks and full_path.is_symlink():
        raise ValidationError("Symbolic links not allowed")
    
    # Check existence
    if must_exist and not full_path.exists():
        raise ValidationError(f"Path does not exist: {full_path}")
    
    # Check extension
    if allowed_extensions and full_path.suffix.lower() not in allowed_extensions:
        raise ValidationError(
            f"File extension '{full_path.suffix}' not allowed. "
            f"Allowed: {', '.join(sorted(allowed_extensions))}"
        )
    
    return full_path


def validate_url_string(
    url: str,
    allowed_schemes: Optional[Set[str]] = None,
    allowed_domains: Optional[Set[str]] = None,
    require_https: bool = False
) -> str:
    """Validate a URL string.
    
    Args:
        url: URL to validate
        allowed_schemes: Set of allowed URL schemes
        allowed_domains: Set of allowed domains
        require_https: Whether to require HTTPS
        
    Returns:
        Validated URL string
        
    Raises:
        ValidationError: If validation fails
    """
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL: {e}")
    
    # Check scheme
    if allowed_schemes is None:
        allowed_schemes = ALLOWED_URL_SCHEMES
    
    if parsed.scheme not in allowed_schemes:
        raise ValidationError(
            f"URL scheme '{parsed.scheme}' not allowed. "
            f"Allowed: {', '.join(sorted(allowed_schemes))}"
        )
    
    # Check HTTPS requirement
    if require_https and parsed.scheme != 'https':
        raise ValidationError("HTTPS required")
    
    # Check domain
    if allowed_domains and parsed.netloc:
        domain = parsed.netloc.lower()
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        if domain not in allowed_domains:
            raise ValidationError(
                f"Domain '{domain}' not allowed. "
                f"Allowed: {', '.join(sorted(allowed_domains))}"
            )
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'file://',
        r'\.\./\.\.',  # Multiple traversals
        r'@',  # Username in URL
    ]
    
    url_lower = url.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, url_lower):
            raise ValidationError(f"Suspicious URL pattern detected")
    
    return url


def sanitize_filename(filename: str, default: str = "file") -> str:
    """Sanitize a filename for safe file system usage.
    
    Args:
        filename: Original filename
        default: Default name if sanitization fails
        
    Returns:
        Safe filename
    """
    if not filename:
        return default
    
    # Remove path components
    filename = Path(filename).name
    
    # Replace dangerous characters
    safe_chars = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    # Remove multiple dots (prevent extension confusion)
    safe_chars = re.sub(r'\.+', '.', safe_chars)
    
    # Remove leading/trailing dots and spaces
    safe_chars = safe_chars.strip('. ')
    
    # Limit length
    if len(safe_chars) > MAX_FILENAME_LENGTH:
        # Preserve extension if possible
        name, ext = Path(safe_chars).stem, Path(safe_chars).suffix
        max_name_length = MAX_FILENAME_LENGTH - len(ext)
        safe_chars = name[:max_name_length] + ext
    
    # Return default if result is empty
    return safe_chars or default


def validate_json_input(
    schema: Optional[dict] = None,
    required_fields: Optional[List[str]] = None,
    max_size: int = 10 * 1024 * 1024  # 10MB default
) -> Callable[[F], F]:
    """Decorator to validate JSON input.
    
    Args:
        schema: JSON schema for validation
        required_fields: List of required fields
        max_size: Maximum allowed size in bytes
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find JSON data in arguments
            json_data = None
            json_idx = None
            
            for i, arg in enumerate(args):
                if isinstance(arg, dict):
                    json_data = arg
                    json_idx = i
                    break
            
            # Check kwargs
            if json_data is None:
                for key in ['data', 'json', 'payload']:
                    if key in kwargs and isinstance(kwargs[key], dict):
                        json_data = kwargs[key]
                        break
            
            if json_data:
                # Check size (rough estimate)
                import json
                json_str = json.dumps(json_data)
                if len(json_str) > max_size:
                    raise ValidationError(
                        f"JSON data too large: {len(json_str)} > {max_size} bytes"
                    )
                
                # Check required fields
                if required_fields:
                    missing = [f for f in required_fields if f not in json_data]
                    if missing:
                        raise ValidationError(
                            f"Missing required fields: {', '.join(missing)}"
                        )
                
                # TODO: Add JSON schema validation if schema provided
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def sanitize_error_message(error: Exception, show_type: bool = True) -> str:
    """Sanitize error message to remove sensitive information.
    
    Args:
        error: Exception to sanitize
        show_type: Whether to include error type
        
    Returns:
        Safe error message
    """
    # Patterns that might contain sensitive data
    sensitive_patterns = [
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w\-]+', 'API_KEY=***'),
        (r'token["\']?\s*[:=]\s*["\']?[\w\-]+', 'token=***'),
        (r'password["\']?\s*[:=]\s*["\']?[\w\-]+', 'password=***'),
        (r'secret["\']?\s*[:=]\s*["\']?[\w\-]+', 'secret=***'),
        (r'/api/v\d+/[\w\-]+', '/api/v1/***'),  # API endpoints
        (r'[a-f0-9]{32,}', '***'),  # Long hex strings (hashes, tokens)
        (r'Bearer\s+[\w\-\.]+', 'Bearer ***'),  # Auth headers
    ]
    
    error_msg = str(error)
    
    # Apply sanitization patterns
    for pattern, replacement in sensitive_patterns:
        error_msg = re.sub(pattern, replacement, error_msg, flags=re.IGNORECASE)
    
    # Truncate very long messages
    if len(error_msg) > 500:
        error_msg = error_msg[:500] + '... (truncated)'
    
    if show_type:
        return f"{type(error).__name__}: {error_msg}"
    
    return error_msg