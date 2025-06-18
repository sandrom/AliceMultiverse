"""Media organizer implementation combining all mixins."""

import logging
from pathlib import Path
from typing import List, Optional

from ...core.performance_config import PerformanceConfig, get_performance_config
from ...monitoring.tracker import (
    PerformanceTracker,
    track_file_processing,
    track_operation,
    update_worker_metrics
)
from ..parallel_processor import ParallelBatchProcessor, ParallelProcessor
from .base import MediaOrganizerBase
from .file_operations import FileOperationsMixin
from .media_analysis import MediaAnalysisMixin
from .organization_logic import OrganizationLogicMixin
from .process_file import ProcessFileMixin
from .search_operations import SearchOperationsMixin
from .statistics import StatisticsMixin
from .watch_mode import WatchModeMixin

logger = logging.getLogger(__name__)


class MediaOrganizer(
    MediaOrganizerBase,
    FileOperationsMixin,
    MediaAnalysisMixin,
    OrganizationLogicMixin,
    ProcessFileMixin,
    SearchOperationsMixin,
    StatisticsMixin,
    WatchModeMixin,
):
    """Main class for organizing AI-generated media files.

    This class combines all the functionality from various mixins to provide
    a complete media organization solution. It handles:

    - Finding and analyzing media files
    - Detecting AI generation sources
    - Organizing files by date/project/source
    - Quality assessment and rating
    - Understanding (semantic tagging)
    - Search indexing with perceptual hashing
    - Duplicate detection and cleanup
    - Watch mode for continuous monitoring
    - Comprehensive statistics tracking
    """

    def __init__(self, config=None):
        """Initialize media organizer with optional performance configuration."""
        super().__init__(config)
        
        # Load performance configuration
        self.perf_config = get_performance_config()
        if hasattr(config, 'performance'):
            # Override with user settings
            self.perf_config = PerformanceConfig.from_dict(config.performance)
        
        # Initialize performance tracker
        self.tracker = PerformanceTracker()
        
        # Initialize parallel processors if enabled
        self.parallel_enabled = self.perf_config.max_workers > 1
        if self.parallel_enabled:
            self.parallel_processor = ParallelProcessor(self.perf_config.max_workers)
            self.batch_processor = ParallelBatchProcessor(
                batch_size=self.perf_config.batch_size,
                max_workers=self.perf_config.max_workers
            )
            logger.info(f"Parallel processing enabled with {self.perf_config.max_workers} workers")
            # Update worker metrics
            update_worker_metrics(0, self.perf_config.max_workers)
        
        # Check if storage supports batch operations
        self.batch_operations_enabled = (
            self.perf_config.enable_batch_operations and
            hasattr(self.search_db, 'batch_upsert_assets')
        )
        
    def organize(self, watch: bool = False) -> 'Statistics':
        """Organize media files with optional parallel processing."""
        if watch:
            return self._watch_and_organize()
        
        with track_operation("organize.total"):
            # Find all media files
            with track_operation("organize.find_files"):
                media_files = list(self._find_media_files())
            logger.info(f"Found {len(media_files)} media files to process")
            
            if not media_files:
                return self.stats
            
            # Use parallel processing for large collections
            if self.parallel_enabled and len(media_files) > self.perf_config.batch_size:
                logger.info("Using parallel processing for large collection")
                self._organize_parallel(media_files)
            else:
                # Fall back to sequential processing
                logger.info("Using sequential processing")
                self._organize_sequential(media_files)
            
            self._log_statistics()
            return self.stats
    
    def _organize_sequential(self, media_files: List[Path]) -> None:
        """Original sequential organization logic."""
        with track_operation("organize.sequential"):
            for media_path in media_files:
                with track_file_processing(media_path):
                    result = self._process_file(media_path)
                    self._update_statistics(result)
    
    def _organize_parallel(self, media_files: List[Path]) -> None:
        """Organize files using parallel processing."""
        with track_operation("organize.parallel"):
            if self.batch_operations_enabled:
                # Use batch database operations for best performance
                self._organize_with_batch_db(media_files)
            else:
                # Parallel file processing with individual DB operations
                self._organize_parallel_individual(media_files)
    
    def _organize_with_batch_db(self, media_files: List[Path]) -> None:
        """Organize with parallel processing and batch database operations."""
        def process_batch(file_batch: List[Path]) -> List[dict]:
            """Process a batch of files."""
            batch_assets = []
            
            # Use parallel metadata extraction within batch
            if self.perf_config.parallel_metadata_extraction:
                with track_operation("metadata.parallel_extraction"):
                    metadata_map = self.parallel_processor.extract_metadata_parallel(file_batch)
                for file_path, metadata in metadata_map.items():
                    try:
                        with track_file_processing(file_path):
                            result = self._process_file_with_metadata(file_path, metadata)
                            if result:
                                batch_assets.append(result)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        self.stats["errors"] += 1
                        self.tracker.collector.record_error()
            else:
                # Sequential processing within batch
                for file_path in file_batch:
                    try:
                        with track_file_processing(file_path):
                            result = self._process_file_for_batch(file_path)
                            if result:
                                batch_assets.append(result)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        self.stats["errors"] += 1
                        self.tracker.collector.record_error()
            
            return batch_assets
        
        # Process in batches
        all_assets = self.batch_processor.process_in_batches(
            media_files,
            process_batch,
            combine_func=lambda results: [item for batch in results for item in batch]
        )
        
        # Batch insert into database
        if all_assets:
            try:
                inserted = self.search_db.batch_upsert_assets(all_assets)
                logger.info(f"Batch inserted {inserted} assets into database")
            except Exception as e:
                logger.error(f"Batch database insert failed: {e}")
    
    def _organize_parallel_individual(self, media_files: List[Path]) -> None:
        """Parallel processing with individual database operations."""
        results = self.parallel_processor.process_files_parallel(
            media_files,
            self._process_file,
            batch_size=self.perf_config.batch_size
        )
        
        # Update statistics
        for _, result in results:
            if result:
                self._update_statistics(result)
    
    def _process_file_for_batch(self, media_path: Path) -> Optional[dict]:
        """Process file and return asset data for batch insert."""
        # Get the normal result
        result = self._process_file(media_path)
        
        if result["status"] == "success":
            # Convert to asset data format
            return self._result_to_asset_data(media_path, result)
        return None
    
    def _process_file_with_metadata(self, media_path: Path, metadata: dict) -> Optional[dict]:
        """Process file with pre-extracted metadata."""
        # This would be an optimized version that uses the metadata
        # For now, fall back to regular processing
        return self._process_file_for_batch(media_path)
    
    def _result_to_asset_data(self, media_path: Path, result: dict) -> dict:
        """Convert organize result to asset data for database."""
        # Extract data from result and format for database
        analysis = result.get("analysis", {})
        
        return {
            "content_hash": analysis.get("content_hash", ""),
            "file_path": result.get("destination", ""),
            "file_name": media_path.name,
            "file_size": media_path.stat().st_size,
            "media_type": analysis.get("media_type", "image"),
            "source_type": result.get("source_type", "unknown"),
            "date_taken": result.get("date_taken"),
            "project": result.get("project_folder", ""),
            "metadata": analysis,
        }
