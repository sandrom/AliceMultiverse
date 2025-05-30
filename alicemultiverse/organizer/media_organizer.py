"""Media organizer implementation."""

import re
import signal
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from omegaconf import DictConfig
from PIL import Image
from tqdm import tqdm

from ..core.cache_migration import MetadataCacheAdapter as MetadataCache
from ..core.constants import OUTPUT_DATE_FORMAT, SEQUENCE_FORMAT
from ..core.file_operations import FileHandler
from ..core.logging import get_logger
from ..core.types import AnalysisResult, MediaType, OrganizeResult, Statistics
from ..quality.brisque import BRISQUEAssessor
from ..quality.brisque import is_available as brisque_available
from ..quality.pipeline_stages import create_pipeline_stages
from .organization_helpers import (
    extract_project_folder,
    get_quality_folder_name,
    match_ai_source_patterns,
)

logger = get_logger(__name__)


class MediaOrganizer:
    """Main class for organizing AI-generated media files."""

    def __init__(self, config: DictConfig):
        """Initialize the media organizer.

        Args:
            config: Configuration object
        """
        self._project_counters = {}  # Track next number for each project
        self.config = config
        self.source_dir = Path(config.paths.inbox)
        self.output_dir = Path(config.paths.organized)

        # Initialize components
        self.file_handler = FileHandler(dry_run=getattr(config.processing, "dry_run", False))
        self.metadata_cache = MetadataCache(
            self.source_dir, force_reindex=config.processing.force_reindex
        )

        # Initialize quality assessor if enabled
        self.quality_enabled = config.processing.quality
        self.quality_assessor = None
        if self.quality_enabled and brisque_available():
            thresholds = self._parse_quality_thresholds(config.quality.thresholds)
            self.quality_assessor = BRISQUEAssessor(thresholds)
        elif self.quality_enabled:
            logger.warning("Quality assessment requested but BRISQUE not available")
            self.quality_enabled = False

        # Initialize pipeline stages if configured
        self.pipeline_stages = create_pipeline_stages(config)
        self.pipeline_enabled = bool(self.pipeline_stages)

        # Cost tracking for pipeline
        pipeline_config = getattr(config, "pipeline", {})
        self.pipeline_cost_limit = getattr(pipeline_config, "cost_limit", None)
        self.pipeline_cost_total = 0.0

        # Watch mode settings
        self.watch_mode = config.processing.watch
        self.watch_interval = config.processing.watch_interval
        self.processed_files: set[Path] = set()
        self.stop_watching = False

        # Statistics
        self.stats: Statistics = self._init_statistics()

        # AI generator patterns
        self.ai_generators = {
            "image": config.ai_generators.image,
            "video": config.ai_generators.video,
        }

        # File extensions
        self.image_extensions = set(config.file_types.image_extensions)
        self.video_extensions = set(config.file_types.video_extensions)

    def organize(self) -> bool:
        """Organize media files.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.watch_mode:
                return self._watch_and_organize()
            else:
                return self._organize_once()
        except KeyboardInterrupt:
            logger.info("\nOrganization cancelled by user")
            raise  # Re-raise to let CLI handle the exit code
        except Exception as e:
            logger.error(f"Organization failed: {e}")
            return False

    def _organize_once(self) -> bool:
        """Organize files once and return."""
        logger.info(f"Organizing files from {self.source_dir} to {self.output_dir}")

        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return False

        # Find all media files
        media_files = self._find_media_files()
        if not media_files:
            logger.info("No media files found to organize")
            return True

        logger.info(f"Found {len(media_files)} media files to process")

        # Process files with progress bar
        with tqdm(total=len(media_files), desc="Organizing files") as pbar:
            for media_file in media_files:
                result = self._process_file(media_file)
                self._update_statistics(result)
                pbar.update(1)

        # Clean up duplicates in organized folder
        if self.output_dir.exists():
            self._cleanup_duplicates()

        # Log statistics
        self._log_statistics()

        # Log cache statistics
        cache_stats = self.metadata_cache.get_stats()
        if cache_stats["total_processed"] > 0:
            logger.info(
                f"Cache performance: {cache_stats['cache_hits']} hits, "
                f"{cache_stats['cache_misses']} misses "
                f"({cache_stats['hit_rate']:.1f}% hit rate)"
            )
            if cache_stats["time_saved"] > 0:
                logger.info(f"Time saved by cache: {cache_stats['time_saved']:.1f} seconds")

        return True

    def _watch_and_organize(self) -> bool:
        """Watch for new files and organize them continuously."""
        logger.info(f"Watching {self.source_dir} for new files...")
        logger.info("Press Ctrl+C to stop")

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

        # Process existing files first
        self._organize_once()

        # Track processed files
        self.processed_files = set(self._find_media_files())

        # Watch for new files
        while not self.stop_watching:
            try:
                time.sleep(self.watch_interval)

                # Find new files
                current_files = set(self._find_media_files())
                new_files = current_files - self.processed_files

                if new_files:
                    logger.info(f"Found {len(new_files)} new files")
                    for media_file in new_files:
                        result = self._process_file(media_file)
                        self._update_statistics(result)
                        self.processed_files.add(media_file)

                    # Clean up duplicates after processing batch
                    if self.output_dir.exists():
                        self._cleanup_duplicates()

            except Exception as e:
                logger.error(f"Error in watch mode: {e}")

        logger.info("\nStopped watching")
        self._log_statistics()
        return True

    def _signal_handler(self, signum, frame):
        """Handle interrupt signal."""
        _ = signum, frame  # Unused but required by signal interface
        self.stop_watching = True

    def _find_media_files(self) -> list[Path]:
        """Find all media files in source directory."""
        media_files = []

        # Find all project folders
        for project_dir in self.source_dir.iterdir():
            if not project_dir.is_dir():
                continue

            if project_dir.name.startswith("."):
                continue

            # Find media files in project
            for file_path in project_dir.rglob("*"):
                if file_path.is_file() and self._is_media_file(file_path):
                    media_files.append(file_path)

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
                quality_stars=None,
                brisque_score=None,
                pipeline_result=None,
                error=str(e),
            )

    def _analyze_media(self, media_path: Path, project_folder: str) -> AnalysisResult:
        """Analyze media file to extract metadata."""
        media_type = self._get_media_type(media_path)

        # Detect AI source
        source_type = self._detect_ai_source(media_path, media_type)

        # Get date taken
        date_taken = self._get_date_taken(media_path, media_type)

        # Assign unique file number for this project/source combination
        file_number = self._get_next_file_number(project_folder, source_type)

        # Build metadata dict for pipeline stages
        metadata = {
            "source_type": source_type,
            "date_taken": date_taken,
            "project_folder": project_folder,
            "media_type": media_type,
            "file_number": file_number,
        }

        # Quality assessment for images
        quality_stars = None
        brisque_score = None

        if media_type == MediaType.IMAGE:
            # Run pipeline stages if configured (includes BRISQUE)
            if self.pipeline_enabled:
                metadata = self._run_pipeline_stages(media_path, metadata)
                quality_stars = metadata.get("quality_stars")
                brisque_score = metadata.get("brisque_score")
            # Otherwise just run BRISQUE if enabled
            elif self.quality_enabled:
                brisque_score, quality_stars = self.quality_assessor.assess_quality(media_path)
                metadata["quality_stars"] = quality_stars
                metadata["brisque_score"] = brisque_score

        return AnalysisResult(
            source_type=source_type,
            date_taken=date_taken,
            project_folder=project_folder,
            media_type=media_type,
            file_number=file_number,
            quality_stars=quality_stars,
            brisque_score=brisque_score,
            pipeline_result=metadata.get("pipeline_stages"),  # Include pipeline results
        )

    def _detect_ai_source(self, media_path: Path, media_type: MediaType) -> str:
        """Detect AI generation source from filename and metadata."""
        filename = media_path.stem.lower()

        # Get appropriate generator list
        if media_type == MediaType.IMAGE:
            generators = self.ai_generators["image"]
        elif media_type == MediaType.VIDEO:
            generators = self.ai_generators["video"]
        else:
            return "unknown"

        # Check filename patterns
        for generator in generators:
            if generator in filename:
                return generator

        # Check specific patterns using helper
        matched_source = match_ai_source_patterns(filename, generators)
        if matched_source:
            return matched_source

        # Try to read metadata for additional clues
        try:
            if media_type == MediaType.IMAGE:
                img = Image.open(media_path)
                metadata = img.info

                # Check for generator signatures in metadata
                for _, value in metadata.items():
                    value_str = str(value).lower()
                    for generator in generators:
                        if generator in value_str:
                            return generator
        except Exception as e:
            logger.debug(f"Unable to extract metadata from {media_path}: {e}")

        return "ai-generated"  # Generic fallback

    def _get_date_taken(self, media_path: Path, media_type: MediaType) -> str:
        """Extract date taken from media file."""
        _ = media_type  # Reserved for future metadata extraction
        # Try file modification time first
        try:
            mtime = media_path.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime(OUTPUT_DATE_FORMAT)
        except Exception:
            return datetime.now().strftime(OUTPUT_DATE_FORMAT)

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

                # Quality folders
                for stars in range(1, 6):
                    star_dir = project_dir / get_quality_folder_name(stars)
                    if star_dir.exists():
                        possible_locations.extend(
                            star_dir.glob(f"{project_folder}-*{source_path.suffix}")
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

    def _cleanup_duplicates(self) -> None:
        """Remove duplicate files from the organized folder."""
        logger.info("Checking for duplicates in organized folder...")

        # Track files by content hash
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

    def _run_pipeline_stages(self, media_path: Path, metadata: dict) -> dict:
        """Run pipeline stages on an image.

        Args:
            media_path: Path to the image
            metadata: Current metadata dictionary

        Returns:
            Updated metadata dictionary
        """
        for stage in self.pipeline_stages:
            try:
                # Check if we should run this stage
                min_stars = getattr(stage, "min_stars", 0)
                current_stars = metadata.get("quality_stars", 0)

                if current_stars >= min_stars:
                    # Check cost limit if applicable
                    stage_cost = getattr(stage, "cost", 0.0)
                    if (
                        self.pipeline_cost_limit
                        and self.pipeline_cost_total + stage_cost > self.pipeline_cost_limit
                    ):
                        logger.warning(f"Skipping {stage.stage_name} - would exceed cost limit")
                        continue

                    # Run the stage
                    logger.debug(f"Running {stage.stage_name} on {media_path.name}")
                    metadata = stage(media_path, metadata)

                    # Update cost tracking
                    self.pipeline_cost_total += stage_cost

            except Exception as e:
                logger.error(
                    f"Error in pipeline stage {getattr(stage, 'stage_name', 'unknown')}: {e}"
                )
                # Continue with next stage even if one fails

        return metadata

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

    def _parse_quality_thresholds(self, thresholds_config: dict) -> dict:
        """Parse quality thresholds from config format."""
        thresholds = {}
        for star_key, bounds in thresholds_config.items():
            stars = int(star_key.split("_")[0])
            thresholds[stars] = (bounds["min"], bounds["max"])
        return thresholds

    def _init_statistics(self) -> Statistics:
        """Initialize statistics tracking."""
        return Statistics(
            total=0,
            organized=0,
            already_organized=0,
            duplicates=0,
            errors=0,
            moved_existing=0,
            by_date=defaultdict(int),
            by_source=defaultdict(int),
            by_project=defaultdict(int),
            by_quality=defaultdict(int),
            quality_assessed=0,
            quality_skipped=0,
            images_found=0,
            videos_found=0,
            pipeline_results=defaultdict(int),
            pipeline_costs=defaultdict(float),
        )

    def _update_statistics(self, result: OrganizeResult) -> None:
        """Update statistics with organization result."""
        self.stats["total"] += 1

        if result["status"] == "success":
            self.stats["organized"] += 1
        elif result["status"] == "moved_existing":
            self.stats["moved_existing"] += 1
            self.stats["organized"] += 1  # Count as organized too
        elif result["status"] == "duplicate":
            self.stats["duplicates"] += 1
        elif result["status"] == "error":
            self.stats["errors"] += 1

        if result["date"]:
            self.stats["by_date"][result["date"]] += 1

        if result["source_type"]:
            self.stats["by_source"][result["source_type"]] += 1

        if result["project_folder"]:
            self.stats["by_project"][result["project_folder"]] += 1

        # Track media types
        if result.get("media_type") == MediaType.IMAGE:
            self.stats["images_found"] += 1
        elif result.get("media_type") == MediaType.VIDEO:
            self.stats["videos_found"] += 1

        if result["quality_stars"] is not None:
            self.stats["by_quality"][result["quality_stars"]] += 1
            self.stats["quality_assessed"] += 1
        elif self.quality_enabled and result.get("media_type") == MediaType.IMAGE:
            self.stats["quality_skipped"] += 1

    def _log_statistics(self) -> None:
        """Log organization statistics."""
        logger.info("\n" + "=" * 50)
        logger.info("Organization Summary:")
        logger.info(f"  Total files processed: {self.stats['total']}")
        logger.info(f"  Successfully organized: {self.stats['organized']}")
        if self.stats["moved_existing"] > 0:
            logger.info(f"    - Moved from existing: {self.stats['moved_existing']}")
            logger.info(
                f"    - Newly organized: {self.stats['organized'] - self.stats['moved_existing']}"
            )
        logger.info(f"  Duplicates skipped: {self.stats['duplicates']}")
        logger.info(f"  Errors: {self.stats['errors']}")

        if self.stats["images_found"] > 0 or self.stats["videos_found"] > 0:
            logger.info("\nMedia Types:")
            logger.info(f"  Images: {self.stats['images_found']}")
            logger.info(f"  Videos: {self.stats['videos_found']}")

        if self.stats["by_source"]:
            logger.info("\nBy AI Source:")
            for source, count in sorted(self.stats["by_source"].items()):
                logger.info(f"  {source}: {count}")

        if self.stats["by_project"]:
            logger.info("\nBy Project:")
            for project, count in sorted(self.stats["by_project"].items()):
                logger.info(f"  {project}: {count}")

        if self.quality_enabled and self.stats["quality_assessed"] > 0:
            logger.info("\nQuality Assessment:")
            logger.info(f"  Images assessed: {self.stats['quality_assessed']}")
            logger.info(f"  Files skipped: {self.stats['quality_skipped']}")
            if self.stats["by_quality"]:
                logger.info("  Distribution:")
                for stars in sorted(self.stats["by_quality"].keys(), reverse=True):
                    count = self.stats["by_quality"][stars]
                    pct = count / self.stats["quality_assessed"] * 100
                    logger.info(f"    {stars}-star: {count} ({pct:.1f}%)")

        logger.info("=" * 50)

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

            # If no file number in cache, assign one now
            if "file_number" not in analysis or analysis["file_number"] is None:
                analysis["file_number"] = self._get_next_file_number(
                    project_folder, analysis["source_type"]
                )
                # Update cache with the new file number
                self.metadata_cache.set_metadata(
                    media_path, analysis, cached_metadata.get("analysis_time", 0)
                )

            analysis_time = cached_metadata.get("analysis_time", 0)
            self.metadata_cache.update_stats(True, analysis_time)
        else:
            # Analyze file
            analysis = self._analyze_media(media_path, project_folder)
            analysis_time = time.time() - start_time

            # Cache the results
            self.metadata_cache.set_metadata(media_path, analysis, analysis_time)
            self.metadata_cache.update_stats(False)

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

        return OrganizeResult(
            source=str(media_path),
            project_folder=project_folder,
            status="success" if not self.config.processing.get("dry_run") else "dry_run",
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
