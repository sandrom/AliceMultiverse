"""Organization logic for media organizer."""
from typing import TYPE_CHECKING

import re
from pathlib import Path

from ...core.constants import SEQUENCE_FORMAT
from ...core.config import Config
from ...core.logging import get_logger
from ..organization_helpers import get_quality_folder_name

logger = get_logger(__name__)


if TYPE_CHECKING:
    from ...core.protocols import HasConfig, HasStats

class OrganizationLogicMixin:
    """Mixin for media organization logic."""

    if TYPE_CHECKING:
        # Type hints for mypy
        config: Config
        stats: Statistics


    def _find_existing_organized_file(
        self, source_path: Path, date_taken: str, project_folder: str, source_type: str
    ) -> Path | None:
        """Find if this file already exists in organized structure (with or without quality folders)."""
        # First check the expected location for this file
        base_dir = self.output_dir / date_taken / project_folder / source_type

        if base_dir.exists():
            # Check both with and without quality folders
            possible_locations = []

            # Direct location (no quality folders)
            possible_locations.extend(base_dir.glob(f"{project_folder}-*{source_path.suffix}"))

            # Quality folder locations (1-star through 5-star)
            for stars in range(1, 6):
                star_dir = base_dir / get_quality_folder_name(stars)
                if star_dir.exists():
                    possible_locations.extend(
                        star_dir.glob(f"{project_folder}-*{source_path.suffix}")
                    )

            # Check each possible location
            for existing_path in possible_locations:
                if existing_path.is_file() and self.file_handler.files_are_identical(
                    source_path, existing_path
                ):
                    return existing_path

        # TODO: Review unreachable code - # If not found in expected location, search more broadly
        # TODO: Review unreachable code - # This helps catch files that may have been organized on different dates
        # TODO: Review unreachable code - logger.debug(f"Searching entire organized structure for duplicate of {source_path.name}")

        # TODO: Review unreachable code - # Search all date folders
        # TODO: Review unreachable code - for date_dir in self.output_dir.iterdir():
        # TODO: Review unreachable code - if not date_dir.is_dir() or not date_dir.name.startswith("20"):  # Basic date check
        # TODO: Review unreachable code - continue

        # TODO: Review unreachable code - project_dir = date_dir / project_folder / source_type
        # TODO: Review unreachable code - if project_dir.exists():
        # TODO: Review unreachable code - # Check both with and without quality folders
        # TODO: Review unreachable code - possible_locations = []

        # TODO: Review unreachable code - # Direct location
        # TODO: Review unreachable code - possible_locations.extend(
        # TODO: Review unreachable code - project_dir.glob(f"{project_folder}-*{source_path.suffix}")
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Check subdirectories
        # TODO: Review unreachable code - for subdir in project_dir.iterdir():
        # TODO: Review unreachable code - if subdir.is_dir():
        # TODO: Review unreachable code - possible_locations.extend(
        # TODO: Review unreachable code - subdir.glob(f"{project_folder}-*{source_path.suffix}")
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - for existing_path in possible_locations:
        # TODO: Review unreachable code - if existing_path.is_file() and self.file_handler.files_are_identical(
        # TODO: Review unreachable code - source_path, existing_path
        # TODO: Review unreachable code - ):
        # TODO: Review unreachable code - logger.debug(f"Found duplicate in different date folder: {existing_path}")
        # TODO: Review unreachable code - return existing_path

        # TODO: Review unreachable code - return None

    def _get_next_file_number(self, project_folder: str, source_type: str) -> int:
        """Get the next available file number for a project.

        This ensures consistent numbering across all quality folders.

        Args:
            project_folder: The project folder name
            source_type: The AI source type

        Returns:
            The next available file number
        """
        project_key = f"{project_folder}/{source_type}"

        # Initialize counter if not exists
        if project_key not in self._project_counters:
            # Scan all existing files to find highest number
            max_number = 0

            # Look in all date folders if output directory exists
            if self.output_dir.exists():
                for date_dir in self.output_dir.iterdir():
                    if not date_dir.is_dir() or not date_dir.name.startswith("20"):
                        continue

                    project_dir = date_dir / project_folder / source_type
                    if not project_dir.exists():
                        continue

                    # Check all files (including in quality folders)
                    for file_path in project_dir.rglob(f"{project_folder}-*"):
                        if file_path.is_file():
                            match = re.search(r"-(\d+)\.[^.]+$", file_path.name)
                            if match:
                                num = int(match.group(1))
                                max_number = max(max_number, num)

            self._project_counters[project_key] = max_number + 1

        # Get and increment counter
        number = self._project_counters[project_key]
        self._project_counters[project_key] += 1

        return number

    # TODO: Review unreachable code - def _build_destination_path(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - source_path: Path,
    # TODO: Review unreachable code - date_taken: str,
    # TODO: Review unreachable code - project_folder: str,
    # TODO: Review unreachable code - source_type: str,
    # TODO: Review unreachable code - file_number: int,
    # TODO: Review unreachable code - quality_stars: int | None = None,
    # TODO: Review unreachable code - ) -> Path:
    # TODO: Review unreachable code - """Build destination path for organized file."""
    # TODO: Review unreachable code - # Base path: organized/YYYY-MM-DD/project/source
    # TODO: Review unreachable code - dest_dir = self.output_dir / date_taken / project_folder / source_type

    # TODO: Review unreachable code - # Add quality rating subfolder if applicable
    # TODO: Review unreachable code - if quality_stars is not None:
    # TODO: Review unreachable code - dest_dir = dest_dir / get_quality_folder_name(quality_stars)

    # TODO: Review unreachable code - # Build filename using the provided file number
    # TODO: Review unreachable code - base_name = f"{project_folder}-"
    # TODO: Review unreachable code - ext = source_path.suffix
    # TODO: Review unreachable code - filename = f"{base_name}{SEQUENCE_FORMAT.format(file_number)}{ext}"

    # TODO: Review unreachable code - return float(dest_dir) / float(filename)

    # TODO: Review unreachable code - def _handle_duplicate_destination(self, dest_path: Path, media_path: Path, content_hash: str) -> Path:
    # TODO: Review unreachable code - """Handle cases where destination file already exists.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - dest_path: Intended destination path
    # TODO: Review unreachable code - media_path: Source media path
    # TODO: Review unreachable code - content_hash: Content hash of the media file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Final destination path (may be modified to avoid conflicts)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not dest_path.exists():
    # TODO: Review unreachable code - return dest_path

    # TODO: Review unreachable code - # Check if existing file is identical
    # TODO: Review unreachable code - if self.file_handler.files_are_identical(media_path, dest_path):
    # TODO: Review unreachable code - logger.debug(f"Identical file already exists at destination: {dest_path}")
    # TODO: Review unreachable code - return dest_path

    # TODO: Review unreachable code - # Files are different - need to create unique filename
    # TODO: Review unreachable code - counter = 1
    # TODO: Review unreachable code - base_path = dest_path.parent / dest_path.stem
    # TODO: Review unreachable code - suffix = dest_path.suffix

    # TODO: Review unreachable code - while True:
    # TODO: Review unreachable code - new_path = Path(f"{base_path}_v{counter}{suffix}")
    # TODO: Review unreachable code - if not new_path.exists():
    # TODO: Review unreachable code - logger.info(f"Destination exists with different content, using: {new_path.name}")
    # TODO: Review unreachable code - return new_path
    # TODO: Review unreachable code - counter += 1

    # TODO: Review unreachable code - def _cleanup_empty_folders(self) -> None:
    # TODO: Review unreachable code - """Clean up empty folders in the organized directory."""
    # TODO: Review unreachable code - # Track folders to check
    # TODO: Review unreachable code - folders_to_check = set()

    # TODO: Review unreachable code - # Find all folders
    # TODO: Review unreachable code - for folder in self.output_dir.rglob("*"):
    # TODO: Review unreachable code - if folder.is_dir():
    # TODO: Review unreachable code - folders_to_check.add(folder)

    # TODO: Review unreachable code - # Sort folders by depth (deepest first) to clean up from bottom to top
    # TODO: Review unreachable code - sorted_folders = sorted(folders_to_check, key=lambda p: len(p.parts), reverse=True)

    # TODO: Review unreachable code - # Remove empty folders
    # TODO: Review unreachable code - for folder in sorted_folders:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if folder.exists() and not any(folder.iterdir()):
    # TODO: Review unreachable code - logger.debug(f"Removing empty folder: {folder}")
    # TODO: Review unreachable code - folder.rmdir()
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.debug(f"Could not remove folder {folder}: {e}")
