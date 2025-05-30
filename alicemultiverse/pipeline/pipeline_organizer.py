"""Pipeline-based media organizer with multi-stage quality assessment."""

import logging
import time
from pathlib import Path

from omegaconf import DictConfig

from ..core.types import MediaType, OrganizeResult
from ..core.keys import APIKeyManager
from ..organizer.media_organizer import MediaOrganizer
from .stages import BRISQUEStage, ClaudeStage, PipelineStage, SightEngineStage

logger = logging.getLogger(__name__)


class PipelineOrganizer(MediaOrganizer):
    """Extended organizer with pipeline-based quality assessment."""

    def __init__(self, config: DictConfig) -> None:
        """Initialize pipeline organizer.

        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.pipeline_stages: list[PipelineStage] = []
        self.pipeline_config = config.pipeline
        self.total_cost = 0.0
        self.cost_limit = config.pipeline.cost_limits.get("total", float("inf"))

        # Initialize pipeline stages based on mode
        if config.pipeline.mode:
            self._initialize_pipeline(config.pipeline.mode)

    def _initialize_pipeline(self, mode: str) -> None:
        """Initialize pipeline stages based on mode.

        Args:
            mode: Pipeline mode (basic, standard, premium, custom)
        """
        stages_map = {
            # Single stage pipelines
            "basic": ["brisque"],
            "brisque": ["brisque"],
            # Two stage pipelines
            "standard": ["brisque", "sightengine"],
            "brisque-sightengine": ["brisque", "sightengine"],
            "brisque-claude": ["brisque", "claude"],
            # Three stage pipeline
            "premium": ["brisque", "sightengine", "claude"],
            "full": ["brisque", "sightengine", "claude"],
            "brisque-sightengine-claude": ["brisque", "sightengine", "claude"],
            # Custom
            "custom": self.pipeline_config.get("stages", []),
        }

        stage_names = stages_map.get(mode, [])

        for stage_name in stage_names:
            stage = self._create_stage(stage_name)
            if stage:
                self.pipeline_stages.append(stage)
                logger.info(f"Initialized pipeline stage: {stage_name}")
            else:
                logger.warning(f"Failed to initialize stage: {stage_name}")

    def _create_stage(self, stage_name: str) -> PipelineStage | None:
        """Create a pipeline stage by name.

        Args:
            stage_name: Name of the stage to create

        Returns:
            Pipeline stage instance or None if creation failed
        """
        if stage_name == "brisque":
            thresholds = self._parse_quality_thresholds(self.config.quality.thresholds)
            return BRISQUEStage(thresholds)

        elif stage_name == "sightengine":
            # Get API keys
            key_manager = APIKeyManager()

            # Try pipeline-specific key first, then fall back to general key
            api_user = None
            api_secret = None

            if hasattr(self, "sightengine_key") and self.sightengine_key:
                if "," in self.sightengine_key:
                    api_user, api_secret = self.sightengine_key.split(",", 1)

            if not api_user or not api_secret:
                # Try both naming conventions
                api_user = key_manager.get_api_key("sightengine_api_user")
                api_secret = key_manager.get_api_key("sightengine_api_secret")

                if not api_user:
                    api_user = key_manager.get_api_key("sightengine_user")
                if not api_secret:
                    api_secret = key_manager.get_api_key("sightengine_secret")

            if not api_user or not api_secret:
                logger.error(
                    "SightEngine API credentials not found. Use 'alice keys setup' to configure."
                )
                return None

            min_stars = self.pipeline_config.thresholds.get("brisque_min_stars", 3)

            # Get scoring weights and thresholds
            weights = self.pipeline_config.scoring_weights.get("standard", {})
            star_thresholds = self.pipeline_config.get("star_thresholds", {})

            return SightEngineStage(api_user, api_secret, min_stars, weights, star_thresholds)

        elif stage_name == "claude":
            # Get API key
            key_manager = APIKeyManager()

            # Try pipeline-specific key first, then fall back to general key
            api_key = getattr(self, "claude_key", None)

            if not api_key:
                api_key = key_manager.get_api_key("anthropic_api_key")

            if not api_key:
                logger.error("Anthropic API key not found. Use 'alice keys setup' to configure.")
                return None

            min_stars = self.pipeline_config.thresholds.get("sightengine_min_stars", 4)

            # Get scoring weights and thresholds
            weights = self.pipeline_config.scoring_weights.get("premium", {})
            star_thresholds = self.pipeline_config.get("star_thresholds", {})

            return ClaudeStage(
                api_key, min_stars, "claude-3-haiku-20240307", weights, star_thresholds
            )

        else:
            logger.error(f"Unknown pipeline stage: {stage_name}")
            return None

    def _analyze_media(self, media_path: Path, project_folder: str) -> dict:
        """Analyze media file with pipeline stages.

        Args:
            media_path: Path to media file
            project_folder: Project folder name

        Returns:
            Analysis results
        """
        # Get base analysis from parent class
        analysis = super()._analyze_media(media_path, project_folder)

        # Skip pipeline for non-images
        if analysis.get("media_type") != MediaType.IMAGE:
            return analysis

        # Check cost limit
        if self.total_cost >= self.cost_limit:
            logger.warning(f"Cost limit reached (${self.total_cost:.2f}), skipping pipeline")
            return analysis

        # Process through pipeline stages
        metadata = dict(analysis)

        for stage in self.pipeline_stages:
            if stage.should_process(metadata):
                # Check stage cost
                stage_cost = stage.get_cost()
                if self.total_cost + stage_cost > self.cost_limit:
                    logger.warning(f"Skipping {stage.name()} - would exceed cost limit")
                    break

                # Process through stage
                logger.debug(f"Processing {media_path.name} through {stage.name()}")
                metadata = stage.process(media_path, metadata)
                self.total_cost += stage_cost

                # Check if stage failed (dict structure now)
                stage_results = metadata.get("pipeline_stages", {})
                stage_result = stage_results.get(stage.name(), {})
                if stage_result and not stage_result.get("passed", True):
                    logger.debug(f"{media_path.name} failed {stage.name()}, stopping pipeline")
                    break

        # Update analysis with pipeline results
        analysis.update(metadata)

        return analysis

    def _build_destination_path(
        self,
        source_path: Path,
        date_taken: str,
        project_folder: str,
        source_type: str,
        file_number: int,
        quality_stars: int | None = None,
    ) -> Path:
        """Build destination path including pipeline result subfolder.

        Args:
            source_path: Source file path
            date_taken: Date taken string
            project_folder: Project folder name
            source_type: AI source type
            file_number: Unique file number
            quality_stars: Quality rating (1-5)

        Returns:
            Destination path
        """
        # Get base path from parent
        dest_path = super()._build_destination_path(
            source_path, date_taken, project_folder, source_type, file_number, quality_stars
        )

        return dest_path

    def _process_file(self, media_path: Path) -> OrganizeResult:
        """Process a single media file through the pipeline.

        This method is called by the parent class and handles the entire
        file processing including pipeline stages.
        """
        try:
            # Get project folder (same logic as parent)
            relative_path = media_path.relative_to(self.source_dir)
            path_parts = relative_path.parts

            if len(path_parts) > 1:
                project_folder = path_parts[0]
            else:
                project_folder = "uncategorized"

            # Check cache first
            start_time = time.time()
            cached_metadata = self.metadata_cache.get_metadata(media_path)

            if cached_metadata and not self.config.processing.get("force_reindex", False):
                # Use cached analysis but update project folder
                analysis = cached_metadata["analysis"]
                analysis["project_folder"] = project_folder

                # If no file number in cache, assign one now
                if "file_number" not in analysis or analysis["file_number"] is None:
                    analysis["file_number"] = self._get_next_file_number(
                        project_folder, analysis["source_type"]
                    )
                    self.metadata_cache.set_metadata(
                        media_path, analysis, cached_metadata.get("analysis_time", 0)
                    )

                # Check if any pipeline stages need to be run
                if (
                    analysis.get("media_type") == MediaType.IMAGE
                    and analysis.get("quality_stars") is not None
                ):
                    # Process through pipeline stages
                    metadata = dict(analysis)
                    updated = False

                    for stage in self.pipeline_stages:
                        # Check if this stage has already been processed
                        existing_stages = metadata.get("pipeline_stages", {})
                        if stage.name() in existing_stages:
                            logger.debug(
                                f"Skipping {stage.name()} for {media_path.name} - already processed"
                            )
                            continue

                        if stage.should_process(metadata):
                            # Check stage cost
                            stage_cost = stage.get_cost()
                            if self.total_cost + stage_cost > self.cost_limit:
                                logger.warning(f"Skipping {stage.name()} - would exceed cost limit")
                                break

                            # Process through stage
                            logger.debug(f"Processing {media_path.name} through {stage.name()}")
                            metadata = stage.process(media_path, metadata)
                            self.total_cost += stage_cost
                            updated = True

                            # Check if stage failed (dict structure now)
                            stage_results = metadata.get("pipeline_stages", {})
                            stage_result = stage_results.get(stage.name(), {})
                            if stage_result and not stage_result.get("passed", True):
                                logger.debug(
                                    f"{media_path.name} failed {stage.name()}, stopping pipeline"
                                )
                                break

                    # Only update cache if something changed
                    if updated:
                        # Update analysis with pipeline results
                        analysis.update(metadata)

                        # Update cache with pipeline results
                        self.metadata_cache.set_metadata(
                            media_path, analysis, cached_metadata.get("analysis_time", 0)
                        )

                analysis_time = cached_metadata.get("analysis_time", 0)
                self.metadata_cache.update_stats(True, analysis_time)
            else:
                # Analyze file with pipeline
                analysis = self._analyze_media(media_path, project_folder)
                analysis_time = time.time() - start_time

                # Cache the results
                self.metadata_cache.set_metadata(media_path, analysis, analysis_time)
                self.metadata_cache.update_stats(False)

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

            # No subfolders needed since we're just refining ratings

            # Continue with parent's file processing logic
            # (This duplicates some parent code but avoids complex inheritance issues)

            # Check for existing files
            existing_file = self._find_existing_organized_file(
                media_path, analysis["date_taken"], project_folder, analysis["source_type"]
            )

            # Check if destination already exists
            if dest_path.exists():
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

            # Clean up existing file if it's in a different location
            if existing_file and existing_file != dest_path:
                logger.debug(f"Moving existing file from {existing_file} to {dest_path}")
                if not self.config.processing.dry_run:
                    # If there's already a file at dest_path, remove the existing file instead
                    if dest_path.exists() and self.file_handler.files_are_identical(
                        existing_file, dest_path
                    ):
                        logger.debug(
                            f"Destination already exists, removing duplicate: {existing_file}"
                        )
                        existing_file.unlink()
                    else:
                        self.file_handler.move_file(existing_file, dest_path)

                    # Skip the copy/move below since we already handled it
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

            # Copy or move file
            if self.config.processing.copy_mode:
                self.file_handler.copy_file(media_path, dest_path)
            else:
                self.file_handler.move_file(media_path, dest_path)

            # Log pipeline costs periodically
            if self.stats["total"] % 100 == 0 and self.total_cost > 0:
                logger.info(f"Pipeline costs so far: ${self.total_cost:.2f}")

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

    def _log_statistics(self) -> None:
        """Log organization statistics including pipeline costs."""
        super()._log_statistics()

        if self.total_cost > 0:
            logger.info("\nPipeline Costs:")
            logger.info(f"  Total: ${self.total_cost:.2f}")

            # TODO: Add detailed stage cost breakdown in future
