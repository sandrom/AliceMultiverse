"""Organization logic for media organizer."""

import re
from pathlib import Path

from ...core.constants import SEQUENCE_FORMAT
from ...core.logging import get_logger
from ..organization_helpers import get_quality_folder_name

logger = get_logger(__name__)


class OrganizationLogicMixin:
    """Mixin for media organization logic."""

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

        # If not found in expected location, search more broadly
        # This helps catch files that may have been organized on different dates
        logger.debug(f"Searching entire organized structure for duplicate of {source_path.name}")

        # Search all date folders
        for date_dir in self.output_dir.iterdir():
            if not date_dir.is_dir() or not date_dir.name.startswith("20"):  # Basic date check
                continue

            project_dir = date_dir / project_folder / source_type
            if project_dir.exists():
                # Check both with and without quality folders
                possible_locations = []

                # Direct location
                possible_locations.extend(
                    project_dir.glob(f"{project_folder}-*{source_path.suffix}")
                )

                # Check subdirectories
                for subdir in project_dir.iterdir():
                    if subdir.is_dir():
                        possible_locations.extend(
                            subdir.glob(f"{project_folder}-*{source_path.suffix}")
                        )

                for existing_path in possible_locations:
                    if existing_path.is_file() and self.file_handler.files_are_identical(
                        source_path, existing_path
                    ):
                        logger.debug(f"Found duplicate in different date folder: {existing_path}")
                        return existing_path

        return None

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

    def _build_destination_path(
        self,
        source_path: Path,
        date_taken: str,
        project_folder: str,
        source_type: str,
        file_number: int,
        quality_stars: int | None = None,
    ) -> Path:
        """Build destination path for organized file."""
        # Base path: organized/YYYY-MM-DD/project/source
        dest_dir = self.output_dir / date_taken / project_folder / source_type

        # Add quality rating subfolder if applicable
        if quality_stars is not None:
            dest_dir = dest_dir / get_quality_folder_name(quality_stars)

        # Build filename using the provided file number
        base_name = f"{project_folder}-"
        ext = source_path.suffix
        filename = f"{base_name}{SEQUENCE_FORMAT.format(file_number)}{ext}"

        return dest_dir / filename

    def _handle_duplicate_destination(self, dest_path: Path, media_path: Path, content_hash: str) -> Path:
        """Handle cases where destination file already exists.
        
        Args:
            dest_path: Intended destination path
            media_path: Source media path
            content_hash: Content hash of the media file
            
        Returns:
            Final destination path (may be modified to avoid conflicts)
        """
        if not dest_path.exists():
            return dest_path

        # Check if existing file is identical
        if self.file_handler.files_are_identical(media_path, dest_path):
            logger.debug(f"Identical file already exists at destination: {dest_path}")
            return dest_path

        # Files are different - need to create unique filename
        counter = 1
        base_path = dest_path.parent / dest_path.stem
        suffix = dest_path.suffix

        while True:
            new_path = Path(f"{base_path}_v{counter}{suffix}")
            if not new_path.exists():
                logger.info(f"Destination exists with different content, using: {new_path.name}")
                return new_path
            counter += 1

    def _cleanup_empty_folders(self) -> None:
        """Clean up empty folders in the organized directory."""
        # Track folders to check
        folders_to_check = set()

        # Find all folders
        for folder in self.output_dir.rglob("*"):
            if folder.is_dir():
                folders_to_check.add(folder)

        # Sort folders by depth (deepest first) to clean up from bottom to top
        sorted_folders = sorted(folders_to_check, key=lambda p: len(p.parts), reverse=True)

        # Remove empty folders
        for folder in sorted_folders:
            try:
                if folder.exists() and not any(folder.iterdir()):
                    logger.debug(f"Removing empty folder: {folder}")
                    folder.rmdir()
            except Exception as e:
                logger.debug(f"Could not remove folder {folder}: {e}")
