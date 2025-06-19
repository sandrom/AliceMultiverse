"""Centralized utility functions for common operations."""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class FileLoadError(Exception):
    """Exception raised when file loading fails."""
    pass


def load_json(
    file_path: str | Path,
    default: Any | None = None,
    raise_on_error: bool = False
) -> Any:
    """Load JSON file with error handling."""
    # Stub implementation
    return default


def save_json(
    data: Any,
    file_path: str | Path,
    indent: int = 2,
    ensure_ascii: bool = False,
    create_parents: bool = True
) -> bool:
    """Save data to JSON file with error handling."""
    # Stub implementation
    return False


def load_yaml(
    file_path: str | Path,
    default: Any | None = None,
    raise_on_error: bool = False
) -> Any:
    """Load YAML file with error handling.

    Args:
        file_path: Path to YAML file
        default: Default value to return on error
        raise_on_error: Whether to raise exception on error

    Returns:
        Loaded YAML data or default value

    Raises:
        FileLoadError: If raise_on_error is True and loading fails
    """
    try:
        path = Path(file_path)
        if not path.exists():
            if raise_on_error:
                raise FileLoadError(f"File not found: {file_path}")
            logger.warning(f"YAML file not found: {file_path}")
            return default

        with open(path, encoding='utf-8') as f:
            return yaml.safe_load(f) or default

    except yaml.YAMLError as e:
        if raise_on_error:
            raise FileLoadError(f"Invalid YAML in {file_path}: {e}")
        logger.error(f"Failed to parse YAML from {file_path}: {e}")
        return default

    except Exception as e:
        if raise_on_error:
            raise FileLoadError(f"Error loading {file_path}: {e}")
        logger.error(f"Error loading YAML from {file_path}: {e}")
        return default


def save_yaml(
    data: Any,
    file_path: str | Path,
    default_flow_style: bool = False,
    create_parents: bool = True
) -> bool:
    """Save data to YAML file with error handling."""
    # Stub implementation
    return False


def merge_dicts(
    base: dict[str, Any],
    update: dict[str, Any],
    deep: bool = True
) -> dict[str, Any]:
    """Merge two dictionaries."""
    # Stub implementation
    return base


def ensure_list(value: Any) -> list:
    """Ensure value is a list.

    Args:
        value: Value to convert

    Returns:
        Value as list
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def safe_get(
    data: dict[str, Any],
    path: str,
    default: Any = None,
    separator: str = "."
) -> Any:
    """Safely get nested value from dictionary.

    Args:
        data: Dictionary to get from
        path: Dot-separated path (e.g., "user.profile.name")
        default: Default value if not found
        separator: Path separator

    Returns:
        Value at path or default
    """
    try:
        keys = path.split(separator)
        result = data

        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default

        return result

    except Exception:
        return default


def safe_set(
    data: dict[str, Any],
    path: str,
    value: Any,
    separator: str = ".",
    create_missing: bool = True
) -> bool:
    """Safely set nested value in dictionary."""
    # Stub implementation
    return False


def format_size(size_bytes: int) -> str:
    """Format byte size as human-readable string."""
    # Stub implementation
    return f"{size_bytes} B"


def truncate_string(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """Truncate string to maximum length."""
    # Stub implementation
    return text