"""File operations for media organizer."""
from typing import TYPE_CHECKING

import hashlib
from pathlib import Path

from ...core.logging import get_logger
from ...core.config import Config
from ...core.types import MediaType

logger = get_logger(__name__)


if TYPE_CHECKING:
    from ...core.protocols import HasConfig, HasStats

class FileOperationsMixin:
    """Mixin for file-related operations."""

    if TYPE_CHECKING:
        # Type hints for mypy
        config: Config
        stats: Statistics


    def _find_media_files(self) -> list[Path]:
        """Find all media files in source directory."""
        media_files = []

        # Folders to exclude from scanning
        exclude_folders = {'sorted-out', 'sorted_out', '.metadata', '.alice'}
        excluded_count = 0

        # Find all project folders
        for project_dir in self.source_dir.iterdir():
            if not project_dir.is_dir():
                continue

            if project_dir.name.startswith(".") or project_dir.name.lower() in exclude_folders:
                if project_dir.name.lower() in {'sorted-out', 'sorted_out'}:
                    excluded_count += 1
                    logger.debug(f"Skipping excluded folder: {project_dir.name}")
                continue

            # Find media files in project
            for file_path in project_dir.rglob("*"):
                if file_path.is_file() and self._is_media_file(file_path):
                    # Check if any parent directory is excluded
                    should_exclude = False
                    for parent in file_path.parents:
                        if parent == self.source_dir:
                            break
                        if parent.name.lower() in exclude_folders:
                            should_exclude = True
                            break

                    if not should_exclude:
                        media_files.append(file_path)
                    else:
                        excluded_count += 1

        if excluded_count > 0:
            logger.info(f"Excluded {excluded_count} files in 'sorted-out' folders")

        return sorted(media_files)

    # TODO: Review unreachable code - def _is_media_file(self, file_path: Path) -> bool:
    # TODO: Review unreachable code - """Check if file is a supported media file."""
    # TODO: Review unreachable code - ext = file_path.suffix.lower()
    # TODO: Review unreachable code - return ext in self.image_extensions or ext in self.video_extensions

    # TODO: Review unreachable code - def _get_media_type(self, file_path: Path) -> MediaType:
    # TODO: Review unreachable code - """Determine media type from file extension."""
    # TODO: Review unreachable code - ext = file_path.suffix.lower()
    # TODO: Review unreachable code - if ext in self.image_extensions:
    # TODO: Review unreachable code - return MediaType.IMAGE
    # TODO: Review unreachable code - elif ext in self.video_extensions:
    # TODO: Review unreachable code - return MediaType.VIDEO
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return MediaType.UNKNOWN

    # TODO: Review unreachable code - def _perform_file_operation(self, media_path: Path, dest_path: Path) -> bool:
    # TODO: Review unreachable code - """Perform the actual file operation (copy or move).

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Source file path
    # TODO: Review unreachable code - dest_path: Destination file path

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if successful, False otherwise
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if self.config.processing.move:
    # TODO: Review unreachable code - success = self.file_handler.move_file(media_path, dest_path)
    # TODO: Review unreachable code - action = "Moved"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - success = self.file_handler.copy_file(media_path, dest_path)
    # TODO: Review unreachable code - action = "Copied"

    # TODO: Review unreachable code - if success:
    # TODO: Review unreachable code - logger.info(f"{action}: {media_path.name} -> {dest_path.parent.name}/{dest_path.name}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - logger.error(f"Failed to {action.lower()}: {media_path.name}")

    # TODO: Review unreachable code - return success

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error during file operation: {e}")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - def _handle_existing_file_relocation(self, existing_file: Path, dest_path: Path) -> None:
    # TODO: Review unreachable code - """Handle relocation of existing organized files.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - existing_file: Path to existing file
    # TODO: Review unreachable code - dest_path: New destination path
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if existing_file == dest_path:
    # TODO: Review unreachable code - return  # Same file, no action needed

    # TODO: Review unreachable code - if existing_file.parent == dest_path.parent:
    # TODO: Review unreachable code - # Same folder, just rename
    # TODO: Review unreachable code - logger.debug(f"Renaming in same folder: {existing_file.name} -> {dest_path.name}")
    # TODO: Review unreachable code - if self.file_handler.move_file(existing_file, dest_path):
    # TODO: Review unreachable code - logger.info(f"Renamed: {existing_file.name} -> {dest_path.name}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Different folder, move the file
    # TODO: Review unreachable code - logger.debug(f"Moving to new folder: {existing_file} -> {dest_path}")
    # TODO: Review unreachable code - if self.file_handler.move_file(existing_file, dest_path):
    # TODO: Review unreachable code - logger.info(f"Relocated: {existing_file.name} -> {dest_path.parent.name}/{dest_path.name}")

    # TODO: Review unreachable code - def _cleanup_duplicates(self) -> None:
    # TODO: Review unreachable code - """Clean up duplicate empty folders after organization."""
    # TODO: Review unreachable code - # Map to track folders with their normalized names
    # TODO: Review unreachable code - folder_map = {}

    # TODO: Review unreachable code - # Find all date folders
    # TODO: Review unreachable code - for date_folder in self.output_dir.iterdir():
    # TODO: Review unreachable code - if not date_folder.is_dir():
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Find all project folders
    # TODO: Review unreachable code - for project_folder in date_folder.iterdir():
    # TODO: Review unreachable code - if not project_folder.is_dir():
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Normalize folder name for comparison
    # TODO: Review unreachable code - normalized = project_folder.name.lower().replace("-", "_").replace(" ", "_")

    # TODO: Review unreachable code - if normalized not in folder_map:
    # TODO: Review unreachable code - folder_map[normalized] = []
    # TODO: Review unreachable code - folder_map[normalized].append(project_folder)

    # TODO: Review unreachable code - # Clean up duplicates
    # TODO: Review unreachable code - for normalized, folders in folder_map.items():
    # TODO: Review unreachable code - if len(folders) > 1:
    # TODO: Review unreachable code - # Sort by modification time, keep the newest
    # TODO: Review unreachable code - folders.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    # TODO: Review unreachable code - for folder in folders[1:]:
    # TODO: Review unreachable code - # Only remove if empty
    # TODO: Review unreachable code - if not any(folder.iterdir()):
    # TODO: Review unreachable code - logger.debug(f"Removing duplicate empty folder: {folder}")
    # TODO: Review unreachable code - folder.rmdir()

    # TODO: Review unreachable code - def _calculate_file_hash(self, file_path: Path) -> str:
    # TODO: Review unreachable code - """Calculate SHA256 hash of a file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to the file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Hex string of the file hash
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - sha256_hash = hashlib.sha256()
    # TODO: Review unreachable code - with open(file_path, "rb") as f:
    # TODO: Review unreachable code - for byte_block in iter(lambda: f.read(4096), b""):
    # TODO: Review unreachable code - sha256_hash.update(byte_block)
    # TODO: Review unreachable code - return sha256_hash.hexdigest()
