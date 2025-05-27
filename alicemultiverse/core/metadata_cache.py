"""Metadata caching functionality for AliceMultiverse.

DEPRECATED: This module is deprecated and will be removed in v3.0.
Please use alicemultiverse.core.unified_cache.UnifiedCache instead.
"""

import hashlib
import json
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

from .constants import CACHE_VERSION, HASH_CHUNK_SIZE, METADATA_DIR_NAME
from .exceptions import CacheError
from .types import AnalysisResult, CacheMetadata

logger = logging.getLogger(__name__)

# Issue deprecation warning when module is imported
warnings.warn(
    "MetadataCache is deprecated and will be removed in v3.0. "
    "Please use UnifiedCache instead. "
    "Current code uses adapters for compatibility.",
    DeprecationWarning,
    stacklevel=2,
)


class MetadataCache:
    """Handle metadata caching for media files.

    The cache stores metadata using content hashes as filenames, allowing
    files to be moved within the source directory without losing metadata.

    Attributes:
        source_root: Root directory for source files
        force_reindex: Whether to bypass cache and force re-analysis
        cache_hits: Number of cache hits
        cache_misses: Number of cache misses
        analysis_time_saved: Total time saved by using cache (seconds)
    """

    def __init__(self, source_root: Path, force_reindex: bool = False):
        """Initialize metadata cache.

        Args:
            source_root: Root directory for source files
            force_reindex: Whether to bypass cache and force re-analysis
        """
        self.source_root = source_root
        self.force_reindex = force_reindex
        self.cache_hits = 0
        self.cache_misses = 0
        self.analysis_time_saved = 0.0

        # Ensure cache directory exists
        self._cache_dir = source_root / METADATA_DIR_NAME
        if not self.force_reindex:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_content_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content.

        Args:
            file_path: Path to the file to hash

        Returns:
            Hexadecimal string representation of the SHA256 hash

        Raises:
            CacheError: If file cannot be read
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except OSError as e:
            raise CacheError(f"Failed to hash file {file_path}: {e}")

    def load(self, media_path: Path) -> CacheMetadata | None:
        """Load cached metadata for a media file.

        Args:
            media_path: Path to the media file

        Returns:
            Cached metadata if available and valid, None otherwise
        """
        if self.force_reindex:
            return None

        content_hash = self.get_content_hash(media_path)
        cache_path = self._get_cache_path(content_hash)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                metadata = json.load(f)

            # Validate cache version
            if metadata.get("version") != CACHE_VERSION:
                logger.debug(f"Cache version mismatch for {media_path.name}")
                return None

            # Check if file has changed
            current_hash = self._compute_quick_hash(media_path)
            if metadata.get("file_hash") != current_hash:
                logger.debug(f"File changed since cache: {media_path.name}")
                return None

            # Convert media_type string back to enum if present
            if "analysis" in metadata and "media_type" in metadata["analysis"]:
                from alicemultiverse.core.types import MediaType

                media_type_str = metadata["analysis"]["media_type"]
                if isinstance(media_type_str, str):
                    try:
                        metadata["analysis"]["media_type"] = MediaType(media_type_str)
                    except ValueError:
                        # If conversion fails, leave as string
                        pass

            return metadata

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load cache for {media_path.name}: {e}")
            return None

    def save(self, media_path: Path, analysis: AnalysisResult, analysis_time: float) -> None:
        """Save metadata cache for a media file.

        Args:
            media_path: Path to the media file
            analysis: Analysis results to cache
            analysis_time: Time taken for analysis (seconds)

        Raises:
            CacheError: If cache cannot be saved
        """
        try:
            content_hash = self.get_content_hash(media_path)
            cache_path = self._get_cache_path(content_hash)

            # Convert MediaType enum to string if present
            analysis_copy = dict(analysis)
            if "media_type" in analysis_copy and hasattr(analysis_copy["media_type"], "value"):
                analysis_copy["media_type"] = analysis_copy["media_type"].value

            # Build metadata structure
            stat = media_path.stat()
            metadata: CacheMetadata = {
                "version": CACHE_VERSION,
                "file_hash": self._compute_quick_hash(media_path),
                "content_hash": content_hash,
                "original_path": (
                    str(media_path)
                    if not media_path.is_relative_to(self.source_root)
                    else str(media_path.relative_to(self.source_root))
                ),
                "file_name": media_path.name,
                "file_size": stat.st_size,
                "last_modified": stat.st_mtime,
                "analysis": analysis_copy,
                "analysis_time": analysis_time,
                "cached_at": datetime.now().isoformat(),
            }

            # Ensure cache directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            # Write cache file
            with open(cache_path, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.debug(f"Cached metadata for {media_path.name}")

        except Exception as e:
            # Log error but don't fail the operation
            logger.error(f"Failed to save cache for {media_path.name}: {e}")

    def update_stats(self, from_cache: bool, time_saved: float = 0) -> None:
        """Update cache hit/miss statistics.

        Args:
            from_cache: Whether the data was loaded from cache
            time_saved: Time saved by using cache (seconds)
        """
        if from_cache:
            self.cache_hits += 1
            self.analysis_time_saved += time_saved
        else:
            self.cache_misses += 1

    def set_metadata(
        self, media_path: Path, analysis: AnalysisResult, analysis_time: float = 0.0
    ) -> None:
        """Set metadata for a media file (alias for save).

        Args:
            media_path: Path to the media file
            analysis: Analysis results to cache
            analysis_time: Time taken for analysis (seconds)
        """
        self.save(media_path, analysis, analysis_time)

    def get_metadata(self, media_path: Path) -> CacheMetadata | None:
        """Get metadata for a media file (alias for load).

        Args:
            media_path: Path to the media file

        Returns:
            Cached metadata if available and valid, None otherwise
        """
        return self.load(media_path)

    def has_metadata(self, media_path: Path) -> bool:
        """Check if metadata exists for a media file.

        Args:
            media_path: Path to the media file

        Returns:
            True if cached metadata exists and is valid, False otherwise
        """
        if self.force_reindex:
            return False

        # Try to load the metadata to ensure it's valid
        return self.load(media_path) is not None

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary containing cache statistics
        """
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "total_processed": total,
            "time_saved": self.analysis_time_saved,
        }

    def _get_cache_path(self, content_hash: str) -> Path:
        """Get the cache file path for a content hash.

        Args:
            content_hash: SHA256 hash of file content

        Returns:
            Path to the cache file
        """
        # Use first two characters of hash for subdirectory (sharding)
        subdir = self._cache_dir / content_hash[:2]
        return subdir / f"{content_hash}.json"

    def _compute_quick_hash(self, file_path: Path) -> str:
        """Compute a quick hash for change detection.

        This uses file size, mtime, and first 1KB to quickly detect changes.

        Args:
            file_path: Path to the file

        Returns:
            Quick hash string
        """
        stat = file_path.stat()
        size = stat.st_size
        mtime = stat.st_mtime

        # Quick hash based on size, mtime, and first 1KB
        with open(file_path, "rb") as f:
            first_kb = f.read(1024)

        hash_str = f"{size}:{mtime}:{hashlib.md5(first_kb, usedforsecurity=False).hexdigest()}"
        return hashlib.md5(hash_str.encode(), usedforsecurity=False).hexdigest()[:16]


# Public convenience functions for testing
def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of a file."""
    cache = MetadataCache(file_path.parent)
    return cache.get_content_hash(file_path)


def get_content_hash(file_path: Path) -> str:
    """Get content hash for an image file."""
    # For images, this could do perceptual hashing, but for now just use file hash
    return get_file_hash(file_path)
