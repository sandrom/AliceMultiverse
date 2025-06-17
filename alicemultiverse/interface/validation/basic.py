"""Basic validation functions for common data types."""

import re
from pathlib import Path

from ...core.exceptions import ValidationError
from ..structured_models import AssetRole
from .constants import (
    CONTENT_HASH_PATTERN,
    MAX_ASSET_IDS,
    MAX_PATH_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TAGS_PER_REQUEST,
    SAFE_TAG_PATTERN,
    SQL_INJECTION_PATTERNS,
)


def validate_path(path: str | None, param_name: str = "path") -> Path | None:
    """Validate and sanitize file system paths.
    
    Args:
        path: Path string to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated Path object or None
        
    Raises:
        ValidationError: If path is invalid or potentially malicious
    """
    if path is None:
        return None

    if not isinstance(path, str):
        raise ValidationError(f"{param_name} must be a string")

    if len(path) > MAX_PATH_LENGTH:
        raise ValidationError(f"{param_name} exceeds maximum length of {MAX_PATH_LENGTH}")

    # Check for null bytes before Path resolution
    if "\x00" in path:
        raise ValidationError(f"{param_name} contains null bytes")

    # Convert to Path object for validation
    try:
        path_obj = Path(path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(f"Invalid {param_name}: {e}")

    # Prevent path traversal attacks
    if ".." in str(path):
        raise ValidationError(f"{param_name} contains path traversal sequence")

    return path_obj


def validate_tag(tag: str) -> str:
    """Validate a single tag.
    
    Args:
        tag: Tag string to validate
        
    Returns:
        Validated tag
        
    Raises:
        ValidationError: If tag is invalid
    """
    if not isinstance(tag, str):
        raise ValidationError("Tag must be a string")

    if len(tag) == 0:
        raise ValidationError("Tag cannot be empty")

    if len(tag) > MAX_TAG_LENGTH:
        raise ValidationError(f"Tag exceeds maximum length of {MAX_TAG_LENGTH}")

    # Strip whitespace and normalize
    tag = tag.strip()

    # Check for safe characters
    if not SAFE_TAG_PATTERN.match(tag):
        raise ValidationError(
            "Tag contains invalid characters. Only alphanumeric, underscore, hyphen, and spaces allowed"
        )

    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(tag):
            raise ValidationError("Tag contains potentially malicious patterns")

    return tag


def validate_tags(tags: list[str] | None) -> list[str] | None:
    """Validate a list of tags.
    
    Args:
        tags: List of tag strings
        
    Returns:
        Validated list of tags or None
        
    Raises:
        ValidationError: If any tag is invalid
    """
    if tags is None:
        return None

    if not isinstance(tags, list):
        raise ValidationError("Tags must be a list")

    if len(tags) > MAX_TAGS_PER_REQUEST:
        raise ValidationError(f"Too many tags. Maximum {MAX_TAGS_PER_REQUEST} allowed")

    validated_tags = []
    seen_tags = set()

    for i, tag in enumerate(tags):
        try:
            validated_tag = validate_tag(tag)

            # Check for duplicates
            tag_lower = validated_tag.lower()
            if tag_lower in seen_tags:
                continue  # Skip duplicates silently

            seen_tags.add(tag_lower)
            validated_tags.append(validated_tag)
        except ValidationError as e:
            raise ValidationError(f"Invalid tag at index {i}: {e}")

    return validated_tags


def validate_content_hash(content_hash: str) -> str:
    """Validate a content hash (SHA256).
    
    Args:
        content_hash: Hash string to validate
        
    Returns:
        Validated hash (lowercase)
        
    Raises:
        ValidationError: If hash is invalid
    """
    if not isinstance(content_hash, str):
        raise ValidationError("Content hash must be a string")

    if not CONTENT_HASH_PATTERN.match(content_hash):
        raise ValidationError("Invalid content hash format. Must be 64-character SHA256 hash")

    return content_hash.lower()  # Normalize to lowercase


def validate_asset_ids(asset_ids: list[str]) -> list[str]:
    """Validate a list of asset IDs (content hashes).
    
    Args:
        asset_ids: List of asset ID strings
        
    Returns:
        Validated list of asset IDs
        
    Raises:
        ValidationError: If any ID is invalid
    """
    if not isinstance(asset_ids, list):
        raise ValidationError("Asset IDs must be a list")

    if len(asset_ids) == 0:
        raise ValidationError("Asset IDs list cannot be empty")

    if len(asset_ids) > MAX_ASSET_IDS:
        raise ValidationError(f"Too many asset IDs. Maximum {MAX_ASSET_IDS} allowed")

    validated_ids = []
    seen_ids = set()

    for i, asset_id in enumerate(asset_ids):
        try:
            validated_id = validate_content_hash(asset_id)

            # Check for duplicates
            if validated_id in seen_ids:
                continue  # Skip duplicates silently

            seen_ids.add(validated_id)
            validated_ids.append(validated_id)
        except ValidationError as e:
            raise ValidationError(f"Invalid asset ID at index {i}: {e}")

    return validated_ids


def validate_regex_pattern(pattern: str | None, param_name: str = "pattern") -> str | None:
    """Validate a regex pattern for safety.
    
    Args:
        pattern: Regex pattern string
        param_name: Parameter name for error messages
        
    Returns:
        Validated pattern or None
        
    Raises:
        ValidationError: If pattern is invalid or potentially malicious
    """
    if pattern is None:
        return None

    if not isinstance(pattern, str):
        raise ValidationError(f"{param_name} must be a string")

    # Limit pattern length to prevent ReDoS attacks
    MAX_PATTERN_LENGTH = 500
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise ValidationError(f"{param_name} exceeds maximum length of {MAX_PATTERN_LENGTH}")

    # Try to compile the pattern
    try:
        re.compile(pattern)
    except re.error as e:
        raise ValidationError(f"Invalid regex {param_name}: {e}")

    # Check for dangerous patterns that could cause ReDoS
    dangerous_patterns = [
        r'(\w+)*$',  # Exponential backtracking
        r'(a+)+',    # Nested quantifiers
        r'(.*)*',    # Catastrophic backtracking
    ]

    for dangerous in dangerous_patterns:
        if dangerous in pattern:
            raise ValidationError(f"{param_name} contains potentially dangerous regex pattern")

    return pattern


def validate_asset_role(role: str | AssetRole) -> AssetRole:
    """Validate asset role.
    
    Args:
        role: Role string or enum
        
    Returns:
        Validated AssetRole enum
        
    Raises:
        ValidationError: If role is invalid
    """
    if isinstance(role, AssetRole):
        return role

    if not isinstance(role, str):
        raise ValidationError("Asset role must be a string or AssetRole enum")

    try:
        # Try to convert string to enum
        return AssetRole(role.lower())
    except ValueError:
        valid_roles = [r.value for r in AssetRole]
        raise ValidationError(
            f"Invalid asset role '{role}'. Must be one of: {', '.join(valid_roles)}"
        )
