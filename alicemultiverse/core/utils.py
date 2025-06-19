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
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - path = Path(file_path)
# TODO: Review unreachable code - if not path.exists():
# TODO: Review unreachable code - if raise_on_error:
# TODO: Review unreachable code - raise FileLoadError(f"File not found: {file_path}")
# TODO: Review unreachable code - logger.warning(f"JSON file not found: {file_path}")
# TODO: Review unreachable code - return default

# TODO: Review unreachable code - with open(path, encoding='utf-8') as f:
# TODO: Review unreachable code - return json.load(f)

# TODO: Review unreachable code - except json.JSONDecodeError as e:
# TODO: Review unreachable code - if raise_on_error:
# TODO: Review unreachable code - raise FileLoadError(f"Invalid JSON in {file_path}: {e}")
# TODO: Review unreachable code - logger.error(f"Failed to parse JSON from {file_path}: {e}")
# TODO: Review unreachable code - return default

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - if raise_on_error:
# TODO: Review unreachable code - raise FileLoadError(f"Error loading {file_path}: {e}")
# TODO: Review unreachable code - logger.error(f"Error loading JSON from {file_path}: {e}")
# TODO: Review unreachable code - return default


# TODO: Review unreachable code - def save_json(
# TODO: Review unreachable code - data: Any,
# TODO: Review unreachable code - file_path: str | Path,
# TODO: Review unreachable code - indent: int = 2,
# TODO: Review unreachable code - ensure_ascii: bool = False,
# TODO: Review unreachable code - create_parents: bool = True
# TODO: Review unreachable code - ) -> bool:
# TODO: Review unreachable code - """Save data to JSON file with error handling.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - data: Data to save
# TODO: Review unreachable code - file_path: Path to save to
# TODO: Review unreachable code - indent: JSON indentation
# TODO: Review unreachable code - ensure_ascii: Whether to escape non-ASCII characters
# TODO: Review unreachable code - create_parents: Whether to create parent directories

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - True if successful, False otherwise
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - path = Path(file_path)

# TODO: Review unreachable code - if create_parents:
# TODO: Review unreachable code - path.parent.mkdir(parents=True, exist_ok=True)

# TODO: Review unreachable code - with open(path, 'w', encoding='utf-8') as f:
# TODO: Review unreachable code - json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)

# TODO: Review unreachable code - return True

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Failed to save JSON to {file_path}: {e}")
# TODO: Review unreachable code - return False


# TODO: Review unreachable code - def load_yaml(
# TODO: Review unreachable code - file_path: str | Path,
# TODO: Review unreachable code - default: Any | None = None,
# TODO: Review unreachable code - raise_on_error: bool = False
# TODO: Review unreachable code - ) -> Any:
# TODO: Review unreachable code - """Load YAML file with error handling.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - file_path: Path to YAML file
# TODO: Review unreachable code - default: Default value to return on error
# TODO: Review unreachable code - raise_on_error: Whether to raise exception on error

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Loaded YAML data or default value

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - FileLoadError: If raise_on_error is True and loading fails
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - path = Path(file_path)
# TODO: Review unreachable code - if not path.exists():
# TODO: Review unreachable code - if raise_on_error:
# TODO: Review unreachable code - raise FileLoadError(f"File not found: {file_path}")
# TODO: Review unreachable code - logger.warning(f"YAML file not found: {file_path}")
# TODO: Review unreachable code - return default

# TODO: Review unreachable code - with open(path, encoding='utf-8') as f:
# TODO: Review unreachable code - return yaml.safe_load(f) or default

# TODO: Review unreachable code - except yaml.YAMLError as e:
# TODO: Review unreachable code - if raise_on_error:
# TODO: Review unreachable code - raise FileLoadError(f"Invalid YAML in {file_path}: {e}")
# TODO: Review unreachable code - logger.error(f"Failed to parse YAML from {file_path}: {e}")
# TODO: Review unreachable code - return default

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - if raise_on_error:
# TODO: Review unreachable code - raise FileLoadError(f"Error loading {file_path}: {e}")
# TODO: Review unreachable code - logger.error(f"Error loading YAML from {file_path}: {e}")
# TODO: Review unreachable code - return default


# TODO: Review unreachable code - def save_yaml(
# TODO: Review unreachable code - data: Any,
# TODO: Review unreachable code - file_path: str | Path,
# TODO: Review unreachable code - default_flow_style: bool = False,
# TODO: Review unreachable code - create_parents: bool = True
# TODO: Review unreachable code - ) -> bool:
# TODO: Review unreachable code - """Save data to YAML file with error handling.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - data: Data to save
# TODO: Review unreachable code - file_path: Path to save to
# TODO: Review unreachable code - default_flow_style: YAML flow style
# TODO: Review unreachable code - create_parents: Whether to create parent directories

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - True if successful, False otherwise
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - path = Path(file_path)

# TODO: Review unreachable code - if create_parents:
# TODO: Review unreachable code - path.parent.mkdir(parents=True, exist_ok=True)

# TODO: Review unreachable code - with open(path, 'w', encoding='utf-8') as f:
# TODO: Review unreachable code - yaml.safe_dump(data, f, default_flow_style=default_flow_style, allow_unicode=True)

# TODO: Review unreachable code - return True

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Failed to save YAML to {file_path}: {e}")
# TODO: Review unreachable code - return False


# TODO: Review unreachable code - def merge_dicts(
# TODO: Review unreachable code - base: dict[str, Any],
# TODO: Review unreachable code - update: dict[str, Any],
# TODO: Review unreachable code - deep: bool = True
# TODO: Review unreachable code - ) -> dict[str, Any]:
# TODO: Review unreachable code - """Merge two dictionaries.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - base: Base dictionary
# TODO: Review unreachable code - update: Dictionary to merge in
# TODO: Review unreachable code - deep: Whether to do deep merge

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Merged dictionary (base is modified)
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if not deep:
# TODO: Review unreachable code - base.update(update)
# TODO: Review unreachable code - return base

# TODO: Review unreachable code - for key, value in update.items():
# TODO: Review unreachable code - if key in base and isinstance(base[key], dict) and isinstance(value, dict):
# TODO: Review unreachable code - merge_dicts(base[key], value, deep=True)
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - base[key] = value

# TODO: Review unreachable code - return base


# TODO: Review unreachable code - def ensure_list(value: Any) -> list:
# TODO: Review unreachable code - """Ensure value is a list.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - value: Value to convert

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Value as list
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if value is None:
# TODO: Review unreachable code - return []
# TODO: Review unreachable code - if isinstance(value, list):
# TODO: Review unreachable code - return value
# TODO: Review unreachable code - if isinstance(value, (tuple, set)):
# TODO: Review unreachable code - return list(value)
# TODO: Review unreachable code - return [value]


# TODO: Review unreachable code - def safe_get(
# TODO: Review unreachable code - data: dict[str, Any],
# TODO: Review unreachable code - path: str,
# TODO: Review unreachable code - default: Any = None,
# TODO: Review unreachable code - separator: str = "."
# TODO: Review unreachable code - ) -> Any:
# TODO: Review unreachable code - """Safely get nested value from dictionary.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - data: Dictionary to get from
# TODO: Review unreachable code - path: Dot-separated path (e.g., "user.profile.name")
# TODO: Review unreachable code - default: Default value if not found
# TODO: Review unreachable code - separator: Path separator

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Value at path or default
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - keys = path.split(separator)
# TODO: Review unreachable code - result = data

# TODO: Review unreachable code - for key in keys:
# TODO: Review unreachable code - if isinstance(result, dict) and key in result:
# TODO: Review unreachable code - result = result[key]
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - return default

# TODO: Review unreachable code - return result

# TODO: Review unreachable code - except Exception:
# TODO: Review unreachable code - return default


# TODO: Review unreachable code - def safe_set(
# TODO: Review unreachable code - data: dict[str, Any],
# TODO: Review unreachable code - path: str,
# TODO: Review unreachable code - value: Any,
# TODO: Review unreachable code - separator: str = ".",
# TODO: Review unreachable code - create_missing: bool = True
# TODO: Review unreachable code - ) -> bool:
# TODO: Review unreachable code - """Safely set nested value in dictionary.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - data: Dictionary to set in
# TODO: Review unreachable code - path: Dot-separated path (e.g., "user.profile.name")
# TODO: Review unreachable code - value: Value to set
# TODO: Review unreachable code - separator: Path separator
# TODO: Review unreachable code - create_missing: Whether to create missing intermediate dicts

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - True if successful
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - keys = path.split(separator)
# TODO: Review unreachable code - current = data

# TODO: Review unreachable code - for key in keys[:-1]:
# TODO: Review unreachable code - if key not in current:
# TODO: Review unreachable code - if create_missing:
# TODO: Review unreachable code - current[key] = {}
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - return False

# TODO: Review unreachable code - if not isinstance(current[key], dict):
# TODO: Review unreachable code - return False

# TODO: Review unreachable code - current = current[key]

# TODO: Review unreachable code - current[keys[-1]] = value
# TODO: Review unreachable code - return True

# TODO: Review unreachable code - except Exception:
# TODO: Review unreachable code - return False


# TODO: Review unreachable code - def format_size(size_bytes: int) -> str:
# TODO: Review unreachable code - """Format byte size as human-readable string.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - size_bytes: Size in bytes

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Formatted size string
# TODO: Review unreachable code - """
# TODO: Review unreachable code - for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
# TODO: Review unreachable code - if size_bytes < 1024.0:
# TODO: Review unreachable code - return f"{size_bytes:.2f} {unit}"
# TODO: Review unreachable code - size_bytes /= 1024.0
# TODO: Review unreachable code - return f"{size_bytes:.2f} PB"


# TODO: Review unreachable code - def truncate_string(
# TODO: Review unreachable code - text: str,
# TODO: Review unreachable code - max_length: int = 100,
# TODO: Review unreachable code - suffix: str = "..."
# TODO: Review unreachable code - ) -> str:
# TODO: Review unreachable code - """Truncate string to maximum length.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - text: Text to truncate
# TODO: Review unreachable code - max_length: Maximum length
# TODO: Review unreachable code - suffix: Suffix to add if truncated

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Truncated string
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if len(text) <= max_length:
# TODO: Review unreachable code - return text

# TODO: Review unreachable code - if len(suffix) >= max_length:
# TODO: Review unreachable code - return text[:max_length]

# TODO: Review unreachable code - return text[:max_length - len(suffix)] + suffix
