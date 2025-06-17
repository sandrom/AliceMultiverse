"""Base class for media organizer components."""

from pathlib import Path

from omegaconf import DictConfig

from ...core.file_operations import FileHandler
from ...core.logging import get_logger
from ...core.types import Statistics
from ...core.unified_cache import UnifiedCache as MetadataCache

logger = get_logger(__name__)


class MediaOrganizerBase:
    """Base class with common functionality for media organizer."""

    def __init__(self, config: DictConfig):
        """Initialize the media organizer base.
        
        Args:
            config: Configuration object
        """
        self._project_counters = {}  # Track next number for each project
        self.config = config
        self.source_dir = Path(config.paths.inbox)
        self.output_dir = Path(config.paths.organized)

        # Initialize components
        self.file_handler = FileHandler(dry_run=getattr(config.processing, "dry_run", False))

        # Initialize DuckDB search for auto-indexing
        self.search_db = None
        if getattr(config.processing, "understanding", False):
            try:
                from ...storage.unified_duckdb import DuckDBSearch
                db_path = None
                if hasattr(config, 'storage') and hasattr(config.storage, 'search_db'):
                    db_path = config.storage.search_db
                self.search_db = DuckDBSearch(db_path)
                logger.info("Auto-indexing to DuckDB enabled during organization")
            except Exception as e:
                logger.warning(f"Failed to initialize DuckDB for auto-indexing: {e}")

        # Check if understanding is enabled
        enable_understanding = getattr(config.processing, "understanding", False)
        understanding_provider = None

        # Understanding config is in pipeline.extra_fields
        if enable_understanding and hasattr(config, "pipeline"):
            if hasattr(config.pipeline, "extra_fields") and "understanding" in config.pipeline.extra_fields:
                understanding_config = config.pipeline.extra_fields["understanding"]
                understanding_provider = understanding_config.get("preferred_provider")

            # If no preferred provider, use anthropic since we have the key
            if understanding_provider is None:
                understanding_provider = "anthropic"
                logger.info("Using anthropic provider for understanding (API key configured)")

        self.metadata_cache = MetadataCache(
            self.source_dir,
            force_reindex=config.processing.force_reindex,
            enable_understanding=enable_understanding,
            understanding_provider=understanding_provider
        )

        # Quality assessment has been replaced with image understanding
        self.quality_enabled = False

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

    def _init_statistics(self) -> Statistics:
        """Initialize statistics tracking.
        
        Returns:
            Initialized statistics object
        """
        return Statistics(
            processed=0,
            organized=0,
            skipped=0,
            errors=0,
            by_source={},
            by_quality={},
            total_size_mb=0.0,
            processing_time=0.0,
            understanding_cost=0.0,
        )

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle interrupt signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info("Received interrupt signal, stopping watch mode...")
        self.stop_watching = True
