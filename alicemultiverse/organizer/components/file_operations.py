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

    def _is_media_file(self, file_path: Path) -> bool:
        """Check if file is a supported media file."""
        ext = file_path.suffix.lower()
        return ext in self.image_extensions or ext in self.video_extensions

    def _get_media_type(self, file_path: Path) -> MediaType:
        """Determine media type from file extension."""
        ext = file_path.suffix.lower()
        if ext in self.image_extensions:
            return MediaType.IMAGE
        elif ext in self.video_extensions:
            return MediaType.VIDEO
        else:
            return MediaType.UNKNOWN

    def _perform_file_operation(self, media_path: Path, dest_path: Path) -> bool:
        """Perform the actual file operation (copy or move).

        Args:
            media_path: Source file path
            dest_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.config.processing.move:
                success = self.file_handler.move_file(media_path, dest_path)
                action = "Moved"
            else:
                success = self.file_handler.copy_file(media_path, dest_path)
                action = "Copied"

            if success:
                logger.info(f"{action}: {media_path.name} -> {dest_path.parent.name}/{dest_path.name}")
            else:
                logger.error(f"Failed to {action.lower()}: {media_path.name}")

            return success

        except Exception as e:
            logger.error(f"Error during file operation: {e}")
            return False

    def _handle_existing_file_relocation(self, existing_file: Path, dest_path: Path) -> None:
        """Handle relocation of existing organized files.

        Args:
            existing_file: Path to existing file
            dest_path: New destination path
        """
        if existing_file == dest_path:
            return  # Same file, no action needed

        if existing_file.parent == dest_path.parent:
            # Same folder, just rename
            logger.debug(f"Renaming in same folder: {existing_file.name} -> {dest_path.name}")
            if self.file_handler.move_file(existing_file, dest_path):
                logger.info(f"Renamed: {existing_file.name} -> {dest_path.name}")
        else:
            # Different folder, move the file
            logger.debug(f"Moving to new folder: {existing_file} -> {dest_path}")
            if self.file_handler.move_file(existing_file, dest_path):
                logger.info(f"Relocated: {existing_file.name} -> {dest_path.parent.name}/{dest_path.name}")

    def _cleanup_duplicates(self) -> None:
        """Clean up duplicate empty folders after organization."""
        # Map to track folders with their normalized names
        folder_map = {}

        # Find all date folders
        for date_folder in self.output_dir.iterdir():
            if not date_folder.is_dir():
                continue

            # Find all project folders
            for project_folder in date_folder.iterdir():
                if not project_folder.is_dir():
                    continue

                # Normalize folder name for comparison
                normalized = project_folder.name.lower().replace("-", "_").replace(" ", "_")

                if normalized not in folder_map:
                    folder_map[normalized] = []
                folder_map[normalized].append(project_folder)

        # Clean up duplicates
        for normalized, folders in folder_map.items():
            if len(folders) > 1:
                # Sort by modification time, keep the newest
                folders.sort(key=lambda f: f.stat().st_mtime, reverse=True)

                for folder in folders[1:]:
                    # Only remove if empty
                    if not any(folder.iterdir()):
                        logger.debug(f"Removing duplicate empty folder: {folder}")
                        folder.rmdir()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex string of the file hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
