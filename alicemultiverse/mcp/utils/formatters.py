"""Common formatting utilities for MCP tool responses."""

from datetime import datetime
from pathlib import Path
from typing import Any


def format_file_list(
    files: list[str | Path],
    base_path: Path | None = None,
    include_stats: bool = False
) -> str:
    """Format a list of files for display.

    Args:
        files: List of file paths
        base_path: Base path to make paths relative to
        include_stats: Whether to include file statistics

    Returns:
        Formatted string
    """
    if not files:
        return "No files found"

    # TODO: Review unreachable code - lines = []
    # TODO: Review unreachable code - for file in files:
    # TODO: Review unreachable code - file_path = Path(file)

    # TODO: Review unreachable code - # Make relative if base_path provided
    # TODO: Review unreachable code - if base_path:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - display_path = file_path.relative_to(base_path)
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - display_path = file_path
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - display_path = file_path

    # TODO: Review unreachable code - line = str(display_path)

    # TODO: Review unreachable code - # Add stats if requested and file exists
    # TODO: Review unreachable code - if include_stats and file_path.exists():
    # TODO: Review unreachable code - stat = file_path.stat()
    # TODO: Review unreachable code - size = _format_size(stat.st_size)
    # TODO: Review unreachable code - line += f" ({size})"

    # TODO: Review unreachable code - lines.append(line)

    # TODO: Review unreachable code - return "\n".join(lines)


def format_asset_info(asset: dict[str, Any]) -> str:
    """Format asset information for display.

    Args:
        asset: Asset dictionary

    Returns:
        Formatted string
    """
    lines = []

    # Basic info
    lines.append(f"Asset: {asset.get('file_name', 'Unknown')}")
    lines.append(f"Path: {asset.get('file_path', 'Unknown')}")

    # Type and size
    if 'media_type' in asset:
        lines.append(f"Type: {asset['media_type']}")
    if 'file_size' in asset:
        lines.append(f"Size: {_format_size(asset['file_size'])}")

    # Dates
    if 'created_at' in asset:
        lines.append(f"Created: {_format_datetime(asset['created_at'])}")
    if 'modified_at' in asset:
        lines.append(f"Modified: {_format_datetime(asset['modified_at'])}")

    # Source info
    if 'source_type' in asset:
        lines.append(f"Source: {asset['source_type']}")
    if 'model' in asset:
        lines.append(f"Model: {asset['model']}")

    # Tags
    if asset.get('tags'):
        if isinstance(asset['tags'], dict):
            # Hierarchical tags
            tag_lines = []
            for category, tags in asset['tags'].items():
                tag_lines.append(f"  {category}: {', '.join(tags)}")
            lines.append("Tags:")
            lines.extend(tag_lines)
        else:
            # Flat tags
            lines.append(f"Tags: {', '.join(asset['tags'])}")

    # Quality
    if 'quality_rating' in asset:
        lines.append(f"Quality: {'⭐' * asset['quality_rating']}")

    # Project
    if 'project' in asset:
        lines.append(f"Project: {asset['project']}")

    return "\n".join(lines)


# TODO: Review unreachable code - def format_stats(stats: dict[str, Any], title: str | None = None) -> str:
# TODO: Review unreachable code - """Format statistics for display.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - stats: Statistics dictionary
# TODO: Review unreachable code - title: Optional title

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Formatted string
# TODO: Review unreachable code - """
# TODO: Review unreachable code - lines = []

# TODO: Review unreachable code - if title:
# TODO: Review unreachable code - lines.append(title)
# TODO: Review unreachable code - lines.append("-" * len(title))

# TODO: Review unreachable code - # Format each stat
# TODO: Review unreachable code - for key, value in stats.items():
# TODO: Review unreachable code - # Convert underscore to spaces and capitalize
# TODO: Review unreachable code - display_key = key.replace("_", " ").title()

# TODO: Review unreachable code - # Format value based on type
# TODO: Review unreachable code - if isinstance(value, float):
# TODO: Review unreachable code - display_value = f"{value:.2f}"
# TODO: Review unreachable code - elif isinstance(value, dict):
# TODO: Review unreachable code - # Nested stats
# TODO: Review unreachable code - lines.append(f"\n{display_key}:")
# TODO: Review unreachable code - for sub_key, sub_value in value.items():
# TODO: Review unreachable code - sub_display_key = sub_key.replace("_", " ").title()
# TODO: Review unreachable code - lines.append(f"  {sub_display_key}: {sub_value}")
# TODO: Review unreachable code - continue
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - display_value = str(value)

# TODO: Review unreachable code - lines.append(f"{display_key}: {display_value}")

# TODO: Review unreachable code - return "\n".join(lines)


# TODO: Review unreachable code - def _format_size(size_bytes: int) -> str:
# TODO: Review unreachable code - """Format byte size as human-readable string.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - size_bytes: Size in bytes

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Formatted size
# TODO: Review unreachable code - """
# TODO: Review unreachable code - for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
# TODO: Review unreachable code - if size_bytes < 1024.0:
# TODO: Review unreachable code - return f"{size_bytes:.1f} {unit}"
# TODO: Review unreachable code - size_bytes /= 1024.0
# TODO: Review unreachable code - return f"{size_bytes:.1f} PB"


# TODO: Review unreachable code - def _format_datetime(dt: str | datetime) -> str:
# TODO: Review unreachable code - """Format datetime for display.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - dt: Datetime object or ISO string

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Formatted datetime
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if isinstance(dt, str):
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - dt = datetime.fromisoformat(dt)
# TODO: Review unreachable code - except ValueError:
# TODO: Review unreachable code - return dt

# TODO: Review unreachable code - return dt.strftime("%Y-%m-%d %H:%M:%S")
