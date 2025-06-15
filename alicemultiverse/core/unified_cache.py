"""Unified cache implementation that consolidates all caching functionality."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..metadata.embedder import MetadataEmbedder
from ..metadata.extractor import MetadataExtractor
from ..metadata.models import AssetMetadata
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
            return None

        # Try embedded metadata first (self-contained assets)
        if media_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}:
            try:
                embedded = self.embedder.extract_metadata(media_path)
                if embedded:
                    # Check various possible locations for our metadata
                    if "alice_metadata" in embedded:
                        logger.debug(f"Loaded alice_metadata from image: {media_path.name}")
                        return embedded["alice_metadata"]
                    elif "metadata" in embedded:
                        logger.debug(f"Loaded metadata from image: {media_path.name}")
                        return embedded["metadata"]
                    elif any(key.startswith("claude_") for key in embedded):
                        # This is the format the embedder extracts
                        logger.debug(f"Loaded embedded metadata from image: {media_path.name}")
                        return embedded
            except Exception as e:
                logger.debug(f"Could not extract embedded metadata: {e}")

        # Fall back to cache
        result = self.cache.load(media_path)

        # Track cache hit/miss
        if result is not None:
            self.cache.cache_hits += 1
        else:
            self.cache.cache_misses += 1

        return result

    def save(self, media_path: Path, analysis: AnalysisResult, analysis_time: float) -> None:
        """Save metadata for a media file (backward compatible).

        Saves to both cache and embeds in image if possible.
        If understanding is enabled, runs understanding analysis.

        Args:
            media_path: Path to the media file
            analysis: Analysis results to cache
            analysis_time: Time taken for analysis
        """
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

        # Check if already enhanced
        if "enhanced_metadata" in basic:
            return basic["enhanced_metadata"]

        # Generate enhanced metadata
        content_hash = self.cache.get_content_hash(media_path)
        # Extract just the analysis from the full metadata structure
        analysis = basic.get("analysis", basic) if isinstance(basic, dict) else basic
        enhanced = self.extractor.extract_metadata(
            file_path=media_path,
            analysis=analysis,
            project_id=self.project_id,
            content_hash=content_hash,
        )

        # Store it
        self.metadata_index[content_hash] = enhanced
        return enhanced

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

        try:
            result = await self.understanding_analyzer.analyze(
                media_path,
                provider=self.understanding_provider,
                generate_prompt=True,
                extract_tags=True,
                detailed=False
            )
            return result
        except Exception as e:
            logger.error(f"Understanding analysis failed for {media_path}: {e}")
            return None

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
        analysis["version"] = self.cache_version

        return analysis

    # ===== Quality Scoring Interface =====

    def calculate_quality(self, media_path: Path) -> dict[str, Any] | None:
        """Calculate quality scores for a media file.

        Args:
            media_path: Path to the media file

        Returns:
            Quality analysis results
        """
        # Get existing metadata
        metadata = self.load(media_path)
        if not metadata:
            return None

        # Extract raw scores
        analysis = metadata.get("analysis", {})
        analysis.get("brisque_score")
        analysis.get("sightengine_results")
        analysis.get("claude_results")

        # Calculate merged quality
        # Quality assessment removed - return default
        return {"overall_score": 0.5, "star_rating": 3}

    # ===== Search Interface =====

    def search_by_tags(self, tags: list[str], tag_type: str | None = None) -> list[AssetMetadata]:
        """Search for assets by tags.

        Args:
            tags: Tags to search for
            tag_type: Optional tag type filter (style, mood, subject, etc.)

        Returns:
            List of matching assets
        """
        results = []

        for asset in self.metadata_index.values():
            # AssetMetadata is a TypedDict, access as dict
            asset_tags = asset.get("tags", {})

            # Check each tag type
            for t_type, t_list in asset_tags.items():
                if tag_type and t_type != tag_type:
                    continue

                if any(tag in t_list for tag in tags):
                    results.append(asset)
                    break

        return results

    def search_by_quality(self, min_stars: int = 1, max_stars: int = 5) -> list[AssetMetadata]:
        """Search for assets by quality rating.

        Args:
            min_stars: Minimum star rating (inclusive)
            max_stars: Maximum star rating (inclusive)

        Returns:
            List of matching assets
        """
        results = []

        for asset in self.metadata_index.values():
            # AssetMetadata is a TypedDict, access as dict
            quality = asset.get("quality", {})
            rating = quality.get("star_rating", 0)
            if min_stars <= rating <= max_stars:
                results.append(asset)

        return results

    # ===== Utility Methods =====

    def rebuild_from_images(self, image_dir: Path) -> int:
        """Rebuild cache from embedded image metadata.

        Args:
            image_dir: Directory containing images

        Returns:
            Number of images processed
        """
        count = 0

        for img_path in image_dir.rglob("*"):
            if img_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}:
                continue

            # Extract embedded metadata
            metadata = self.embedder.extract_metadata(img_path)
            if metadata and "alice_metadata" in metadata:
                # Save to cache
                analysis = metadata["alice_metadata"]
                analysis_time = metadata.get("analysis_time", 0.0)
                self.cache.save(img_path, analysis, analysis_time)
                count += 1

        logger.info(f"Rebuilt cache from {count} images")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache performance statistics
        """
        stats = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "analysis_time_saved": self.analysis_time_saved,
            "indexed_assets": len(self.metadata_index),
            "project_id": self.project_id
        }
        return stats

    def get_content_hash(self, file_path: Path) -> str:
        """Get content hash for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash of file content
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def save(self, media_path: Path, analysis: Any, analysis_time: float) -> None:
        """Save analysis to cache (for backward compatibility).
        
        Args:
            media_path: Path to media file
            analysis: Analysis result
            analysis_time: Time taken for analysis
        """
        # Get cache file path
        content_hash = self.get_content_hash(media_path)
        cache_file = self.cache_dir / f"{content_hash}.json"

        # Create cache metadata
        metadata = {
            "version": "1.0",
            "content_hash": content_hash,
            "original_path": str(media_path),
            "file_name": media_path.name,
            "file_size": media_path.stat().st_size if media_path.exists() else 0,
            "last_modified": media_path.stat().st_mtime if media_path.exists() else 0,
            "analysis": analysis,
            "analysis_time": analysis_time,
            "cached_at": datetime.now().isoformat()
        }

        # Save to cache file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

    # ===== Private Methods =====

    def _load_metadata_index(self) -> None:
        """Load metadata index from cache."""
        logger.info("Loading metadata index...")

        cache_dir = self.source_root / ".metadata"
        if not cache_dir.exists():
            return

        loaded = 0
        for cache_file in cache_dir.rglob("*.json"):
            try:
                # Load directly from JSON file
                with open(cache_file) as f:
                    metadata = json.load(f)

                if metadata and "enhanced_metadata" in metadata:
                    enhanced = metadata["enhanced_metadata"]
                    content_hash = cache_file.stem
                    self.metadata_index[content_hash] = enhanced
                    loaded += 1

            except Exception as e:
                logger.debug(f"Skipping invalid cache file {cache_file}: {e}")

        logger.info(f"Loaded {loaded} enhanced metadata entries")


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


def get_content_hash(file_path: Path) -> str:
    """Get content hash for a file (backward compatible)."""
    return get_file_hash(file_path)
