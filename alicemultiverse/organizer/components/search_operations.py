"""Search and indexing operations for media organizer."""

from datetime import datetime
from pathlib import Path

from ...core.logging import get_logger
from ...core.types import MediaType

logger = get_logger(__name__)


class SearchOperationsMixin:
    """Mixin for search index and perceptual hashing operations."""

    def _update_search_index(self, file_path: Path, analysis: dict) -> None:
        """Update search index with newly organized file.
        
        Args:
            file_path: Path to the organized file
            analysis: Analysis results containing metadata
        """
        if not self.search_db or self.config.processing.dry_run:
            logger.warning(f"Skipping search index update: search_db={bool(self.search_db)}, dry_run={self.config.processing.dry_run}")
            return

        logger.info(f"_update_search_index called for {file_path.name}")
        try:
            # Build metadata for indexing
            metadata = {
                "content_hash": analysis.get("content_hash"),
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "media_type": analysis.get("media_type", MediaType.IMAGE),
                "ai_source": analysis.get("source_type"),
                "quality_rating": analysis.get("quality_stars"),
                "quality_score": analysis.get("final_combined_score"),
                "prompt": analysis.get("prompt"),
                "project": analysis.get("project_folder"),
                "created_at": datetime.now(),
                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime),
                "discovered_at": datetime.now(),
            }

            # Extract tags from understanding data if available
            if "understanding" in analysis:
                understanding = analysis["understanding"]
                if isinstance(understanding, dict) and "tags" in understanding:
                    metadata["tags"] = understanding["tags"]
                    # Also extract description and prompts
                    if "description" in understanding:
                        metadata["description"] = understanding["description"]
                    if "positive_prompt" in understanding:
                        metadata["prompt"] = understanding["positive_prompt"]

            # Extract prompt from filename if not in analysis
            if not metadata["prompt"] and "_" in file_path.name:
                parts = file_path.name.split("_")
                if len(parts) > 2:
                    potential_prompt = "_".join(parts[1:-1])
                    if len(potential_prompt) > 10:
                        metadata["prompt"] = potential_prompt.replace("_", " ")

            # Index the asset
            self.search_db.index_asset(metadata)
            logger.info(f"Indexed asset in search: {file_path.name}")

            # Calculate and index perceptual hashes for images
            media_type = metadata.get("media_type")
            logger.debug(f"Media type for perceptual hashing: {media_type} (type: {type(media_type)})")
            if (media_type == MediaType.IMAGE or
                media_type == "image" or
                (hasattr(media_type, 'value') and media_type.value == "image") or
                str(media_type) == "MediaType.IMAGE"):
                logger.debug(f"Calculating perceptual hashes for {file_path.name}")
                self._index_perceptual_hashes(file_path, metadata.get("content_hash"))

        except Exception as e:
            logger.error(f"Failed to update search index for {file_path}: {e}", exc_info=True)

    def _index_perceptual_hashes(self, file_path: Path, content_hash: str) -> None:
        """Calculate and index perceptual hashes for an image.
        
        Args:
            file_path: Path to image file  
            content_hash: Content hash of the file
        """
        if not self.search_db or not content_hash:
            return

        try:
            from ...assets.perceptual_hashing import (
                calculate_average_hash,
                calculate_difference_hash,
                calculate_perceptual_hash,
            )

            # Calculate different hash types
            phash = calculate_perceptual_hash(file_path)
            dhash = calculate_difference_hash(file_path)
            ahash = calculate_average_hash(file_path)

            # Store in database
            if any([phash, dhash, ahash]):
                self.search_db.index_perceptual_hashes(
                    content_hash=content_hash,
                    phash=phash,
                    dhash=dhash,
                    ahash=ahash
                )
                logger.info(f"Indexed perceptual hashes for {file_path.name}: phash={phash}, dhash={dhash}, ahash={ahash}")

        except ImportError:
            logger.debug("Perceptual hashing not available")
        except Exception as e:
            logger.warning(f"Failed to calculate perceptual hashes: {e}")

    def _cleanup_search_index(self) -> None:
        """Clean up search index of removed files."""
        if not self.search_db:
            return

        try:
            # Get all indexed files
            indexed_files = self.search_db.get_all_file_paths()
            removed_count = 0

            # Check each file still exists
            for file_path in indexed_files:
                if not Path(file_path).exists():
                    # Remove from index
                    self.search_db.remove_asset(file_path)
                    removed_count += 1

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} missing files from search index")

        except Exception as e:
            logger.warning(f"Failed to clean up search index: {e}")
