"""Build and rebuild DuckDB search index from file metadata."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from tqdm import tqdm

from ..core.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ..core.structured_logging import get_logger
from .duckdb_search import DuckDBSearch
from .metadata_extractor import MetadataExtractor

logger = get_logger(__name__)


class SearchIndexBuilder:
    """Builds search index from file metadata."""

    def __init__(self, db_path: str | None = None):
        """Initialize index builder.

        Args:
            db_path: Path to DuckDB database file
        """
        self.search_db = DuckDBSearch(db_path)
        self.extractor = MetadataExtractor()

    def rebuild_from_paths(self, paths: list[str], show_progress: bool = True) -> int:
        """Rebuild search index from files in given paths.

        Args:
            paths: List of directories to scan
            show_progress: Whether to show progress bar

        Returns:
            Number of assets indexed
        """
        # First collect all media files
        media_files = []
        extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

        logger.info(f"Scanning {len(paths)} paths for media files...")

        for path_str in paths:
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue

            if path.is_file() and path.suffix.lower() in extensions:
                # Check if file is in sorted-out folder
                if not any(part in ['sorted-out', 'sorted_out'] for part in path.parts):
                    media_files.append(path)
            elif path.is_dir():
                for ext in extensions:
                    # Find all files but filter out sorted-out folders
                    all_files = path.rglob(f"*{ext}")
                    filtered_files = [
                        f for f in all_files
                        if not any(part in ['sorted-out', 'sorted_out'] for part in f.parts)
                    ]
                    media_files.extend(filtered_files)

        logger.info(f"Found {len(media_files)} media files to index")

        # Clear existing index
        logger.info("Clearing existing search index...")
        self.search_db.clear_index()

        # Index each file
        indexed_count = 0

        if show_progress:
            file_iterator = tqdm(media_files, desc="Indexing files")
        else:
            file_iterator = media_files

        for file_path in file_iterator:
            try:
                # Extract metadata
                metadata = self._extract_full_metadata(file_path)
                if metadata:
                    # Add to search index
                    self.search_db.index_asset(metadata)

                    # Calculate and index perceptual hashes for images
                    if metadata.get("media_type") == "image":
                        self._index_perceptual_hashes(file_path, metadata.get("content_hash"))

                    indexed_count += 1

                    if show_progress and indexed_count % 100 == 0:
                        logger.debug(f"Indexed {indexed_count} files...")

            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")

        logger.info(f"Successfully indexed {indexed_count} of {len(media_files)} files")

        # Get index statistics
        stats = self.search_db.get_statistics()
        logger.info(
            f"Index statistics: {stats.get('total_assets', 0)} assets, "
            f"{stats.get('unique_tags', 0)} unique tags"
        )

        return indexed_count

    # TODO: Review unreachable code - def _index_perceptual_hashes(self, file_path: Path, content_hash: str) -> None:
    # TODO: Review unreachable code - """Calculate and index perceptual hashes for an image.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to image file
    # TODO: Review unreachable code - content_hash: Content hash of the file
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - from ..assets.perceptual_hashing import (
    # TODO: Review unreachable code - calculate_average_hash,
    # TODO: Review unreachable code - calculate_difference_hash,
    # TODO: Review unreachable code - calculate_perceptual_hash,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Calculate different hash types
    # TODO: Review unreachable code - phash = calculate_perceptual_hash(file_path)
    # TODO: Review unreachable code - dhash = calculate_difference_hash(file_path)
    # TODO: Review unreachable code - ahash = calculate_average_hash(file_path)

    # TODO: Review unreachable code - # Store in database
    # TODO: Review unreachable code - if any([phash, dhash, ahash]):
    # TODO: Review unreachable code - self.search_db.index_perceptual_hashes(
    # TODO: Review unreachable code - content_hash=content_hash,
    # TODO: Review unreachable code - phash=phash,
    # TODO: Review unreachable code - dhash=dhash,
    # TODO: Review unreachable code - ahash=ahash
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - logger.debug(f"Indexed perceptual hashes for {file_path.name}")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to calculate perceptual hashes for {file_path}: {e}")

    # TODO: Review unreachable code - def update_from_path(self, path: str) -> int:
    # TODO: Review unreachable code - """Update index with new or modified files from a path.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - path: Directory to scan for updates

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Number of files updated
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - path_obj = Path(path)
    # TODO: Review unreachable code - if not path_obj.exists():
    # TODO: Review unreachable code - logger.warning(f"Path does not exist: {path}")
    # TODO: Review unreachable code - return 0

    # TODO: Review unreachable code - updated_count = 0
    # TODO: Review unreachable code - extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

    # TODO: Review unreachable code - # Find media files
    # TODO: Review unreachable code - media_files = []
    # TODO: Review unreachable code - if path_obj.is_file() and path_obj.suffix.lower() in extensions:
    # TODO: Review unreachable code - media_files = [path_obj]
    # TODO: Review unreachable code - elif path_obj.is_dir():
    # TODO: Review unreachable code - for ext in extensions:
    # TODO: Review unreachable code - media_files.extend(path_obj.rglob(f"*{ext}"))

    # TODO: Review unreachable code - for file_path in media_files:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Extract metadata
    # TODO: Review unreachable code - metadata = self._extract_full_metadata(file_path)
    # TODO: Review unreachable code - if metadata:
    # TODO: Review unreachable code - # Check if already indexed
    # TODO: Review unreachable code - content_hash = metadata.get("content_hash")
    # TODO: Review unreachable code - if content_hash:
    # TODO: Review unreachable code - existing, _ = self.search_db.search({"content_hash": content_hash})

    # TODO: Review unreachable code - # Update if modified or new
    # TODO: Review unreachable code - if not existing or existing[0]["modified_at"] < metadata.get("modified_at", ""):
    # TODO: Review unreachable code - self.search_db.index_asset(metadata)
    # TODO: Review unreachable code - updated_count += 1

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to update {file_path}: {e}")

    # TODO: Review unreachable code - logger.info(f"Updated {updated_count} files in index")
    # TODO: Review unreachable code - return updated_count

    # TODO: Review unreachable code - def verify_index(self) -> dict:
    # TODO: Review unreachable code - """Verify index integrity and find missing files.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dict with verification results
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - logger.info("Verifying search index...")

    # TODO: Review unreachable code - # Get all indexed assets
    # TODO: Review unreachable code - all_assets, total = self.search_db.search({}, limit=10000)

    # TODO: Review unreachable code - missing_files = []
    # TODO: Review unreachable code - valid_files = 0

    # TODO: Review unreachable code - for asset in all_assets:
    # TODO: Review unreachable code - file_path = Path(asset.get("file_path", ""))
    # TODO: Review unreachable code - if file_path.exists():
    # TODO: Review unreachable code - valid_files += 1
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - missing_files.append(str(file_path))

    # TODO: Review unreachable code - results = {
    # TODO: Review unreachable code - "total_indexed": total,
    # TODO: Review unreachable code - "valid_files": valid_files,
    # TODO: Review unreachable code - "missing_files": len(missing_files),
    # TODO: Review unreachable code - "missing_file_paths": missing_files[:100],  # Limit to first 100
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Index verification: {valid_files}/{total} files exist, "
    # TODO: Review unreachable code - f"{len(missing_files)} missing"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return results

    # TODO: Review unreachable code - def _extract_full_metadata(self, file_path: Path) -> dict[str, Any]:
    # TODO: Review unreachable code - """Extract full metadata including content hash and required fields.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to media file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Complete metadata dict ready for indexing
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Calculate content hash first
    # TODO: Review unreachable code - content_hash = self._calculate_content_hash(file_path)

    # TODO: Review unreachable code - # Check for cached metadata
    # TODO: Review unreachable code - cached_metadata = self._load_cached_metadata(file_path, content_hash)
    # TODO: Review unreachable code - if cached_metadata:
    # TODO: Review unreachable code - # Use cached metadata as base
    # TODO: Review unreachable code - metadata = self._extract_indexable_data(cached_metadata)
    # TODO: Review unreachable code - metadata["content_hash"] = content_hash
    # TODO: Review unreachable code - metadata["file_path"] = str(file_path)
    # TODO: Review unreachable code - metadata["file_size"] = file_path.stat().st_size

    # TODO: Review unreachable code - # Update timestamps from file
    # TODO: Review unreachable code - stat = file_path.stat()
    # TODO: Review unreachable code - metadata["created_at"] = datetime.fromtimestamp(stat.st_ctime)
    # TODO: Review unreachable code - metadata["modified_at"] = datetime.fromtimestamp(stat.st_mtime)
    # TODO: Review unreachable code - metadata["discovered_at"] = datetime.now()
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Fallback to embedded metadata extraction
    # TODO: Review unreachable code - metadata = self.extractor.extract_metadata(file_path)

    # TODO: Review unreachable code - # Add required fields
    # TODO: Review unreachable code - metadata["content_hash"] = content_hash
    # TODO: Review unreachable code - metadata["file_path"] = str(file_path)
    # TODO: Review unreachable code - metadata["file_size"] = file_path.stat().st_size

    # TODO: Review unreachable code - # Add timestamps
    # TODO: Review unreachable code - stat = file_path.stat()
    # TODO: Review unreachable code - metadata["created_at"] = datetime.fromtimestamp(stat.st_ctime)
    # TODO: Review unreachable code - metadata["modified_at"] = datetime.fromtimestamp(stat.st_mtime)
    # TODO: Review unreachable code - metadata["discovered_at"] = datetime.now()

    # TODO: Review unreachable code - # Ensure media type is set
    # TODO: Review unreachable code - if "media_type" not in metadata:
    # TODO: Review unreachable code - suffix = file_path.suffix.lower()
    # TODO: Review unreachable code - if suffix in IMAGE_EXTENSIONS:
    # TODO: Review unreachable code - metadata["media_type"] = "image"
    # TODO: Review unreachable code - elif suffix in VIDEO_EXTENSIONS:
    # TODO: Review unreachable code - metadata["media_type"] = "video"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - metadata["media_type"] = "unknown"

    # TODO: Review unreachable code - # Extract AI source from filename patterns
    # TODO: Review unreachable code - filename = file_path.name.lower()
    # TODO: Review unreachable code - if "midjourney" in filename or "miasmah" in filename:
    # TODO: Review unreachable code - metadata["ai_source"] = "midjourney"
    # TODO: Review unreachable code - elif "dalle" in filename or "dall-e" in filename:
    # TODO: Review unreachable code - metadata["ai_source"] = "dalle"
    # TODO: Review unreachable code - elif "stable" in filename or "sd" in filename:
    # TODO: Review unreachable code - metadata["ai_source"] = "stablediffusion"
    # TODO: Review unreachable code - elif filename is not None and "leonardo" in filename:
    # TODO: Review unreachable code - metadata["ai_source"] = "leonardo"
    # TODO: Review unreachable code - elif filename is not None and "firefly" in filename:
    # TODO: Review unreachable code - metadata["ai_source"] = "firefly"

    # TODO: Review unreachable code - # Extract prompt from filename if available
    # TODO: Review unreachable code - if "prompt" not in metadata and "_" in filename:
    # TODO: Review unreachable code - # Many AI tools put prompt in filename
    # TODO: Review unreachable code - parts = filename.split("_")
    # TODO: Review unreachable code - if len(parts) > 2:
    # TODO: Review unreachable code - # Skip the first part (usually tool name) and last part (ID/extension)
    # TODO: Review unreachable code - potential_prompt = "_".join(parts[1:-1])
    # TODO: Review unreachable code - if len(potential_prompt) > 10:  # Reasonable prompt length
    # TODO: Review unreachable code - metadata["prompt"] = potential_prompt.replace("_", " ")

    # TODO: Review unreachable code - return metadata

    # TODO: Review unreachable code - def _load_cached_metadata(self, file_path: Path, content_hash: str) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Load metadata from cache if available.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to media file
    # TODO: Review unreachable code - content_hash: SHA256 hash of file content

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Cached metadata dict or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Look for .metadata folder in parent directories
    # TODO: Review unreachable code - current_dir = file_path.parent

    # TODO: Review unreachable code - # First check immediate parent, then walk up to find .metadata
    # TODO: Review unreachable code - while current_dir != current_dir.parent:  # Stop at root
    # TODO: Review unreachable code - metadata_dir = current_dir / ".metadata"
    # TODO: Review unreachable code - if metadata_dir.exists():
    # TODO: Review unreachable code - # Build cache file path
    # TODO: Review unreachable code - hash_prefix = content_hash[:2]
    # TODO: Review unreachable code - cache_file = metadata_dir / hash_prefix / f"{content_hash}.json"

    # TODO: Review unreachable code - if cache_file.exists():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(cache_file) as f:
    # TODO: Review unreachable code - cached_data = json.load(f)
    # TODO: Review unreachable code - logger.debug(f"Loaded cached metadata for {file_path.name} from {cache_file}")
    # TODO: Review unreachable code - return cached_data
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to load cached metadata from {cache_file}: {e}")

    # TODO: Review unreachable code - # If not found in the expected location, check if it's an older flat structure
    # TODO: Review unreachable code - old_cache_file = metadata_dir / f"{content_hash}.json"
    # TODO: Review unreachable code - if old_cache_file.exists():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(old_cache_file) as f:
    # TODO: Review unreachable code - cached_data = json.load(f)
    # TODO: Review unreachable code - logger.debug(f"Loaded cached metadata for {file_path.name} from old location")
    # TODO: Review unreachable code - return cached_data
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to load cached metadata from old location: {e}")

    # TODO: Review unreachable code - # Only check the first .metadata directory found
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - current_dir = current_dir.parent

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def _extract_indexable_data(self, cached_data: dict[str, Any]) -> dict[str, Any]:
    # TODO: Review unreachable code - """Extract indexable fields from cached metadata.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - cached_data: Full cached metadata

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Metadata dict with indexable fields
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - metadata = {}

    # TODO: Review unreachable code - # Direct fields from cache structure
    # TODO: Review unreachable code - for field in ["content_hash", "file_size", "last_modified"]:
    # TODO: Review unreachable code - if field in cached_data:
    # TODO: Review unreachable code - metadata[field] = cached_data[field]

    # TODO: Review unreachable code - # Extract from analysis section
    # TODO: Review unreachable code - if cached_data is not None and "analysis" in cached_data:
    # TODO: Review unreachable code - analysis = cached_data["analysis"]

    # TODO: Review unreachable code - # Media type and AI source
    # TODO: Review unreachable code - metadata["media_type"] = analysis.get("media_type", "unknown")
    # TODO: Review unreachable code - # Handle MediaType enum values
    # TODO: Review unreachable code - if hasattr(metadata["media_type"], "value"):
    # TODO: Review unreachable code - metadata["media_type"] = metadata["media_type"].value

    # TODO: Review unreachable code - metadata["ai_source"] = analysis.get("source_type")

    # TODO: Review unreachable code - # Understanding data (tags)
    # TODO: Review unreachable code - if analysis is not None and "understanding" in analysis:
    # TODO: Review unreachable code - understanding = analysis["understanding"]
    # TODO: Review unreachable code - # Handle new v4.0 format where understanding is a dict with structured data
    # TODO: Review unreachable code - if isinstance(understanding, dict):
    # TODO: Review unreachable code - # Extract tags - they should be a dict of categories
    # TODO: Review unreachable code - if understanding is not None and "tags" in understanding and isinstance(understanding["tags"], dict):
    # TODO: Review unreachable code - # Flatten all tag categories into a single list
    # TODO: Review unreachable code - all_tags = []
    # TODO: Review unreachable code - for category, tag_list in understanding["tags"].items():
    # TODO: Review unreachable code - if isinstance(tag_list, list):
    # TODO: Review unreachable code - all_tags.extend(tag_list)
    # TODO: Review unreachable code - metadata["tags"] = list(set(all_tags))  # Deduplicate

    # TODO: Review unreachable code - # Extract prompt if available
    # TODO: Review unreachable code - if understanding is not None and "positive_prompt" in understanding:
    # TODO: Review unreachable code - metadata["prompt"] = understanding["positive_prompt"]

    # TODO: Review unreachable code - # Extract description
    # TODO: Review unreachable code - if understanding is not None and "description" in understanding:
    # TODO: Review unreachable code - metadata["description"] = understanding["description"]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Legacy format - multiple provider data
    # TODO: Review unreachable code - tags = []
    # TODO: Review unreachable code - for provider_data in understanding.values():
    # TODO: Review unreachable code - if isinstance(provider_data, dict) and "tags" in provider_data:
    # TODO: Review unreachable code - tags.extend(provider_data["tags"])
    # TODO: Review unreachable code - if tags:
    # TODO: Review unreachable code - metadata["tags"] = list(set(tags))  # Deduplicate

    # TODO: Review unreachable code - # Quality information (legacy - now using understanding system)
    # TODO: Review unreachable code - if analysis is not None and "quality_stars" in analysis:
    # TODO: Review unreachable code - metadata["quality_rating"] = analysis["quality_stars"]
    # TODO: Review unreachable code - if analysis is not None and "final_combined_score" in analysis:
    # TODO: Review unreachable code - metadata["quality_score"] = analysis["final_combined_score"]

    # TODO: Review unreachable code - # Extract prompt from original path or filename
    # TODO: Review unreachable code - original_path = cached_data.get("original_path", cached_data.get("file_name", ""))
    # TODO: Review unreachable code - if original_path:
    # TODO: Review unreachable code - filename = Path(original_path).name.lower()
    # TODO: Review unreachable code - if filename is not None and "_" in filename:
    # TODO: Review unreachable code - parts = filename.split("_")
    # TODO: Review unreachable code - if len(parts) > 2:
    # TODO: Review unreachable code - potential_prompt = "_".join(parts[1:-1])
    # TODO: Review unreachable code - if len(potential_prompt) > 10:
    # TODO: Review unreachable code - metadata["prompt"] = potential_prompt.replace("_", " ")

    # TODO: Review unreachable code - return metadata

    # TODO: Review unreachable code - def _calculate_content_hash(self, file_path: Path) -> str:
    # TODO: Review unreachable code - """Calculate SHA256 hash of file content.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Hex string of content hash
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - sha256_hash = hashlib.sha256()
    # TODO: Review unreachable code - with open(file_path, "rb") as f:
    # TODO: Review unreachable code - # Read in chunks to handle large files
    # TODO: Review unreachable code - for byte_block in iter(lambda: f.read(4096), b""):
    # TODO: Review unreachable code - sha256_hash.update(byte_block)
    # TODO: Review unreachable code - return sha256_hash.hexdigest()
