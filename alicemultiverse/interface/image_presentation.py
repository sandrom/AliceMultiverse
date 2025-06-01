"""Image Presentation API for collaborative browsing with AI assistants."""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from io import BytesIO

from PIL import Image

from alicemultiverse.interface.models import (
    ImageSearchResult,
    PresentableImage,
    SelectionFeedback,
    SoftDeleteCategory
)
from alicemultiverse.storage.duckdb_cache import DuckDBSearchCache
import shutil
import json
from alicemultiverse.core.structured_logging import get_logger

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
        storage: Optional[DuckDBSearchCache] = None,
        cache_dir: Optional[Path] = None
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
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        similar_to: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        exclude_folders: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
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
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        if date_range and date_range[0] > date_range[1]:
            raise ValueError("Invalid date range: start date must be before end date")
        
        # Parse natural language query if provided
        if query:
            tags = self._parse_query_to_tags(query)
            query_interpretation = f"Tags: {', '.join(tags)}"
        else:
            query_interpretation = "All images"
        
        # Handle similarity search
        if similar_to:
            # TODO: Implement similarity search when embeddings are available
            logger.warning("Similarity search not yet implemented")
        
        # Combine exclusion folders
        all_excluded = list(self._exclusion_folders)
        if exclude_folders:
            all_excluded.extend(exclude_folders)
        
        # Convert tags to DuckDB format
        tag_dict = {}
        if tags:
            # Distribute tags across categories based on content
            for tag in tags:
                if tag in ["portrait", "landscape", "abstract", "cyberpunk", "fantasy"]:
                    tag_dict.setdefault("style", []).append(tag)
                elif tag in ["happy", "sad", "dramatic", "serene", "mysterious"]:
                    tag_dict.setdefault("mood", []).append(tag)
                else:
                    tag_dict.setdefault("subject", []).append(tag)
        
        # Search storage
        try:
            # Use sync method (DuckDBSearchCache doesn't have async methods)
            assets = self.storage.search_by_tags(tag_dict, limit=limit)
            
            # Apply exclusions and pagination manually
            filtered_assets = []
            for asset in assets:
                # Check if any location is in excluded folders
                locations = asset.get("locations", [])
                excluded = False
                for loc in locations:
                    # Handle both dict and string formats
                    if isinstance(loc, dict):
                        path = loc.get("path", "")
                    else:
                        path = str(loc)
                    if any(exc in path for exc in all_excluded):
                        excluded = True
                        break
                if not excluded:
                    filtered_assets.append(asset)
            
            # Apply pagination
            total_count = len(filtered_assets)
            paginated = filtered_assets[offset:offset + limit]
            
            result = {
                "images": paginated,
                "total_count": total_count
            }
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            result = {"images": [], "total_count": 0}
        
        # Convert to presentable images
        presentable_images = []
        for img_data in result.get("images", []):
            presentable = await self._create_presentable_image(img_data)
            presentable_images.append(presentable)
        
        # Generate suggestions
        suggestions = self._generate_search_suggestions(tags, result)
        
        return ImageSearchResult(
            images=presentable_images,
            total_count=result.get("total_count", len(presentable_images)),
            has_more=offset + limit < result.get("total_count", 0),
            query_interpretation=query_interpretation,
            suggestions=suggestions
        )
    
    async def track_selection(
        self,
        image_hash: str,
        selected: bool,
        reason: Optional[str] = None,
        session_id: Optional[str] = None
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
        
        # Get first available location
        locations = asset.get("locations", [])
        if not locations:
            raise FileNotFoundError(f"No file locations found for: {image_hash}")
        
        current_path = Path(locations[0]["path"])
        if not current_path.exists():
            raise FileNotFoundError(f"File not found: {current_path}")
        
        # Determine destination folder
        sorted_out_base = current_path.parent.parent / "sorted-out" / category.value
        sorted_out_base.mkdir(parents=True, exist_ok=True)
        
        new_path = sorted_out_base / current_path.name
        
        # Move file using shutil
        try:
            shutil.move(str(current_path), str(new_path))
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            raise
        
        # Update storage with new location
        self.storage.remove_location(image_hash, current_path)
        self.storage._add_file_location(image_hash, new_path, "local")
        
        # Save deletion record to local file
        try:
            with open(self.deletion_file, "a") as f:
                deletion_record = {
                    "image_hash": image_hash,
                    "original_path": str(current_path),
                    "new_path": str(new_path),
                    "reason": reason,
                    "category": category.value,
                    "timestamp": datetime.now().isoformat()
                }
                f.write(json.dumps(deletion_record) + "\n")
        except Exception as e:
            logger.error(f"Failed to save deletion record: {e}")
        
        # Add to exclusion list
        sorted_folder = f"sorted-out/{category.value}/"
        if sorted_folder not in self._exclusion_folders:
            self._exclusion_folders.append(sorted_folder)
        
        logger.info(f"Soft deleted {image_hash} to {new_path}: {reason}")
        
        return str(new_path)
    
    async def _create_presentable_image(self, img_data: Dict[str, Any]) -> PresentableImage:
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
    
    async def _generate_thumbnail(self, image_path: str, size: Tuple[int, int] = (256, 256)) -> str:
        """Generate base64 thumbnail for image.
        
        Args:
            image_path: Path to image file
            size: Thumbnail size
            
        Returns:
            Base64 data URL for thumbnail
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
            # Return placeholder
            return "data:image/jpeg;base64,/9j/4AAQ..."  # Placeholder
    
    async def _get_selection_history(self, image_hash: str) -> Dict[str, Any]:
        """Get selection history for an image.
        
        Args:
            image_hash: Image hash
            
        Returns:
            Selection information
        """
        # Read selection history from local file
        if not self.feedback_file.exists():
            return {"selected": False, "reason": None}
        
        try:
            # Find most recent selection for this image
            selected = False
            reason = None
            
            with open(self.feedback_file, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if record.get("image_hash") == image_hash:
                            selected = record.get("selected", False)
                            reason = record.get("reason")
                    except json.JSONDecodeError:
                        continue
            
            return {"selected": selected, "reason": reason}
        except Exception as e:
            logger.error(f"Failed to read selection history: {e}")
            return {"selected": False, "reason": None}
    
    def _parse_query_to_tags(self, query: str) -> List[str]:
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
    
    def _generate_search_suggestions(
        self,
        current_tags: Optional[List[str]],
        search_result: Dict[str, Any]
    ) -> List[str]:
        """Generate search refinement suggestions.
        
        Args:
            current_tags: Currently searched tags
            search_result: Current search results
            
        Returns:
            List of suggested refinements
        """
        suggestions = []
        
        # If too many results, suggest refinement
        if search_result.get("total_count", 0) > 100:
            suggestions.append("Try adding more specific tags to narrow results")
        
        # If few results, suggest broadening
        if search_result.get("total_count", 0) < 5:
            suggestions.append("Try removing some tags for more results")
        
        # Suggest related tags based on current tags
        if current_tags:
            # This would use tag co-occurrence data in production
            if "portrait" in current_tags:
                suggestions.append("Try adding 'closeup' or 'headshot'")
            if "landscape" in current_tags:
                suggestions.append("Try adding 'mountains' or 'ocean'")
        
        return suggestions[:3]  # Limit suggestions