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
    """Load JSON file with error handling.

    Args:
        file_path: Path to JSON file
        default: Default value to return on error
        raise_on_error: Whether to raise exception on error

    Returns:
        Loaded JSON data or default value

    Raises:
        FileLoadError: If raise_on_error is True and loading fails
    """
    try:
        path = Path(file_path)
        if not path.exists():
            if raise_on_error:
                raise FileLoadError(f"File not found: {file_path}")
            logger.warning(f"JSON file not found: {file_path}")
            return default

        with open(path, encoding='utf-8') as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        if raise_on_error:
            raise FileLoadError(f"Invalid JSON in {file_path}: {e}")
        logger.error(f"Failed to parse JSON from {file_path}: {e}")
        return default

    except Exception as e:
        if raise_on_error:
            raise FileLoadError(f"Error loading {file_path}: {e}")
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default


def save_json(
    data: Any,
    file_path: str | Path,
    indent: int = 2,
    ensure_ascii: bool = False,
    create_parents: bool = True
) -> bool:
    """Save data to JSON file with error handling.

    Args:
        data: Data to save
        file_path: Path to save to
        indent: JSON indentation
        ensure_ascii: Whether to escape non-ASCII characters
        create_parents: Whether to create parent directories

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)

        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)

        return True

    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
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
    """Save data to YAML file with error handling.

    Args:
        data: Data to save
        file_path: Path to save to
        default_flow_style: YAML flow style
        create_parents: Whether to create parent directories

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)

        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=default_flow_style, allow_unicode=True)

        return True

    except Exception as e:
        logger.error(f"Failed to save YAML to {file_path}: {e}")
        return False


def merge_dicts(
    base: dict[str, Any],
    update: dict[str, Any],
    deep: bool = True
) -> dict[str, Any]:
    """Merge two dictionaries.

    Args:
        base: Base dictionary
        update: Dictionary to merge in
        deep: Whether to do deep merge

    Returns:
        Merged dictionary (base is modified)
    """
    if not deep:
        base.update(update)
        return base

    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            merge_dicts(base[key], value, deep=True)
        else:
            base[key] = value

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
    """Safely set nested value in dictionary.

    Args:
        data: Dictionary to set in
        path: Dot-separated path (e.g., "user.profile.name")
        value: Value to set
        separator: Path separator
        create_missing: Whether to create missing intermediate dicts

    Returns:
        True if successful
    """
    try:
        keys = path.split(separator)
        current = data

        for key in keys[:-1]:
            if key not in current:
                if create_missing:
                    current[key] = {}
                else:
                    return False

            if not isinstance(current[key], dict):
                return False

            current = current[key]

        current[keys[-1]] = value
        return True

    except Exception:
        return False


def format_size(size_bytes: int) -> str:
    """Format byte size as human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def truncate_string(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return text[:max_length]

    return text[:max_length - len(suffix)] + suffix
