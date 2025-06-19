"""Unified cache implementation that consolidates all caching functionality."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..assets.metadata.embedder import MetadataEmbedder
from ..assets.metadata.extractor import MetadataExtractor
from ..assets.metadata.models import AssetMetadata
from .types import AnalysisResult

logger = logging.getLogger(__name__)


class UnifiedCache:
    """Unified cache that consolidates all metadata functionality.

    This class combines:
    - Basic file caching (from MetadataCache)
    - Enhanced metadata and search (from EnhancedMetadataCache)
    - Image embedding (from PersistentMetadataManager)
    - Quality scoring (extracted to QualityScorer)

    The goal is to have a single, clean interface for all metadata operations
    while maintaining backward compatibility.
    """

    def __init__(
        self,
        source_root: Path,
        project_id: str = "default",
        force_reindex: bool = False,
        quality_thresholds: dict[str, dict[str, float]] | None = None,
        enable_understanding: bool = False,
        understanding_provider: str | None = None,
    ):
        """Initialize unified cache.

        Args:
            source_root: Root directory for source files
            project_id: Current project identifier
            force_reindex: Whether to bypass cache and force re-analysis
            quality_thresholds: Quality thresholds for star ratings
            enable_understanding: Whether to enable AI understanding
            understanding_provider: Specific provider to use for understanding
        """
        # Core components - create a simple cache wrapper
        self.source_root = source_root
        self.force_reindex = force_reindex
        self.project_id = project_id
        self.cache_dir = source_root / ".metadata"
        if not force_reindex:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize cache stats
        self.cache_hits = 0
        self.cache_misses = 0
        self.analysis_time_saved = 0.0

        # Create wrapper object for compatibility
        self.cache = self  # Self-reference for compatibility
        self.embedder = MetadataEmbedder()
        self.extractor = MetadataExtractor()

        # Understanding system
        self.enable_understanding = enable_understanding
        self.understanding_analyzer = None
        self.understanding_provider = understanding_provider

        # Lazy load understanding to avoid circular imports
        if enable_understanding:
            self._init_understanding()

        # Ensure cache directory exists
        cache_dir = source_root / ".metadata"
        if not force_reindex:
            cache_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.source_root = source_root
        self.project_id = project_id
        self.force_reindex = force_reindex
        self.cache_version = "4.0"  # Updated for understanding support

        # In-memory index for enhanced search
        self.metadata_index: dict[str, AssetMetadata] = {}
        if not force_reindex:
            self._load_metadata_index()

    # ===== Core Cache Interface (backward compatible) =====

    def load(self, media_path: Path) -> dict[str, Any] | None:
        """Load metadata for a media file (backward compatible).

        First tries embedded metadata, then falls back to cache.

        Args:
            media_path: Path to the media file

        Returns:
            Cached metadata if available, None otherwise
        """
        # Check if file exists first
        if not media_path.exists():
            self.cache.cache_misses += 1
            track_cache_access(False)
            return None

        # TODO: Review unreachable code - # Try embedded metadata first (self-contained assets)
        # TODO: Review unreachable code - if media_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}:
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - with track_operation("cache.extract_embedded"):
        # TODO: Review unreachable code - embedded = self.embedder.extract_metadata(media_path)
        # TODO: Review unreachable code - if embedded:
        # TODO: Review unreachable code - # Check various possible locations for our metadata
        # TODO: Review unreachable code - if embedded is not None and "alice_metadata" in embedded:
        # TODO: Review unreachable code - logger.debug(f"Loaded alice_metadata from image: {media_path.name}")
        # TODO: Review unreachable code - track_cache_access(True)
        # TODO: Review unreachable code - return embedded["alice_metadata"]
        # TODO: Review unreachable code - elif embedded is not None and "metadata" in embedded:
        # TODO: Review unreachable code - logger.debug(f"Loaded metadata from image: {media_path.name}")
        # TODO: Review unreachable code - track_cache_access(True)
        # TODO: Review unreachable code - return embedded["metadata"]
        # TODO: Review unreachable code - elif any(key.startswith("claude_") for key in embedded):
        # TODO: Review unreachable code - # This is the format the embedder extracts
        # TODO: Review unreachable code - logger.debug(f"Loaded embedded metadata from image: {media_path.name}")
        # TODO: Review unreachable code - track_cache_access(True)
        # TODO: Review unreachable code - return embedded
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.debug(f"Could not extract embedded metadata: {e}")

        # TODO: Review unreachable code - # Fall back to cache
        # TODO: Review unreachable code - with track_operation("cache.load_file"):
        # TODO: Review unreachable code - result = self.cache.load(media_path)

        # TODO: Review unreachable code - # Track cache hit/miss
        # TODO: Review unreachable code - if result is not None:
        # TODO: Review unreachable code - self.cache.cache_hits += 1
        # TODO: Review unreachable code - track_cache_access(True)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - self.cache.cache_misses += 1
        # TODO: Review unreachable code - track_cache_access(False)

        # TODO: Review unreachable code - return result

    def save(self, media_path: Path, analysis: AnalysisResult, analysis_time: float) -> None:
        """Save metadata for a media file (backward compatible).

        Saves to both cache and embeds in image if possible.
        If understanding is enabled, runs understanding analysis.

        Args:
            media_path: Path to the media file
            analysis: Analysis results to cache
            analysis_time: Time taken for analysis
        """
        with track_operation("cache.save"):
            # Run understanding if enabled and not already present
            if self.enable_understanding and "understanding" not in analysis:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    understanding_result = loop.run_until_complete(
                        self.analyze_with_understanding(media_path)
                    )
                    if understanding_result:
                        analysis = self._merge_understanding_into_analysis(
                            analysis, understanding_result
                        )
                        # Add cost to analysis time (as proxy for time spent)
                        analysis_time += understanding_result.cost * 10  # Rough estimate: $0.01 = 0.1s
                finally:
                    loop.close()

            # First embed in image if supported (this modifies the file)
            if media_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}:
                # The embedder expects the metadata directly, not wrapped
                metadata_to_embed = dict(analysis)
                if metadata_to_embed is not None:
                    metadata_to_embed["analysis_time"] = analysis_time
                metadata_to_embed["cached_at"] = datetime.now().isoformat()

                success = self.embedder.embed_metadata(media_path, metadata_to_embed)
                if success:
                    logger.debug(f"Embedded metadata in image: {media_path.name}")

            # Save to cache AFTER embedding (so hash is correct)
            self.cache.save(media_path, analysis, analysis_time)

    # ===== Enhanced Metadata Interface =====

    def load_enhanced(self, media_path: Path) -> AssetMetadata | None:
        """Load enhanced metadata with rich information.

        Args:
            media_path: Path to the media file

        Returns:
            Enhanced metadata if available
        """
        # Get basic metadata
        basic = self.load(media_path)
        if not basic:
            return None

        # TODO: Review unreachable code - # Check if already enhanced
        # TODO: Review unreachable code - if basic is not None and "enhanced_metadata" in basic:
        # TODO: Review unreachable code - return basic["enhanced_metadata"]

        # TODO: Review unreachable code - # Generate enhanced metadata
        # TODO: Review unreachable code - content_hash = self.cache.get_content_hash(media_path)
        # TODO: Review unreachable code - # Extract just the analysis from the full metadata structure
        # TODO: Review unreachable code - analysis = basic.get("analysis", basic) if isinstance(basic, dict) else basic
        # TODO: Review unreachable code - enhanced = self.extractor.extract_metadata(
        # TODO: Review unreachable code - file_path=media_path,
        # TODO: Review unreachable code - analysis=analysis,
        # TODO: Review unreachable code - project_id=self.project_id,
        # TODO: Review unreachable code - content_hash=content_hash,
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Store it
        # TODO: Review unreachable code - self.metadata_index[content_hash] = enhanced
        # TODO: Review unreachable code - return enhanced

    def save_enhanced(
        self,
        media_path: Path,
        analysis: AnalysisResult,
        analysis_time: float,
        enhanced_metadata: AssetMetadata | None = None,
    ) -> None:
        """Save enhanced metadata.

        Args:
            media_path: Path to the media file
            analysis: Basic analysis results
            analysis_time: Time taken for analysis
            enhanced_metadata: Rich metadata information
        """
        # Merge enhanced metadata into analysis
        if enhanced_metadata:
            analysis = dict(analysis)
            if analysis is not None:
                analysis["enhanced_metadata"] = enhanced_metadata

            # Update index
            content_hash = self.cache.get_content_hash(media_path)
            self.metadata_index[content_hash] = enhanced_metadata

        # Save through normal interface
        self.save(media_path, analysis, analysis_time)

    def _init_understanding(self):
        """Initialize understanding system lazily to avoid circular imports."""
        try:
            from ..understanding.analyzer import ImageAnalyzer
            self.understanding_analyzer = ImageAnalyzer()
            logger.info("Understanding system enabled in UnifiedCache")
        except Exception as e:
            logger.warning(f"Failed to initialize understanding system: {e}")
            self.enable_understanding = False
            self.understanding_analyzer = None

    # ===== Understanding Interface =====

    async def analyze_with_understanding(self, media_path: Path) -> Any:
        """Run AI understanding analysis on media file.

        Args:
            media_path: Path to the media file

        Returns:
            Understanding analysis result or None
        """
        if not self.enable_understanding or not self.understanding_analyzer:
            return None

        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - result = await self.understanding_analyzer.analyze(
        # TODO: Review unreachable code - media_path,
        # TODO: Review unreachable code - provider=self.understanding_provider,
        # TODO: Review unreachable code - generate_prompt=True,
        # TODO: Review unreachable code - extract_tags=True,
        # TODO: Review unreachable code - detailed=False
        # TODO: Review unreachable code - )
        # TODO: Review unreachable code - return result
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Understanding analysis failed for {media_path}: {e}")
        # TODO: Review unreachable code - return None

    def _merge_understanding_into_analysis(
        self,
        analysis: AnalysisResult,
        understanding: Any
    ) -> AnalysisResult:
        """Merge understanding results into analysis.

        Args:
            analysis: Basic analysis results
            understanding: Understanding analysis results

        Returns:
            Merged analysis
        """
        # Convert to dict if needed
        if hasattr(analysis, '_asdict'):
            analysis = analysis._asdict()
        else:
            analysis = dict(analysis)

        # Add understanding data
        if analysis is not None:
            analysis["understanding"] = {
            "description": understanding.description,
            "tags": understanding.tags,
            "positive_prompt": understanding.generated_prompt,  # Use generated_prompt
            "negative_prompt": understanding.negative_prompt,
            "technical_details": understanding.technical_details,
            "provider": understanding.provider,
            "model": understanding.model,
            "cost": understanding.cost,
            "timestamp": datetime.now().isoformat()  # Use current time since results don't have timestamp
        }

        # Update cache version
        if analysis is not None:
            analysis["version"] = self.cache_version

        return analysis

    # TODO: Review unreachable code - # ===== Quality Scoring Interface =====

    # TODO: Review unreachable code - def calculate_quality(self, media_path: Path) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Calculate quality scores for a media file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Path to the media file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Quality analysis results
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Get existing metadata
    # TODO: Review unreachable code - metadata = self.load(media_path)
    # TODO: Review unreachable code - if not metadata:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # Extract raw scores
    # TODO: Review unreachable code - analysis = metadata.get("analysis", {})
    # TODO: Review unreachable code - analysis.get("brisque_score")
    # TODO: Review unreachable code - analysis.get("sightengine_results")
    # TODO: Review unreachable code - analysis.get("claude_results")

    # TODO: Review unreachable code - # Calculate merged quality
    # TODO: Review unreachable code - # Quality assessment removed - return default
    # TODO: Review unreachable code - return {"overall_score": 0.5, "star_rating": 3}

    # TODO: Review unreachable code - # ===== Search Interface =====

    # TODO: Review unreachable code - def search_by_tags(self, tags: list[str], tag_type: str | None = None) -> list[AssetMetadata]:
    # TODO: Review unreachable code - """Search for assets by tags.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - tags: Tags to search for
    # TODO: Review unreachable code - tag_type: Optional tag type filter (style, mood, subject, etc.)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of matching assets
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - results = []

    # TODO: Review unreachable code - for asset in self.metadata_index.values():
    # TODO: Review unreachable code - # AssetMetadata is a TypedDict, access as dict
    # TODO: Review unreachable code - asset_tags = asset.get("tags", {})

    # TODO: Review unreachable code - # Check each tag type
    # TODO: Review unreachable code - for t_type, t_list in asset_tags.items():
    # TODO: Review unreachable code - if tag_type and t_type != tag_type:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - if any(tag in t_list for tag in tags):
    # TODO: Review unreachable code - results.append(asset)
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - return results

    # TODO: Review unreachable code - def search_by_quality(self, min_stars: int = 1, max_stars: int = 5) -> list[AssetMetadata]:
    # TODO: Review unreachable code - """Search for assets by quality rating.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - min_stars: Minimum star rating (inclusive)
    # TODO: Review unreachable code - max_stars: Maximum star rating (inclusive)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of matching assets
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - results = []

    # TODO: Review unreachable code - for asset in self.metadata_index.values():
    # TODO: Review unreachable code - # AssetMetadata is a TypedDict, access as dict
    # TODO: Review unreachable code - quality = asset.get("quality", {})
    # TODO: Review unreachable code - rating = quality.get("star_rating", 0)
    # TODO: Review unreachable code - if min_stars <= rating <= max_stars:
    # TODO: Review unreachable code - results.append(asset)

    # TODO: Review unreachable code - return results

    # TODO: Review unreachable code - # ===== Utility Methods =====

    # TODO: Review unreachable code - def rebuild_from_images(self, image_dir: Path) -> int:
    # TODO: Review unreachable code - """Rebuild cache from embedded image metadata.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - image_dir: Directory containing images

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Number of images processed
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - count = 0

    # TODO: Review unreachable code - for img_path in image_dir.rglob("*"):
    # TODO: Review unreachable code - if img_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Extract embedded metadata
    # TODO: Review unreachable code - metadata = self.embedder.extract_metadata(img_path)
    # TODO: Review unreachable code - if metadata and "alice_metadata" in metadata:
    # TODO: Review unreachable code - # Save to cache
    # TODO: Review unreachable code - analysis = metadata["alice_metadata"]
    # TODO: Review unreachable code - analysis_time = metadata.get("analysis_time", 0.0)
    # TODO: Review unreachable code - self.cache.save(img_path, analysis, analysis_time)
    # TODO: Review unreachable code - count += 1

    # TODO: Review unreachable code - logger.info(f"Rebuilt cache from {count} images")
    # TODO: Review unreachable code - return count

    # TODO: Review unreachable code - def get_stats(self) -> dict[str, Any]:
    # TODO: Review unreachable code - """Get cache statistics.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Cache performance statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - "cache_hits": self.cache_hits,
    # TODO: Review unreachable code - "cache_misses": self.cache_misses,
    # TODO: Review unreachable code - "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
    # TODO: Review unreachable code - "analysis_time_saved": self.analysis_time_saved,
    # TODO: Review unreachable code - "indexed_assets": len(self.metadata_index),
    # TODO: Review unreachable code - "project_id": self.project_id
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - def get_content_hash(self, file_path: Path) -> str:
    # TODO: Review unreachable code - """Get content hash for a file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - SHA256 hash of file content
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - hasher = hashlib.sha256()
    # TODO: Review unreachable code - with open(file_path, "rb") as f:
    # TODO: Review unreachable code - for chunk in iter(lambda: f.read(8192), b""):
    # TODO: Review unreachable code - hasher.update(chunk)
    # TODO: Review unreachable code - return hasher.hexdigest()

    # TODO: Review unreachable code - def save(self, media_path: Path, analysis: Any, analysis_time: float) -> None:
    # TODO: Review unreachable code - """Save analysis to cache (for backward compatibility).

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Path to media file
    # TODO: Review unreachable code - analysis: Analysis result
    # TODO: Review unreachable code - analysis_time: Time taken for analysis
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Get cache file path
    # TODO: Review unreachable code - content_hash = self.get_content_hash(media_path)
    # TODO: Review unreachable code - cache_file = self.cache_dir / f"{content_hash}.json"

    # TODO: Review unreachable code - # Create cache metadata
    # TODO: Review unreachable code - metadata = {
    # TODO: Review unreachable code - "version": "1.0",
    # TODO: Review unreachable code - "content_hash": content_hash,
    # TODO: Review unreachable code - "original_path": str(media_path),
    # TODO: Review unreachable code - "file_name": media_path.name,
    # TODO: Review unreachable code - "file_size": media_path.stat().st_size if media_path.exists() else 0,
    # TODO: Review unreachable code - "last_modified": media_path.stat().st_mtime if media_path.exists() else 0,
    # TODO: Review unreachable code - "analysis": analysis,
    # TODO: Review unreachable code - "analysis_time": analysis_time,
    # TODO: Review unreachable code - "cached_at": datetime.now().isoformat()
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Save to cache file
    # TODO: Review unreachable code - cache_file.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - with open(cache_file, 'w') as f:
    # TODO: Review unreachable code - json.dump(metadata, f, indent=2, default=str)

    # TODO: Review unreachable code - # ===== Private Methods =====

    # TODO: Review unreachable code - def _load_metadata_index(self) -> None:
    # TODO: Review unreachable code - """Load metadata index from cache."""
    # TODO: Review unreachable code - logger.info("Loading metadata index...")

    # TODO: Review unreachable code - cache_dir = self.source_root / ".metadata"
    # TODO: Review unreachable code - if not cache_dir.exists():
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - loaded = 0
    # TODO: Review unreachable code - for cache_file in cache_dir.rglob("*.json"):
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Load directly from JSON file
    # TODO: Review unreachable code - with open(cache_file) as f:
    # TODO: Review unreachable code - metadata = json.load(f)

    # TODO: Review unreachable code - if metadata and "enhanced_metadata" in metadata:
    # TODO: Review unreachable code - enhanced = metadata["enhanced_metadata"]
    # TODO: Review unreachable code - content_hash = cache_file.stem
    # TODO: Review unreachable code - self.metadata_index[content_hash] = enhanced
    # TODO: Review unreachable code - loaded += 1

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.debug(f"Skipping invalid cache file {cache_file}: {e}")

    # TODO: Review unreachable code - logger.info(f"Loaded {loaded} enhanced metadata entries")


# Backward compatibility aliases
def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of a file (backward compatible)."""
    # Avoid creating a new cache instance - use direct hashing
    import hashlib

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# TODO: Review unreachable code - def get_content_hash(file_path: Path) -> str:
# TODO: Review unreachable code - """Get content hash for a file (backward compatible)."""
# TODO: Review unreachable code - return get_file_hash(file_path)
