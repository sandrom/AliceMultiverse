"""Cache migration utilities for transitioning to unified cache.

This module provides backward-compatible imports and migration utilities
to help transition from the old multi-cache system to the unified cache.
"""

import logging
from pathlib import Path
from typing import Any

from .unified_cache import UnifiedCache

logger = logging.getLogger(__name__)


class MetadataCacheAdapter:
    """Adapter that makes UnifiedCache look like the old MetadataCache.

    This allows existing code to continue working while we migrate.
    """

    def __init__(self, source_root: Path, force_reindex: bool = False, 
                 enable_understanding: bool = False, understanding_provider: str | None = None):
        """Initialize adapter with UnifiedCache.
        
        Args:
            source_root: Root directory for source files
            force_reindex: Whether to bypass cache
            enable_understanding: Whether to enable AI understanding
            understanding_provider: Specific provider for understanding
        """
        self._unified = UnifiedCache(
            source_root=source_root, 
            force_reindex=force_reindex,
            enable_understanding=enable_understanding,
            understanding_provider=understanding_provider
        )

        # Expose same attributes as old MetadataCache
        self.source_root = source_root
        self.force_reindex = force_reindex
        self.cache_hits = 0
        self.cache_misses = 0
        self.analysis_time_saved = 0.0
        
        # Expose understanding settings
        self.enable_understanding = enable_understanding
        self.understanding_provider = understanding_provider

    def get_content_hash(self, file_path: Path) -> str:
        """Get content hash (delegates to unified cache)."""
        return self._unified.cache.get_content_hash(file_path)

    def load(self, media_path: Path) -> dict[str, Any] | None:
        """Load metadata (delegates to unified cache)."""
        result = self._unified.load(media_path)

        # Update statistics
        if result is not None:
            self.cache_hits += 1
            self._unified.cache.cache_hits += 1
        else:
            self.cache_misses += 1
            self._unified.cache.cache_misses += 1

        return result

    def save(self, media_path: Path, analysis: Any, analysis_time: float) -> None:
        """Save metadata (delegates to unified cache)."""
        # The first save is technically after a cache miss
        # Check if metadata already exists
        existing = self._unified.cache.load(media_path)
        if existing is None:
            self.cache_misses += 1
            self._unified.cache.cache_misses += 1

        self._unified.save(media_path, analysis, analysis_time)
        self.analysis_time_saved += analysis_time
        self._unified.cache.analysis_time_saved += analysis_time

    def get_metadata(self, media_path: Path) -> dict[str, Any] | None:
        """Alias for load (backward compatibility)."""
        return self.load(media_path)

    def set_metadata(self, media_path: Path, analysis: Any, analysis_time: float) -> None:
        """Alias for save (backward compatibility)."""
        self.save(media_path, analysis, analysis_time)

    def has_metadata(self, media_path: Path) -> bool:
        """Check if metadata exists."""
        return self._unified.cache.has_metadata(media_path)

    def update_stats(self, from_cache: bool, time_saved: float = 0) -> None:
        """Update cache hit/miss statistics.

        Args:
            from_cache: Whether the data was loaded from cache
            time_saved: Time saved by using cache (seconds)
        """
        if from_cache:
            self.cache_hits += 1
            self.analysis_time_saved += time_saved
            self._unified.cache.cache_hits += 1
            self._unified.cache.analysis_time_saved += time_saved
        else:
            self.cache_misses += 1
            self._unified.cache.cache_misses += 1

    def get_stats(self) -> dict[str, Any]:
        """Get statistics."""
        # Sync our stats with unified cache
        self.cache_hits = self._unified.cache.cache_hits
        self.cache_misses = self._unified.cache.cache_misses
        self.analysis_time_saved = self._unified.cache.analysis_time_saved

        return self._unified.get_stats()


class EnhancedMetadataCacheAdapter(MetadataCacheAdapter):
    """Adapter that makes UnifiedCache look like the old EnhancedMetadataCache."""

    def __init__(self, source_root: Path, project_id: str, force_reindex: bool = False,
                 enable_understanding: bool = False, understanding_provider: str | None = None):
        """Initialize adapter with project support.
        
        Args:
            source_root: Root directory for source files
            project_id: Project identifier
            force_reindex: Whether to bypass cache
            enable_understanding: Whether to enable AI understanding
            understanding_provider: Specific provider for understanding
        """
        self._unified = UnifiedCache(
            source_root=source_root, 
            project_id=project_id, 
            force_reindex=force_reindex,
            enable_understanding=enable_understanding,
            understanding_provider=understanding_provider
        )
        self.source_root = source_root
        self.project_id = project_id
        self.force_reindex = force_reindex

        # Enhanced cache specific attributes
        self.metadata_index = self._unified.metadata_index
        self.extractor = self._unified.extractor

    def load_enhanced(self, media_path: Path) -> Any | None:
        """Load enhanced metadata."""
        return self._unified.load_enhanced(media_path)

    def save_enhanced(
        self,
        media_path: Path,
        analysis: Any,
        analysis_time: float,
        enhanced_metadata: Any | None = None,
    ) -> None:
        """Save enhanced metadata."""
        self._unified.save_enhanced(media_path, analysis, analysis_time, enhanced_metadata)

    def get_all_metadata(self) -> dict[str, Any]:
        """Get all metadata from index."""
        return self._unified.metadata_index

    def search_by_tags(self, tags: list, tag_type: str | None = None) -> list:
        """Search by tags."""
        return self._unified.search_by_tags(tags, tag_type)

    def search_by_quality(self, min_stars: int = 1, max_stars: int = 5) -> list:
        """Search by quality rating."""
        return self._unified.search_by_quality(min_stars, max_stars)


class PersistentMetadataManagerAdapter:
    """Adapter that makes UnifiedCache look like the old PersistentMetadataManager."""

    def __init__(
        self,
        cache_dir: Path,
        quality_thresholds: dict[str, float] | None = None,
        project_id: str = "default",
    ):
        """Initialize adapter."""
        self._unified = UnifiedCache(
            source_root=cache_dir, project_id=project_id, quality_thresholds=quality_thresholds
        )

        # Expose same interface
        self.embedder = self._unified.embedder
        self.cache = EnhancedMetadataCacheAdapter(source_root=cache_dir, project_id=project_id)

    def load_metadata(self, image_path: Path) -> tuple:
        """Load metadata from image or cache."""
        metadata = self._unified.load(image_path)
        from_cache = metadata is not None
        return metadata or {}, from_cache

    def save_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """Save metadata to image and cache."""
        # Create a dummy analysis result
        analysis = metadata.get("analysis", metadata)
        analysis_time = metadata.get("analysis_time", 0.0)

        self._unified.save(image_path, analysis, analysis_time)
        return True

    def rebuild_cache_from_images(self, image_dir: Path) -> int:
        """Rebuild cache from embedded metadata."""
        return self._unified.rebuild_from_images(image_dir)


def migrate_to_unified_cache():
    """Migration script to help transition existing code.

    This can be run to update imports throughout the codebase.
    """
    logger.info("Starting cache migration to unified cache...")

    # This would contain logic to update imports, but for now
    # we're using adapters for backward compatibility

    replacements = [
        (
            "from ..core.metadata_cache import MetadataCache",
            "from ..core.cache_migration import MetadataCacheAdapter as MetadataCache",
        ),
        (
            "from ..metadata.enhanced_cache import EnhancedMetadataCache",
            "from ..core.cache_migration import EnhancedMetadataCacheAdapter as EnhancedMetadataCache",
        ),
        (
            "from ..metadata.persistent_metadata import PersistentMetadataManager",
            "from ..core.cache_migration import PersistentMetadataManagerAdapter as PersistentMetadataManager",
        ),
    ]

    logger.info("Cache migration adapters are in place. Update imports gradually.")
    return replacements
