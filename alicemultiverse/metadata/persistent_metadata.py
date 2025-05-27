"""
Persistent metadata system that stores analysis results in image files.

This module coordinates between:
1. Embedding metadata in images (self-contained assets)
2. Cache for fast retrieval (performance optimization)
3. Recalculation of scores when needed

The key insight is that we store raw analysis values (BRISQUE score,
SightEngine results, Claude analysis) in the image, then recalculate
final scores as needed based on current thresholds/weights.
"""

import logging
from pathlib import Path
from typing import Any

from ..core.cache_migration import EnhancedMetadataCacheAdapter as EnhancedMetadataCache
from ..core.types import MediaType
from .embedder import MetadataEmbedder

logger = logging.getLogger(__name__)


class PersistentMetadataManager:
    """
    Manage metadata persistence in images and cache.

    Philosophy:
    - Images are self-contained with embedded analysis results
    - Cache is purely for performance, can be rebuilt from images
    - Final scores are recalculated based on current config
    """

    def __init__(
        self,
        cache_dir: Path,
        quality_thresholds: dict[str, float] | None = None,
        project_id: str = "default",
    ):
        """
        Initialize the persistent metadata manager.

        Args:
            cache_dir: Directory for metadata cache
            quality_thresholds: Thresholds for star ratings (can change over time)
            project_id: Project identifier for the cache
        """
        self.embedder = MetadataEmbedder()
        self.cache = EnhancedMetadataCache(
            source_root=cache_dir, project_id=project_id, force_reindex=False
        )
        self.quality_thresholds = quality_thresholds or {
            "5_star": {"min": 80},
            "4_star": {"min": 65, "max": 80},
            "3_star": {"min": 45, "max": 65},
            "2_star": {"min": 25, "max": 45},
            "1_star": {"max": 25},
        }

    def load_metadata(self, image_path: Path) -> tuple[dict[str, Any], bool]:
        """
        Load metadata for an image, preferring embedded data.

        Args:
            image_path: Path to the image

        Returns:
            Tuple of (metadata dict, from_cache bool)
        """
        # First, try to get from cache for performance
        content_hash = self.cache.get_content_hash(image_path)
        cached_metadata = self.cache.load_enhanced(image_path)

        # Extract embedded metadata from image
        embedded_metadata = self.embedder.extract_metadata(image_path)

        # Decide which to use
        if embedded_metadata and self._has_analysis_data(embedded_metadata):
            # Embedded data takes precedence
            metadata = embedded_metadata
            from_cache = False

            # Update cache with embedded data by saving
            # We need to create a dummy analysis result for the cache
            from ..core.types import AnalysisResult, MediaType

            dummy_analysis = AnalysisResult(
                source_type=metadata.get("source_type", "unknown"),
                date_taken=metadata.get("created_at", ""),
                project_folder=metadata.get("project_id", "unknown"),
                media_type=MediaType.IMAGE,
                prompt=metadata.get("prompt", ""),
                quality_score=metadata.get("brisque_score"),
                enhanced_metadata=metadata,
            )
            self.cache.save_enhanced(image_path, dummy_analysis, 0.0, metadata)
        elif cached_metadata:
            # Use cache if no embedded data
            metadata = cached_metadata
            from_cache = True
        else:
            # No existing metadata
            metadata = {"content_hash": content_hash}
            from_cache = False

        # Always recalculate final scores based on current thresholds
        if self._has_analysis_data(metadata):
            self._recalculate_scores(metadata)

        return metadata, from_cache

    def save_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """
        Save metadata to both image and cache.

        Args:
            image_path: Path to the image
            metadata: Metadata to save

        Returns:
            True if successful
        """
        success = True

        # Embed in image file (all our supported formats have good metadata support)
        if image_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            if not self.embedder.embed_metadata(image_path, metadata):
                logger.warning(f"Failed to embed metadata in {image_path}")
                success = False

        # Always update cache
        content_hash = metadata.get("content_hash")
        if not content_hash:
            content_hash = self.cache.get_content_hash(image_path)
            metadata["content_hash"] = content_hash

        # Save to cache using save_enhanced
        from ..core.types import AnalysisResult

        dummy_analysis = AnalysisResult(
            source_type=metadata.get("source_type", "unknown"),
            date_taken=metadata.get("created_at", ""),
            project_folder=metadata.get("project_id", "unknown"),
            media_type=MediaType.IMAGE,
            prompt=metadata.get("prompt", ""),
            quality_score=metadata.get("brisque_score"),
            enhanced_metadata=metadata,
        )
        self.cache.save_enhanced(image_path, dummy_analysis, 0.0, metadata)

        return success

    def rebuild_cache_from_images(self, image_dir: Path) -> int:
        """
        Rebuild cache by extracting embedded metadata from all images.

        Args:
            image_dir: Directory containing images

        Returns:
            Number of images processed
        """
        count = 0

        for image_path in image_dir.rglob("*"):
            if image_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                try:
                    embedded_metadata = self.embedder.extract_metadata(image_path)
                    if embedded_metadata and self._has_analysis_data(embedded_metadata):
                        content_hash = self.cache.get_content_hash(image_path)
                        embedded_metadata["content_hash"] = content_hash
                        embedded_metadata["file_path"] = str(image_path)

                        # Recalculate scores
                        self._recalculate_scores(embedded_metadata)

                        # Update cache
                        from ..core.types import AnalysisResult, MediaType

                        dummy_analysis = AnalysisResult(
                            source_type=embedded_metadata.get("source_type", "unknown"),
                            date_taken=embedded_metadata.get("created_at", ""),
                            project_folder=embedded_metadata.get("project_id", "unknown"),
                            media_type=MediaType.IMAGE,
                            prompt=embedded_metadata.get("prompt", ""),
                            quality_score=embedded_metadata.get("brisque_score"),
                            enhanced_metadata=embedded_metadata,
                        )
                        self.cache.save_enhanced(image_path, dummy_analysis, 0.0, embedded_metadata)
                        count += 1

                        if count % 100 == 0:
                            logger.info(f"Rebuilt cache for {count} images...")

                except Exception as e:
                    logger.error(f"Failed to process {image_path}: {e}")

        logger.info(f"Cache rebuilt from {count} images")
        return count

    def _has_analysis_data(self, metadata: dict[str, Any]) -> bool:
        """Check if metadata contains analysis results."""
        analysis_fields = ["brisque_score", "sightengine_quality", "claude_defects_found"]
        return any(field in metadata for field in analysis_fields)

    def _recalculate_scores(self, metadata: dict[str, Any]) -> None:
        """
        Recalculate final quality scores based on current thresholds.

        This allows us to adjust scoring without re-analyzing images.
        """
        # Get raw scores
        brisque_score = metadata.get("brisque_score")
        sightengine_quality = metadata.get("sightengine_quality")
        claude_quality = metadata.get("claude_quality_score")

        # Calculate normalized scores
        if brisque_score is not None:
            # BRISQUE: 0-100, lower is better
            brisque_normalized = max(0, min(1, (100 - brisque_score) / 100))
            metadata["brisque_normalized"] = brisque_normalized

        # Determine which scores we have
        available_scores = []
        weights = []

        if brisque_score is not None:
            available_scores.append(brisque_normalized)
            weights.append(0.4)  # Default weight

        if sightengine_quality is not None:
            available_scores.append(sightengine_quality)
            weights.append(0.3)

        if claude_quality is not None:
            available_scores.append(claude_quality)
            weights.append(0.3)

        # Calculate combined score
        if available_scores:
            # Normalize weights
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]

            # Weighted average
            combined_score = sum(
                score * weight
                for score, weight in zip(available_scores, normalized_weights, strict=False)
            )

            metadata["combined_quality_score"] = combined_score

            # Map to star rating
            if brisque_score is not None:  # Use BRISQUE thresholds
                for stars in range(5, 0, -1):
                    threshold_key = f"{stars}_star"
                    if threshold_key in self.quality_thresholds:
                        thresholds = self.quality_thresholds[threshold_key]
                        min_val = thresholds.get("min", 0)
                        max_val = thresholds.get("max", 100)

                        if min_val <= brisque_score < max_val:
                            metadata["quality_stars"] = stars
                            break
            else:
                # Use combined score for star rating
                if combined_score >= 0.85:
                    metadata["quality_stars"] = 5
                elif combined_score >= 0.70:
                    metadata["quality_stars"] = 4
                elif combined_score >= 0.50:
                    metadata["quality_stars"] = 3
                elif combined_score >= 0.30:
                    metadata["quality_stars"] = 2
                else:
                    metadata["quality_stars"] = 1

    def get_metadata_status(self, image_dir: Path) -> dict[str, int]:
        """
        Get statistics about metadata coverage.

        Returns:
            Dict with counts of images with embedded metadata, cache only, etc.
        """
        status = {
            "total_images": 0,
            "with_embedded_metadata": 0,
            "with_analysis_data": 0,
            "cache_only": 0,
            "no_metadata": 0,
        }

        for image_path in image_dir.rglob("*"):
            if image_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                status["total_images"] += 1

                # Check embedded metadata
                embedded = self.embedder.extract_metadata(image_path)
                has_embedded = bool(embedded)
                has_analysis = self._has_analysis_data(embedded) if embedded else False

                # Check cache
                cached = self.cache.load_enhanced(image_path)

                if has_embedded:
                    status["with_embedded_metadata"] += 1
                    if has_analysis:
                        status["with_analysis_data"] += 1
                elif cached:
                    status["cache_only"] += 1
                else:
                    status["no_metadata"] += 1

        return status
