"""
Media Organization Helper Functions

Utility functions for project extraction and AI source detection patterns.
Used throughout the organizer modules for consistent file organization
and source identification.
"""

import re
from pathlib import Path
from typing import Any

# Quality assessment functions have been removed.
# Use image understanding for content analysis instead.


def get_quality_folder_name(stars: int) -> str:
    """Get folder name for quality star rating.

    Args:
        stars: Star rating (1-5)

    Returns:
        Folder name like "5-star"
    """
    return f"{stars}-star"


def extract_project_folder(media_path: Path, source_dir: Path) -> str:
    """Extract project folder name from file path.
    
    Args:
        media_path: Path to media file
        source_dir: Source directory (inbox)
        
    Returns:
        Project folder name or "uncategorized"
    """
    from ..core.constants import UNCATEGORIZED_PROJECT
    
    try:
        relative_path = media_path.relative_to(source_dir)
        path_parts = relative_path.parts
        
        if len(path_parts) > 1:
            # File is in a project folder (or deeper)
            return path_parts[0]
        else:
            # File is directly in inbox
            return UNCATEGORIZED_PROJECT
    except ValueError:
        # Path is not relative to source_dir
        return UNCATEGORIZED_PROJECT


# TODO: Review unreachable code - def extract_project_folder(media_path: Path, source_dir: Path) -> str:
# TODO: Review unreachable code - """Extract project folder name from file path.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - media_path: Path to media file
# TODO: Review unreachable code - source_dir: Source directory (inbox)

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Project folder name or "uncategorized"
# TODO: Review unreachable code - """
# TODO: Review unreachable code - from ..core.constants import UNCATEGORIZED_PROJECT

# TODO: Review unreachable code - try:
# TODO: Review unreachable code - relative_path = media_path.relative_to(source_dir)
# TODO: Review unreachable code - path_parts = relative_path.parts

# TODO: Review unreachable code - if len(path_parts) > 1:
# TODO: Review unreachable code - # File is in a project folder (or deeper)
# TODO: Review unreachable code - return path_parts[0]
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - # File is directly in inbox
# TODO: Review unreachable code - return UNCATEGORIZED_PROJECT
# TODO: Review unreachable code - except ValueError:
# TODO: Review unreachable code - # Path is not relative to source_dir
# TODO: Review unreachable code - return UNCATEGORIZED_PROJECT


# TODO: Review unreachable code - def create_organize_result(
# TODO: Review unreachable code - media_path: Path,
# TODO: Review unreachable code - dest_path: Path,
# TODO: Review unreachable code - analysis: dict[str, Any],
# TODO: Review unreachable code - status: str,
# TODO: Review unreachable code - project_folder: str,
# TODO: Review unreachable code - error: str | None = None,
# TODO: Review unreachable code - ) -> dict[str, Any]:
# TODO: Review unreachable code - """Create a standardized organize result dictionary.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - media_path: Source media file path
# TODO: Review unreachable code - dest_path: Destination file path
# TODO: Review unreachable code - analysis: Analysis results dictionary
# TODO: Review unreachable code - status: Operation status
# TODO: Review unreachable code - project_folder: Project folder name
# TODO: Review unreachable code - error: Optional error message

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - OrganizeResult-compatible dictionary
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return {
# TODO: Review unreachable code - "source": str(media_path),
# TODO: Review unreachable code - "project_folder": project_folder,
# TODO: Review unreachable code - "status": status,
# TODO: Review unreachable code - "destination": str(dest_path),
# TODO: Review unreachable code - "date": analysis.get("date_taken"),
# TODO: Review unreachable code - "source_type": analysis.get("source_type"),
# TODO: Review unreachable code - "media_type": analysis.get("media_type"),
# TODO: Review unreachable code - "file_number": analysis.get("file_number"),
# TODO: Review unreachable code - "pipeline_result": analysis.get("pipeline_result"),
# TODO: Review unreachable code - "error": error,
# TODO: Review unreachable code - }


# TODO: Review unreachable code - # AI source detection patterns
# TODO: Review unreachable code - AI_SOURCE_PATTERNS = {
# TODO: Review unreachable code - "midjourney": [r"_[a-f0-9]{8}-[a-f0-9]{4}-", r"mj_", r"midjourney"],
# TODO: Review unreachable code - "stablediffusion": [r"\d{10,}", r"sd_", r"stable[-_]?diffusion"],
# TODO: Review unreachable code - "dalle": [r"dalle[-_]?[23]", r"openai"],
# TODO: Review unreachable code - "comfyui": [r"comfyui", r"\d{5}_\d{5}"],
# TODO: Review unreachable code - "flux": [r"flux[-_]", r"black[-_]?forest[-_]?labs"],
# TODO: Review unreachable code - "runway": [r"gen[-_]?[123]", r"runway"],
# TODO: Review unreachable code - "kling": [r"kling", r"kuaishou"],
# TODO: Review unreachable code - "pika": [r"pika[-_]?labs?"],
# TODO: Review unreachable code - }


# TODO: Review unreachable code - def match_ai_source_patterns(filename: str, generators: list[str]) -> str | None:
# TODO: Review unreachable code - """Match filename against AI source patterns.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - filename: Lowercase filename to check
# TODO: Review unreachable code - generators: List of enabled generators

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Matched generator name or None
# TODO: Review unreachable code - """
# TODO: Review unreachable code - for generator, patterns in AI_SOURCE_PATTERNS.items():
# TODO: Review unreachable code - if generator in generators:
# TODO: Review unreachable code - for pattern in patterns:
# TODO: Review unreachable code - if re.search(pattern, filename):
# TODO: Review unreachable code - return generator
# TODO: Review unreachable code - return None
