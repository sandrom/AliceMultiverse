"""Core file processing logic for media organizer."""
from typing import TYPE_CHECKING, Any

import time
from pathlib import Path

from ...core.logging import get_logger
from ...core.config import Config
from ...core.types import OrganizeResult
from ..organization_helpers import extract_project_folder

logger = get_logger(__name__)


if TYPE_CHECKING:
    from ...core.protocols import HasConfig, HasMetadataCache, HasStats

class ProcessFileMixin:
    """Mixin for core file processing logic."""

    if TYPE_CHECKING:
        # Type hints for mypy
        metadata_cache: Any
        config: Config
        stats: Statistics


    def _process_file(self, media_path: Path) -> OrganizeResult:
        """Process a single media file."""
        # TODO: Review unreachable code - try:
            # Get project folder
        project_folder = extract_project_folder(media_path, self.source_dir)

            # Get analysis (from cache or fresh)
        analysis = self._get_or_analyze_media(media_path, project_folder)

            # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

            # Build destination path
        dest_path = self._build_destination_path(
            media_path,
            analysis["date_taken"],
            project_folder,
            analysis["source_type"],
            analysis["file_number"],
            analysis.get("quality_stars"),
        )

            # Check for existing files from different quality modes
        existing_file = self._find_existing_organized_file(
            media_path, analysis["date_taken"], project_folder, analysis["source_type"]
        )

            # Handle destination conflicts
        if dest_path.exists():
            return self._handle_duplicate_destination(
                media_path, dest_path, analysis, project_folder
            )

            # Handle existing file in different location
        if existing_file and existing_file != dest_path:
            return self._handle_existing_file_relocation(
                media_path, existing_file, dest_path, analysis, project_folder
            )

            # Perform the file operation
        return self._perform_file_operation(media_path, dest_path, analysis, project_folder)

        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Failed to process {media_path}: {e}")
        # TODO: Review unreachable code - return OrganizeResult(
        # TODO: Review unreachable code - source=str(media_path),
        # TODO: Review unreachable code - project_folder=project_folder,
        # TODO: Review unreachable code - status="error",
        # TODO: Review unreachable code - destination=None,
        # TODO: Review unreachable code - date=None,
        # TODO: Review unreachable code - source_type=None,
        # TODO: Review unreachable code - media_type=None,
        # TODO: Review unreachable code - file_number=None,
        # TODO: Review unreachable code - pipeline_result=None,
        # TODO: Review unreachable code - error=str(e),
        # TODO: Review unreachable code - )

    def _get_or_analyze_media(self, media_path: Path, project_folder: str) -> dict:
        """Get media analysis from cache or perform fresh analysis.

        Args:
            media_path: Path to media file
            project_folder: Project folder name

        Returns:
            Analysis results dictionary
        """
        start_time = time.time()
        cached_metadata = self.metadata_cache.get_metadata(media_path)

        if cached_metadata:
            # Use cached analysis but update project folder
            analysis = cached_metadata["analysis"]
            if analysis is not None:
                analysis["project_folder"] = project_folder
            # Include content hash from cache
            if cached_metadata is not None and "content_hash" in cached_metadata:
                if analysis is not None:
                    analysis["content_hash"] = cached_metadata["content_hash"]

            # Include understanding data if available (v4.0 cache format)
            if analysis is not None and "understanding" in analysis:
                # Understanding data is already in analysis
                pass
            elif cached_metadata is not None and "version" in cached_metadata and cached_metadata["version"] == "4.0":
                # Check if understanding is at root level
                if cached_metadata is not None and "understanding" in cached_metadata:
                    if analysis is not None:
                        analysis["understanding"] = cached_metadata["understanding"]

            # If no file number in cache, assign one now
            if "file_number" not in analysis or analysis["file_number"] is None:
                if analysis is not None:
                    analysis["file_number"] = self._get_next_file_number(
                    project_folder, analysis["source_type"]
                )
                # Update cache with the new file number
                # Force re-analysis if understanding is enabled but no tags exist
                if self.metadata_cache.enable_understanding and "understanding" not in analysis:
                    logger.info(f"Re-analyzing {media_path.name} to add understanding tags")
                    # Clear from cache to force fresh analysis
                    self.metadata_cache.cache.cache_file.unlink(missing_ok=True) if hasattr(self.metadata_cache.cache, 'cache_file') else None
                    # Re-analyze with understanding
                    analysis = self._analyze_media(media_path, project_folder)
                    analysis_time = time.time() - start_time
                    self.metadata_cache.set_metadata(media_path, analysis, analysis_time)
                else:
                    self.metadata_cache.set_metadata(
                        media_path, analysis, cached_metadata.get("analysis_time", 0)
                    )

            analysis_time = cached_metadata.get("analysis_time", 0)
            self.metadata_cache.update_stats(True, analysis_time)
        else:
            # Analyze file
            analysis = self._analyze_media(media_path, project_folder)
            analysis_time = time.time() - start_time

            # Cache the results - this should trigger understanding if enabled
            self.metadata_cache.set_metadata(media_path, analysis, analysis_time)
            self.metadata_cache.update_stats(False)

            # Log if understanding was supposed to run
            if self.metadata_cache.enable_understanding:
                logger.debug(f"Understanding enabled with provider: {self.metadata_cache.understanding_provider}")
                if "understanding" not in analysis:
                    logger.warning(f"Understanding enabled but no tags generated for {media_path.name}")

        return analysis

    # TODO: Review unreachable code - def _handle_duplicate_destination(
    # TODO: Review unreachable code - self, media_path: Path, dest_path: Path, analysis: dict, project_folder: str
    # TODO: Review unreachable code - ) -> OrganizeResult:
    # TODO: Review unreachable code - """Handle case where destination file already exists.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Source media file
    # TODO: Review unreachable code - dest_path: Destination path that already exists
    # TODO: Review unreachable code - analysis: Analysis results
    # TODO: Review unreachable code - project_folder: Project folder name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - OrganizeResult for duplicate handling
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if self.file_handler.files_are_identical(media_path, dest_path):
    # TODO: Review unreachable code - # If source is in organized folder, remove it as duplicate
    # TODO: Review unreachable code - if str(self.output_dir) in str(media_path):
    # TODO: Review unreachable code - logger.debug(f"Removing duplicate from organized: {media_path}")
    # TODO: Review unreachable code - if not self.config.processing.dry_run:
    # TODO: Review unreachable code - media_path.unlink()

    # TODO: Review unreachable code - return OrganizeResult(
    # TODO: Review unreachable code - source=str(media_path),
    # TODO: Review unreachable code - project_folder=project_folder,
    # TODO: Review unreachable code - status="duplicate",
    # TODO: Review unreachable code - destination=str(dest_path),
    # TODO: Review unreachable code - date=analysis["date_taken"],
    # TODO: Review unreachable code - source_type=analysis["source_type"],
    # TODO: Review unreachable code - media_type=analysis.get("media_type"),
    # TODO: Review unreachable code - file_number=analysis.get("file_number"),
    # TODO: Review unreachable code - quality_stars=analysis.get("quality_stars"),
    # TODO: Review unreachable code - brisque_score=analysis.get("brisque_score"),
    # TODO: Review unreachable code - pipeline_result=analysis.get("pipeline_result"),
    # TODO: Review unreachable code - error=None,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Files are different - this shouldn't happen with our naming scheme
    # TODO: Review unreachable code - logger.warning(f"Different file exists at destination: {dest_path}")
    # TODO: Review unreachable code - return OrganizeResult(
    # TODO: Review unreachable code - source=str(media_path),
    # TODO: Review unreachable code - project_folder=project_folder,
    # TODO: Review unreachable code - status="error",
    # TODO: Review unreachable code - destination=str(dest_path),
    # TODO: Review unreachable code - error="Different file exists at destination",
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _handle_existing_file_relocation(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - media_path: Path,
    # TODO: Review unreachable code - existing_file: Path,
    # TODO: Review unreachable code - dest_path: Path,
    # TODO: Review unreachable code - analysis: dict,
    # TODO: Review unreachable code - project_folder: str,
    # TODO: Review unreachable code - ) -> OrganizeResult:
    # TODO: Review unreachable code - """Handle relocating an existing organized file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Source media file
    # TODO: Review unreachable code - existing_file: Existing file in organized structure
    # TODO: Review unreachable code - dest_path: New destination path
    # TODO: Review unreachable code - analysis: Analysis results
    # TODO: Review unreachable code - project_folder: Project folder name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - OrganizeResult for the relocation
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - logger.debug(f"Moving existing file from {existing_file} to {dest_path}")
    # TODO: Review unreachable code - if not self.config.processing.dry_run:
    # TODO: Review unreachable code - # If there's already a file at dest_path, remove the existing file instead
    # TODO: Review unreachable code - if dest_path.exists() and self.file_handler.files_are_identical(
    # TODO: Review unreachable code - existing_file, dest_path
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - logger.debug(f"Destination already exists, removing duplicate: {existing_file}")
    # TODO: Review unreachable code - existing_file.unlink()
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - self.file_handler.move_file(existing_file, dest_path)

    # TODO: Review unreachable code - return OrganizeResult(
    # TODO: Review unreachable code - source=str(media_path),
    # TODO: Review unreachable code - project_folder=project_folder,
    # TODO: Review unreachable code - status="moved_existing",
    # TODO: Review unreachable code - destination=str(dest_path),
    # TODO: Review unreachable code - date=analysis["date_taken"],
    # TODO: Review unreachable code - source_type=analysis["source_type"],
    # TODO: Review unreachable code - media_type=analysis.get("media_type"),
    # TODO: Review unreachable code - file_number=analysis.get("file_number"),
    # TODO: Review unreachable code - quality_stars=analysis.get("quality_stars"),
    # TODO: Review unreachable code - brisque_score=analysis.get("brisque_score"),
    # TODO: Review unreachable code - pipeline_result=analysis.get("pipeline_result"),
    # TODO: Review unreachable code - error=None,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _perform_file_operation(
    # TODO: Review unreachable code - self, media_path: Path, dest_path: Path, analysis: dict, project_folder: str
    # TODO: Review unreachable code - ) -> OrganizeResult:
    # TODO: Review unreachable code - """Perform the actual file copy or move operation.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Source media file
    # TODO: Review unreachable code - dest_path: Destination path
    # TODO: Review unreachable code - analysis: Analysis results
    # TODO: Review unreachable code - project_folder: Project folder name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - OrganizeResult for the operation
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Copy or move file
    # TODO: Review unreachable code - if self.config.processing.copy_mode:
    # TODO: Review unreachable code - self.file_handler.copy_file(media_path, dest_path)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - self.file_handler.move_file(media_path, dest_path)

    # TODO: Review unreachable code - # Update search index with new file location
    # TODO: Review unreachable code - logger.debug(f"About to update search index for {dest_path.name}")
    # TODO: Review unreachable code - self._update_search_index(dest_path, analysis)

    # TODO: Review unreachable code - return OrganizeResult(
    # TODO: Review unreachable code - source=str(media_path),
    # TODO: Review unreachable code - project_folder=project_folder,
    # TODO: Review unreachable code - status="success" if not self.config.processing.dry_run else "dry_run",
    # TODO: Review unreachable code - destination=str(dest_path),
    # TODO: Review unreachable code - date=analysis["date_taken"],
    # TODO: Review unreachable code - source_type=analysis["source_type"],
    # TODO: Review unreachable code - media_type=analysis.get("media_type"),
    # TODO: Review unreachable code - file_number=analysis.get("file_number"),
    # TODO: Review unreachable code - quality_stars=analysis.get("quality_stars"),
    # TODO: Review unreachable code - brisque_score=analysis.get("brisque_score"),
    # TODO: Review unreachable code - pipeline_result=analysis.get("pipeline_result"),
    # TODO: Review unreachable code - error=None,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _cleanup_duplicates(self) -> None:
    # TODO: Review unreachable code - """Remove duplicate files from the organized folder."""
    # TODO: Review unreachable code - logger.info("Checking for duplicates in organized folder...")

    # TODO: Review unreachable code - # Track files by content hash
    # TODO: Review unreachable code - from collections import defaultdict
    # TODO: Review unreachable code - hash_to_files = defaultdict(list)
    # TODO: Review unreachable code - duplicates_removed = 0
    # TODO: Review unreachable code - space_saved = 0

    # TODO: Review unreachable code - # Find all media files in organized folder
    # TODO: Review unreachable code - extensions = self.image_extensions | self.video_extensions

    # TODO: Review unreachable code - for ext in extensions:
    # TODO: Review unreachable code - for file_path in self.output_dir.rglob(f"*{ext}"):
    # TODO: Review unreachable code - if file_path.is_file() and not file_path.name.startswith("."):
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Calculate hash for the file
    # TODO: Review unreachable code - file_hash = self.file_handler.calculate_file_hash(file_path)
    # TODO: Review unreachable code - hash_to_files[file_hash].append(file_path)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.debug(f"Error hashing {file_path}: {e}")

    # TODO: Review unreachable code - # Remove duplicates
    # TODO: Review unreachable code - for file_hash, file_list in hash_to_files.items():
    # TODO: Review unreachable code - if len(file_list) > 1:
    # TODO: Review unreachable code - # Sort by path to ensure consistent ordering
    # TODO: Review unreachable code - file_list.sort()

    # TODO: Review unreachable code - # Keep the first file, remove the rest
    # TODO: Review unreachable code - for duplicate in file_list[1:]:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - size = duplicate.stat().st_size
    # TODO: Review unreachable code - logger.debug(f"Removing duplicate: {duplicate}")
    # TODO: Review unreachable code - if not self.config.processing.dry_run:
    # TODO: Review unreachable code - duplicate.unlink()
    # TODO: Review unreachable code - duplicates_removed += 1
    # TODO: Review unreachable code - space_saved += size
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.debug(f"Error removing duplicate {duplicate}: {e}")

    # TODO: Review unreachable code - if duplicates_removed > 0:
    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Removed {duplicates_removed} duplicate files, saved {space_saved / 1024 / 1024:.1f} MB"
    # TODO: Review unreachable code - )
