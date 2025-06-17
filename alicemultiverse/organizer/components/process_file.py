"""Core file processing logic for media organizer."""

import time
from pathlib import Path

from ...core.logging import get_logger
from ...core.types import OrganizeResult
from ..organization_helpers import extract_project_folder

logger = get_logger(__name__)


class ProcessFileMixin:
    """Mixin for core file processing logic."""
    
    def _process_file(self, media_path: Path) -> OrganizeResult:
        """Process a single media file."""
        try:
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

        except Exception as e:
            logger.error(f"Failed to process {media_path}: {e}")
            return OrganizeResult(
                source=str(media_path),
                project_folder=project_folder,
                status="error",
                destination=None,
                date=None,
                source_type=None,
                media_type=None,
                file_number=None,
                pipeline_result=None,
                error=str(e),
            )

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
            analysis["project_folder"] = project_folder
            # Include content hash from cache
            if "content_hash" in cached_metadata:
                analysis["content_hash"] = cached_metadata["content_hash"]

            # Include understanding data if available (v4.0 cache format)
            if "understanding" in analysis:
                # Understanding data is already in analysis
                pass
            elif "version" in cached_metadata and cached_metadata["version"] == "4.0":
                # Check if understanding is at root level
                if "understanding" in cached_metadata:
                    analysis["understanding"] = cached_metadata["understanding"]

            # If no file number in cache, assign one now
            if "file_number" not in analysis or analysis["file_number"] is None:
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

    def _handle_duplicate_destination(
        self, media_path: Path, dest_path: Path, analysis: dict, project_folder: str
    ) -> OrganizeResult:
        """Handle case where destination file already exists.

        Args:
            media_path: Source media file
            dest_path: Destination path that already exists
            analysis: Analysis results
            project_folder: Project folder name

        Returns:
            OrganizeResult for duplicate handling
        """
        if self.file_handler.files_are_identical(media_path, dest_path):
            # If source is in organized folder, remove it as duplicate
            if str(self.output_dir) in str(media_path):
                logger.debug(f"Removing duplicate from organized: {media_path}")
                if not self.config.processing.dry_run:
                    media_path.unlink()

            return OrganizeResult(
                source=str(media_path),
                project_folder=project_folder,
                status="duplicate",
                destination=str(dest_path),
                date=analysis["date_taken"],
                source_type=analysis["source_type"],
                media_type=analysis.get("media_type"),
                file_number=analysis.get("file_number"),
                quality_stars=analysis.get("quality_stars"),
                brisque_score=analysis.get("brisque_score"),
                pipeline_result=analysis.get("pipeline_result"),
                error=None,
            )

        # Files are different - this shouldn't happen with our naming scheme
        logger.warning(f"Different file exists at destination: {dest_path}")
        return OrganizeResult(
            source=str(media_path),
            project_folder=project_folder,
            status="error",
            destination=str(dest_path),
            error="Different file exists at destination",
        )

    def _handle_existing_file_relocation(
        self,
        media_path: Path,
        existing_file: Path,
        dest_path: Path,
        analysis: dict,
        project_folder: str,
    ) -> OrganizeResult:
        """Handle relocating an existing organized file.

        Args:
            media_path: Source media file
            existing_file: Existing file in organized structure
            dest_path: New destination path
            analysis: Analysis results
            project_folder: Project folder name

        Returns:
            OrganizeResult for the relocation
        """
        logger.debug(f"Moving existing file from {existing_file} to {dest_path}")
        if not self.config.processing.dry_run:
            # If there's already a file at dest_path, remove the existing file instead
            if dest_path.exists() and self.file_handler.files_are_identical(
                existing_file, dest_path
            ):
                logger.debug(f"Destination already exists, removing duplicate: {existing_file}")
                existing_file.unlink()
            else:
                self.file_handler.move_file(existing_file, dest_path)

        return OrganizeResult(
            source=str(media_path),
            project_folder=project_folder,
            status="moved_existing",
            destination=str(dest_path),
            date=analysis["date_taken"],
            source_type=analysis["source_type"],
            media_type=analysis.get("media_type"),
            file_number=analysis.get("file_number"),
            quality_stars=analysis.get("quality_stars"),
            brisque_score=analysis.get("brisque_score"),
            pipeline_result=analysis.get("pipeline_result"),
            error=None,
        )

    def _perform_file_operation(
        self, media_path: Path, dest_path: Path, analysis: dict, project_folder: str
    ) -> OrganizeResult:
        """Perform the actual file copy or move operation.

        Args:
            media_path: Source media file
            dest_path: Destination path
            analysis: Analysis results
            project_folder: Project folder name

        Returns:
            OrganizeResult for the operation
        """
        # Copy or move file
        if self.config.processing.copy_mode:
            self.file_handler.copy_file(media_path, dest_path)
        else:
            self.file_handler.move_file(media_path, dest_path)

        # Update search index with new file location
        logger.debug(f"About to update search index for {dest_path.name}")
        self._update_search_index(dest_path, analysis)

        return OrganizeResult(
            source=str(media_path),
            project_folder=project_folder,
            status="success" if not self.config.processing.dry_run else "dry_run",
            destination=str(dest_path),
            date=analysis["date_taken"],
            source_type=analysis["source_type"],
            media_type=analysis.get("media_type"),
            file_number=analysis.get("file_number"),
            quality_stars=analysis.get("quality_stars"),
            brisque_score=analysis.get("brisque_score"),
            pipeline_result=analysis.get("pipeline_result"),
            error=None,
        )

    def _cleanup_duplicates(self) -> None:
        """Remove duplicate files from the organized folder."""
        logger.info("Checking for duplicates in organized folder...")

        # Track files by content hash
        from collections import defaultdict
        hash_to_files = defaultdict(list)
        duplicates_removed = 0
        space_saved = 0

        # Find all media files in organized folder
        extensions = self.image_extensions | self.video_extensions

        for ext in extensions:
            for file_path in self.output_dir.rglob(f"*{ext}"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    try:
                        # Calculate hash for the file
                        file_hash = self.file_handler.calculate_file_hash(file_path)
                        hash_to_files[file_hash].append(file_path)
                    except Exception as e:
                        logger.debug(f"Error hashing {file_path}: {e}")

        # Remove duplicates
        for file_hash, file_list in hash_to_files.items():
            if len(file_list) > 1:
                # Sort by path to ensure consistent ordering
                file_list.sort()

                # Keep the first file, remove the rest
                for duplicate in file_list[1:]:
                    try:
                        size = duplicate.stat().st_size
                        logger.debug(f"Removing duplicate: {duplicate}")
                        if not self.config.processing.dry_run:
                            duplicate.unlink()
                        duplicates_removed += 1
                        space_saved += size
                    except Exception as e:
                        logger.debug(f"Error removing duplicate {duplicate}: {e}")

        if duplicates_removed > 0:
            logger.info(
                f"Removed {duplicates_removed} duplicate files, saved {space_saved / 1024 / 1024:.1f} MB"
            )