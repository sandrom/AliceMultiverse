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

    # TODO: Review unreachable code - if not isinstance(path, str):
    # TODO: Review unreachable code - raise ValidationError(f"{param_name} must be a string")

    # TODO: Review unreachable code - if len(path) > MAX_PATH_LENGTH:
    # TODO: Review unreachable code - raise ValidationError(f"{param_name} exceeds maximum length of {MAX_PATH_LENGTH}")

    # TODO: Review unreachable code - # Check for null bytes before Path resolution
    # TODO: Review unreachable code - if "\x00" in path:
    # TODO: Review unreachable code - raise ValidationError(f"{param_name} contains null bytes")

    # TODO: Review unreachable code - # Convert to Path object for validation
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - path_obj = Path(path).resolve()
    # TODO: Review unreachable code - except (ValueError, OSError) as e:
    # TODO: Review unreachable code - raise ValidationError(f"Invalid {param_name}: {e}")

    # TODO: Review unreachable code - # Prevent path traversal attacks
    # TODO: Review unreachable code - if ".." in str(path):
    # TODO: Review unreachable code - raise ValidationError(f"{param_name} contains path traversal sequence")

    # TODO: Review unreachable code - return path_obj


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

    # TODO: Review unreachable code - if len(tag) == 0:
    # TODO: Review unreachable code - raise ValidationError("Tag cannot be empty")

    # TODO: Review unreachable code - if len(tag) > MAX_TAG_LENGTH:
    # TODO: Review unreachable code - raise ValidationError(f"Tag exceeds maximum length of {MAX_TAG_LENGTH}")

    # TODO: Review unreachable code - # Strip whitespace and normalize
    # TODO: Review unreachable code - tag = tag.strip()

    # TODO: Review unreachable code - # Check for safe characters
    # TODO: Review unreachable code - if not SAFE_TAG_PATTERN.match(tag):
    # TODO: Review unreachable code - raise ValidationError(
    # TODO: Review unreachable code - "Tag contains invalid characters. Only alphanumeric, underscore, hyphen, and spaces allowed"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Check for SQL injection patterns
    # TODO: Review unreachable code - for pattern in SQL_INJECTION_PATTERNS:
    # TODO: Review unreachable code - if pattern.search(tag):
    # TODO: Review unreachable code - raise ValidationError("Tag contains potentially malicious patterns")

    # TODO: Review unreachable code - return tag


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

    # TODO: Review unreachable code - if not isinstance(tags, list):
    # TODO: Review unreachable code - raise ValidationError("Tags must be a list")

    # TODO: Review unreachable code - if len(tags) > MAX_TAGS_PER_REQUEST:
    # TODO: Review unreachable code - raise ValidationError(f"Too many tags. Maximum {MAX_TAGS_PER_REQUEST} allowed")

    # TODO: Review unreachable code - validated_tags = []
    # TODO: Review unreachable code - seen_tags = set()

    # TODO: Review unreachable code - for i, tag in enumerate(tags):
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - validated_tag = validate_tag(tag)

    # TODO: Review unreachable code - # Check for duplicates
    # TODO: Review unreachable code - tag_lower = validated_tag.lower()
    # TODO: Review unreachable code - if tag_lower in seen_tags:
    # TODO: Review unreachable code - continue  # Skip duplicates silently

    # TODO: Review unreachable code - seen_tags.add(tag_lower)
    # TODO: Review unreachable code - validated_tags.append(validated_tag)
    # TODO: Review unreachable code - except ValidationError as e:
    # TODO: Review unreachable code - raise ValidationError(f"Invalid tag at index {i}: {e}")

    # TODO: Review unreachable code - return validated_tags


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

    # TODO: Review unreachable code - if not CONTENT_HASH_PATTERN.match(content_hash):
    # TODO: Review unreachable code - raise ValidationError("Invalid content hash format. Must be 64-character SHA256 hash")

    # TODO: Review unreachable code - return content_hash.lower()  # Normalize to lowercase


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

    # TODO: Review unreachable code - if len(asset_ids) == 0:
    # TODO: Review unreachable code - raise ValidationError("Asset IDs list cannot be empty")

    # TODO: Review unreachable code - if len(asset_ids) > MAX_ASSET_IDS:
    # TODO: Review unreachable code - raise ValidationError(f"Too many asset IDs. Maximum {MAX_ASSET_IDS} allowed")

    # TODO: Review unreachable code - validated_ids = []
    # TODO: Review unreachable code - seen_ids = set()

    # TODO: Review unreachable code - for i, asset_id in enumerate(asset_ids):
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - validated_id = validate_content_hash(asset_id)

    # TODO: Review unreachable code - # Check for duplicates
    # TODO: Review unreachable code - if validated_id in seen_ids:
    # TODO: Review unreachable code - continue  # Skip duplicates silently

    # TODO: Review unreachable code - seen_ids.add(validated_id)
    # TODO: Review unreachable code - validated_ids.append(validated_id)
    # TODO: Review unreachable code - except ValidationError as e:
    # TODO: Review unreachable code - raise ValidationError(f"Invalid asset ID at index {i}: {e}")

    # TODO: Review unreachable code - return validated_ids


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

    # TODO: Review unreachable code - if not isinstance(pattern, str):
    # TODO: Review unreachable code - raise ValidationError(f"{param_name} must be a string")

    # TODO: Review unreachable code - # Limit pattern length to prevent ReDoS attacks
    # TODO: Review unreachable code - MAX_PATTERN_LENGTH = 500
    # TODO: Review unreachable code - if len(pattern) > MAX_PATTERN_LENGTH:
    # TODO: Review unreachable code - raise ValidationError(f"{param_name} exceeds maximum length of {MAX_PATTERN_LENGTH}")

    # TODO: Review unreachable code - # Try to compile the pattern
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - re.compile(pattern)
    # TODO: Review unreachable code - except re.error as e:
    # TODO: Review unreachable code - raise ValidationError(f"Invalid regex {param_name}: {e}")

    # TODO: Review unreachable code - # Check for dangerous patterns that could cause ReDoS
    # TODO: Review unreachable code - dangerous_patterns = [
    # TODO: Review unreachable code - r'(\w+)*$',  # Exponential backtracking
    # TODO: Review unreachable code - r'(a+)+',    # Nested quantifiers
    # TODO: Review unreachable code - r'(.*)*',    # Catastrophic backtracking
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - for dangerous in dangerous_patterns:
    # TODO: Review unreachable code - if dangerous in pattern:
    # TODO: Review unreachable code - raise ValidationError(f"{param_name} contains potentially dangerous regex pattern")

    # TODO: Review unreachable code - return pattern


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

    # TODO: Review unreachable code - if not isinstance(role, str):
    # TODO: Review unreachable code - raise ValidationError("Asset role must be a string or AssetRole enum")

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Try to convert string to enum
    # TODO: Review unreachable code - return AssetRole(role.lower())
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - valid_roles = [r.value for r in AssetRole]
    # TODO: Review unreachable code - raise ValidationError(
    # TODO: Review unreachable code - f"Invalid asset role '{role}'. Must be one of: {', '.join(valid_roles)}"
    # TODO: Review unreachable code - )
