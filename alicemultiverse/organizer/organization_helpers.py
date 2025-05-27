"""
Media Organization Helper Functions

Utility functions for quality folder management, project extraction, and AI source
detection patterns. Used throughout the organizer modules for consistent file
organization and source identification.
"""

import re
from pathlib import Path
from typing import Any


def get_quality_folder_name(stars: int) -> str:
    """Get the folder name for a quality rating.

    Args:
        stars: Quality rating (1-5)

    Returns:
        Folder name like "5-star"
    """
    return f"{stars}-star"


def get_quality_from_folder_name(folder_name: str) -> int | None:
    """Extract quality rating from folder name.

    Args:
        folder_name: Folder name like "5-star"

    Returns:
        Quality rating (1-5) or None if not a quality folder
    """
    match = re.match(r"^(\d)-star$", folder_name)
    if match:
        return int(match.group(1))
    return None


def get_possible_quality_locations(base_path: Path, filename: str) -> list[Path]:
    """Get all possible locations for a file in quality folders.

    Args:
        base_path: Base directory path
        filename: Name of the file

    Returns:
        List of possible file paths in quality folders
    """
    possible_locations = []

    # Check for quality subfolders
    for quality_folder in base_path.glob("*-star"):
        possible_file = quality_folder / filename
        possible_locations.append(possible_file)

    # Also check base path
    possible_locations.append(base_path / filename)

    return possible_locations


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


def create_organize_result(
    media_path: Path,
    dest_path: Path,
    analysis: dict[str, Any],
    status: str,
    project_folder: str,
    error: str | None = None,
) -> dict[str, Any]:
    """Create a standardized organize result dictionary.

    Args:
        media_path: Source media file path
        dest_path: Destination file path
        analysis: Analysis results dictionary
        status: Operation status
        project_folder: Project folder name
        error: Optional error message

    Returns:
        OrganizeResult-compatible dictionary
    """
    return {
        "source": str(media_path),
        "project_folder": project_folder,
        "status": status,
        "destination": str(dest_path),
        "date": analysis.get("date_taken"),
        "source_type": analysis.get("source_type"),
        "media_type": analysis.get("media_type"),
        "file_number": analysis.get("file_number"),
        "quality_stars": analysis.get("quality_stars"),
        "brisque_score": analysis.get("brisque_score"),
        "pipeline_result": analysis.get("pipeline_result"),
        "error": error,
    }


# AI source detection patterns
AI_SOURCE_PATTERNS = {
    "midjourney": [r"_[a-f0-9]{8}-[a-f0-9]{4}-", r"mj_", r"midjourney"],
    "stablediffusion": [r"\d{10,}", r"sd_", r"stable[-_]?diffusion"],
    "dalle": [r"dalle[-_]?[23]", r"openai"],
    "comfyui": [r"comfyui", r"\d{5}_\d{5}"],
    "flux": [r"flux[-_]", r"black[-_]?forest[-_]?labs"],
    "runway": [r"gen[-_]?[123]", r"runway"],
    "kling": [r"kling", r"kuaishou"],
    "pika": [r"pika[-_]?labs?"],
}


def match_ai_source_patterns(filename: str, generators: list[str]) -> str | None:
    """Match filename against AI source patterns.

    Args:
        filename: Lowercase filename to check
        generators: List of enabled generators

    Returns:
        Matched generator name or None
    """
    for generator, patterns in AI_SOURCE_PATTERNS.items():
        if generator in generators:
            for pattern in patterns:
                if re.search(pattern, filename):
                    return generator
    return None
