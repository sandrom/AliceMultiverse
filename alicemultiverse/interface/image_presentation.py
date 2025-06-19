"""Image Presentation API for collaborative browsing with AI assistants."""

import base64
import json
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from alicemultiverse.core.structured_logging import get_logger
from alicemultiverse.interface.models import (
    ImageSearchResult,
    PresentableImage,
    SelectionFeedback,
    SoftDeleteCategory,
)
from alicemultiverse.storage.unified_duckdb import DuckDBSearchCache

logger = get_logger(__name__)


class ImagePresentationAPI:
    """API for presenting images in AI chat interfaces."""

    # Default excluded folders
    DEFAULT_EXCLUSIONS = [
        "sorted-out/",
        ".metadata/",
        ".cache/",
        "__pycache__/"
    ]

    def __init__(
        self,
        storage: DuckDBSearchCache | None = None,
        cache_dir: Path | None = None
    ):
        """Initialize the Image Presentation API.

        Args:
            storage: Storage backend (DuckDB)
            cache_dir: Directory for caching selection feedback
        """
        self.storage = storage or DuckDBSearchCache()
        self._exclusion_folders = list(self.DEFAULT_EXCLUSIONS)

        # Create cache directory for selection feedback
        self.cache_dir = cache_dir or Path.home() / ".cache" / "alice" / "selections"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Selection feedback file
        self.feedback_file = self.cache_dir / "selection_feedback.jsonl"
        self.deletion_file = self.cache_dir / "deletion_records.jsonl"

    async def search_images(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        similar_to: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        exclude_folders: list[str] | None = None,
        date_range: tuple[datetime, datetime] | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> ImageSearchResult:
        """Search images based on various criteria.

        Args:
            query: Natural language search query
            tags: Tags to search for
            similar_to: Image hashes to find similar images
            exclude_tags: Tags to exclude
            exclude_folders: Folders to exclude from search
            date_range: Date range filter
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            ImageSearchResult with presentable images

        Raises:
            ValueError: Invalid parameters
        """
        # Validate parameters
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        # TODO: Review unreachable code - if offset < 0:
        # TODO: Review unreachable code - raise ValueError("Offset must be non-negative")
        # TODO: Review unreachable code - if date_range and date_range[0] > date_range[1]:
        # TODO: Review unreachable code - raise ValueError("Invalid date range: start date must be before end date")

        # TODO: Review unreachable code - # Parse natural language query if provided
        # TODO: Review unreachable code - if query:
        # TODO: Review unreachable code - tags = self._parse_query_to_tags(query)
        # TODO: Review unreachable code - query_interpretation = f"Tags: {', '.join(tags)}"
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - query_interpretation = "All images"

        # TODO: Review unreachable code - # Handle similarity search
        # TODO: Review unreachable code - if similar_to:
        # TODO: Review unreachable code - # TODO: Implement similarity search when embeddings are available
        # TODO: Review unreachable code - logger.warning("Similarity search not yet implemented")

        # TODO: Review unreachable code - # Combine exclusion folders
        # TODO: Review unreachable code - all_excluded = list(self._exclusion_folders)
        # TODO: Review unreachable code - if exclude_folders:
        # TODO: Review unreachable code - all_excluded.extend(exclude_folders)

        # TODO: Review unreachable code - # Convert tags to DuckDB format
        # TODO: Review unreachable code - tag_dict = {}
        # TODO: Review unreachable code - if tags:
        # TODO: Review unreachable code - # Distribute tags across categories based on content
        # TODO: Review unreachable code - for tag in tags:
        # TODO: Review unreachable code - if tag in ["portrait", "landscape", "abstract", "cyberpunk", "fantasy"]:
        # TODO: Review unreachable code - tag_dict.setdefault("style", []).append(tag)
        # TODO: Review unreachable code - elif tag in ["happy", "sad", "dramatic", "serene", "mysterious"]:
        # TODO: Review unreachable code - tag_dict.setdefault("mood", []).append(tag)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - tag_dict.setdefault("subject", []).append(tag)

        # TODO: Review unreachable code - # Search storage
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - # Use sync method (DuckDBSearchCache doesn't have async methods)
        # TODO: Review unreachable code - assets = self.storage.search_by_tags(tag_dict, limit=limit)

        # TODO: Review unreachable code - # Apply exclusions and pagination manually
        # TODO: Review unreachable code - filtered_assets = []
        # TODO: Review unreachable code - for asset in assets:
        # TODO: Review unreachable code - # Check if any location is in excluded folders
        # TODO: Review unreachable code - locations = asset.get("locations", [])
        # TODO: Review unreachable code - excluded = False
        # TODO: Review unreachable code - for loc in locations:
        # TODO: Review unreachable code - # Handle both dict and string formats
        # TODO: Review unreachable code - if isinstance(loc, dict):
        # TODO: Review unreachable code - path = loc.get("path", "")
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - path = str(loc)
        # TODO: Review unreachable code - if any(exc in path for exc in all_excluded):
        # TODO: Review unreachable code - excluded = True
        # TODO: Review unreachable code - break
        # TODO: Review unreachable code - if not excluded:
        # TODO: Review unreachable code - filtered_assets.append(asset)

        # TODO: Review unreachable code - # Apply pagination
        # TODO: Review unreachable code - total_count = len(filtered_assets)
        # TODO: Review unreachable code - paginated = filtered_assets[offset:offset + limit]

        # TODO: Review unreachable code - result = {
        # TODO: Review unreachable code - "images": paginated,
        # TODO: Review unreachable code - "total_count": total_count
        # TODO: Review unreachable code - }
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Search failed: {e}", exc_info=True)
        # TODO: Review unreachable code - result = {"images": [], "total_count": 0}

        # TODO: Review unreachable code - # Convert to presentable images
        # TODO: Review unreachable code - presentable_images = []
        # TODO: Review unreachable code - for img_data in result.get("images", []):
        # TODO: Review unreachable code - presentable = await self._create_presentable_image(img_data)
        # TODO: Review unreachable code - presentable_images.append(presentable)

        # TODO: Review unreachable code - # Generate suggestions
        # TODO: Review unreachable code - suggestions = self._generate_search_suggestions(tags, result)

        # TODO: Review unreachable code - return ImageSearchResult(
        # TODO: Review unreachable code - images=presentable_images,
        # TODO: Review unreachable code - total_count=result.get("total_count", len(presentable_images)),
        # TODO: Review unreachable code - has_more=offset + limit < result.get("total_count", 0),
        # TODO: Review unreachable code - query_interpretation=query_interpretation,
        # TODO: Review unreachable code - suggestions=suggestions
        # TODO: Review unreachable code - )

    async def track_selection(
        self,
        image_hash: str,
        selected: bool,
        reason: str | None = None,
        session_id: str | None = None
    ) -> None:
        """Track user's selection decision and reasoning.

        Args:
            image_hash: Hash of the selected/rejected image
            selected: Whether image was selected
            reason: User's reason for selection/rejection
            session_id: Optional session identifier
        """
        feedback = SelectionFeedback(
            image_hash=image_hash,
            selected=selected,
            reason=reason,
            session_id=session_id
        )

        # Save to local file (append mode)
        try:
            with open(self.feedback_file, "a") as f:
                feedback_dict = {
                    "image_hash": feedback.image_hash,
                    "selected": feedback.selected,
                    "reason": feedback.reason,
                    "session_id": feedback.session_id,
                    "timestamp": feedback.timestamp.isoformat() if feedback.timestamp else datetime.now().isoformat()
                }
                f.write(json.dumps(feedback_dict) + "\n")
        except Exception as e:
            logger.error(f"Failed to save selection feedback: {e}")

        logger.info(
            f"Tracked selection: {image_hash} - "
            f"{'selected' if selected else 'rejected'} - {reason}"
        )

    async def soft_delete_image(
        self,
        image_hash: str,
        reason: str,
        category: SoftDeleteCategory = SoftDeleteCategory.REJECTED
    ) -> str:
        """Move image to sorted-out folder based on category.

        Args:
            image_hash: Hash of image to soft delete
            reason: Reason for deletion
            category: Category of deletion

        Returns:
            New path in sorted-out structure

        Raises:
            FileNotFoundError: Image not found
        """
        # Get asset data from storage
        asset = self.storage.get_asset_by_hash(image_hash)
        if not asset:
            raise FileNotFoundError(f"Image not found: {image_hash}")

        # TODO: Review unreachable code - # Get first available location
        # TODO: Review unreachable code - locations = asset.get("locations", [])
        # TODO: Review unreachable code - if not locations:
        # TODO: Review unreachable code - raise FileNotFoundError(f"No file locations found for: {image_hash}")

        # TODO: Review unreachable code - current_path = Path(locations[0]["path"])
        # TODO: Review unreachable code - if not current_path.exists():
        # TODO: Review unreachable code - raise FileNotFoundError(f"File not found: {current_path}")

        # TODO: Review unreachable code - # Determine destination folder
        # TODO: Review unreachable code - sorted_out_base = current_path.parent.parent / "sorted-out" / category.value
        # TODO: Review unreachable code - sorted_out_base.mkdir(parents=True, exist_ok=True)

        # TODO: Review unreachable code - new_path = sorted_out_base / current_path.name

        # TODO: Review unreachable code - # Move file using shutil
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - shutil.move(str(current_path), str(new_path))
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Failed to move file: {e}")
        # TODO: Review unreachable code - raise

        # TODO: Review unreachable code - # Update storage with new location
        # TODO: Review unreachable code - self.storage.remove_location(image_hash, current_path)
        # TODO: Review unreachable code - self.storage._add_file_location(image_hash, new_path, "local")

        # TODO: Review unreachable code - # Save deletion record to local file
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - with open(self.deletion_file, "a") as f:
        # TODO: Review unreachable code - deletion_record = {
        # TODO: Review unreachable code - "image_hash": image_hash,
        # TODO: Review unreachable code - "original_path": str(current_path),
        # TODO: Review unreachable code - "new_path": str(new_path),
        # TODO: Review unreachable code - "reason": reason,
        # TODO: Review unreachable code - "category": category.value,
        # TODO: Review unreachable code - "timestamp": datetime.now().isoformat()
        # TODO: Review unreachable code - }
        # TODO: Review unreachable code - f.write(json.dumps(deletion_record) + "\n")
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Failed to save deletion record: {e}")

        # TODO: Review unreachable code - # Add to exclusion list
        # TODO: Review unreachable code - sorted_folder = f"sorted-out/{category.value}/"
        # TODO: Review unreachable code - if sorted_folder not in self._exclusion_folders:
        # TODO: Review unreachable code - self._exclusion_folders.append(sorted_folder)

        # TODO: Review unreachable code - logger.info(f"Soft deleted {image_hash} to {new_path}: {reason}")

        # TODO: Review unreachable code - return str(new_path)

    async def _create_presentable_image(self, img_data: dict[str, Any]) -> PresentableImage:
        """Convert raw image data to presentable format.

        Args:
            img_data: Raw image data from storage

        Returns:
            PresentableImage ready for display
        """
        # Get first available file path
        locations = img_data.get("locations", [])
        file_path = locations[0]["path"] if locations else ""

        # Generate thumbnail if needed
        thumbnail_url = await self._generate_thumbnail(file_path)

        # Get selection history
        selection_info = await self._get_selection_history(img_data.get("content_hash", ""))

        # Extract tags from nested structure
        tags_data = img_data.get("tags", {})
        all_tags = []
        for category, tag_list in tags_data.items():
            if isinstance(tag_list, list):
                all_tags.extend(tag_list)

        # Extract understanding data
        understanding = img_data.get("understanding", {})
        if isinstance(understanding, dict):
            description = understanding.get("description", "")
        else:
            description = ""

        generation = img_data.get("generation", {})
        if isinstance(generation, dict):
            provider = generation.get("provider", "unknown")
        else:
            provider = "unknown"

        return PresentableImage(
            hash=img_data.get("content_hash", ""),
            path=file_path,
            thumbnail_url=thumbnail_url,
            display_url=f"file://{file_path}",
            tags=all_tags,
            source=provider,
            created_date=img_data.get("created_at", datetime.now()),
            description=description,
            mood=tags_data.get("mood", []),
            style=tags_data.get("style", []),
            colors=tags_data.get("color", []),
            previously_selected=selection_info.get("selected", False),
            selection_reason=selection_info.get("reason"),
            dimensions=(0, 0),  # Would need to extract from file
            file_size=img_data.get("file_size", 0)
        )

    async def _generate_thumbnail(self, image_path: str, size: tuple[int, int] = (256, 256)) -> str:
        """Generate base64 thumbnail for image.

        Args:
            image_path: Path to image file
            size: Thumbnail size

        Returns:
            Base64 data URL for thumbnail
        """
        # TODO: Review unreachable code - try:
            # Open and resize image
        with Image.open(image_path) as img:
                # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

                # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)

                # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            base64_data = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/jpeg;base64,{base64_data}"
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
        # TODO: Review unreachable code - # Return placeholder
        # TODO: Review unreachable code - return "data:image/jpeg;base64,/9j/4AAQ..."  # Placeholder

    async def _get_selection_history(self, image_hash: str) -> dict[str, Any]:
        """Get selection history for an image.

        Args:
            image_hash: Image hash

        Returns:
            Selection information
        """
        # Read selection history from local file
        if not self.feedback_file.exists():
            return {"selected": False, "reason": None}

        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - # Find most recent selection for this image
        # TODO: Review unreachable code - selected = False
        # TODO: Review unreachable code - reason = None

        # TODO: Review unreachable code - with open(self.feedback_file) as f:
        # TODO: Review unreachable code - for line in f:
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - record = json.loads(line.strip())
        # TODO: Review unreachable code - if record.get("image_hash") == image_hash:
        # TODO: Review unreachable code - selected = record.get("selected", False)
        # TODO: Review unreachable code - reason = record.get("reason")
        # TODO: Review unreachable code - except json.JSONDecodeError:
        # TODO: Review unreachable code - continue

        # TODO: Review unreachable code - return {"selected": selected, "reason": reason}
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Failed to read selection history: {e}")
        # TODO: Review unreachable code - return {"selected": False, "reason": None}

    def _parse_query_to_tags(self, query: str) -> list[str]:
        """Parse natural language query to tags.

        Args:
            query: Natural language query

        Returns:
            List of extracted tags
        """
        # Simple implementation - split on spaces and common words
        # In production, this would use NLP
        words = query.lower().split()

        # Remove common words
        stop_words = {"with", "and", "or", "the", "a", "an", "in", "on", "at"}
        tags = [w for w in words if w not in stop_words]

        return tags

    # TODO: Review unreachable code - def _generate_search_suggestions(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - current_tags: list[str] | None,
    # TODO: Review unreachable code - search_result: dict[str, Any]
    # TODO: Review unreachable code - ) -> list[str]:
    # TODO: Review unreachable code - """Generate search refinement suggestions.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - current_tags: Currently searched tags
    # TODO: Review unreachable code - search_result: Current search results

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of suggested refinements
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - suggestions = []

    # TODO: Review unreachable code - # If too many results, suggest refinement
    # TODO: Review unreachable code - if search_result.get("total_count", 0) > 100:
    # TODO: Review unreachable code - suggestions.append("Try adding more specific tags to narrow results")

    # TODO: Review unreachable code - # If few results, suggest broadening
    # TODO: Review unreachable code - if search_result.get("total_count", 0) < 5:
    # TODO: Review unreachable code - suggestions.append("Try removing some tags for more results")

    # TODO: Review unreachable code - # Suggest related tags based on current tags
    # TODO: Review unreachable code - if current_tags:
    # TODO: Review unreachable code - # This would use tag co-occurrence data in production
    # TODO: Review unreachable code - if current_tags is not None and "portrait" in current_tags:
    # TODO: Review unreachable code - suggestions.append("Try adding 'closeup' or 'headshot'")
    # TODO: Review unreachable code - if current_tags is not None and "landscape" in current_tags:
    # TODO: Review unreachable code - suggestions.append("Try adding 'mountains' or 'ocean'")

    # TODO: Review unreachable code - return suggestions[:3]  # Limit suggestions
