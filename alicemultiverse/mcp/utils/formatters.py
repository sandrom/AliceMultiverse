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

    lines = []
    for file in files:
        file_path = Path(file)

        # Make relative if base_path provided
        if base_path:
            try:
                display_path = file_path.relative_to(base_path)
            except ValueError:
                display_path = file_path
        else:
            display_path = file_path

        line = str(display_path)

        # Add stats if requested and file exists
        if include_stats and file_path.exists():
            stat = file_path.stat()
            size = _format_size(stat.st_size)
            line += f" ({size})"

        lines.append(line)

    return "\n".join(lines)


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


def format_stats(stats: dict[str, Any], title: str | None = None) -> str:
    """Format statistics for display.
    
    Args:
        stats: Statistics dictionary
        title: Optional title
        
    Returns:
        Formatted string
    """
    lines = []

    if title:
        lines.append(title)
        lines.append("-" * len(title))

    # Format each stat
    for key, value in stats.items():
        # Convert underscore to spaces and capitalize
        display_key = key.replace("_", " ").title()

        # Format value based on type
        if isinstance(value, float):
            display_value = f"{value:.2f}"
        elif isinstance(value, dict):
            # Nested stats
            lines.append(f"\n{display_key}:")
            for sub_key, sub_value in value.items():
                sub_display_key = sub_key.replace("_", " ").title()
                lines.append(f"  {sub_display_key}: {sub_value}")
            continue
        else:
            display_value = str(value)

        lines.append(f"{display_key}: {display_value}")

    return "\n".join(lines)


def _format_size(size_bytes: int) -> str:
    """Format byte size as human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def _format_datetime(dt: str | datetime) -> str:
    """Format datetime for display.
    
    Args:
        dt: Datetime object or ISO string
        
    Returns:
        Formatted datetime
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt

    return dt.strftime("%Y-%m-%d %H:%M:%S")
