"""Base class for natural language interface operations."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ...assets.metadata.models import AssetRole
from ...core.config import load_config
from ...organizer.enhanced_organizer import EnhancedMediaOrganizer
from ...projects import ProjectService
from ..models import AssetInfo

logger = logging.getLogger(__name__)


# Since AliceResponse is a TypedDict, we need to create dicts not instances
def AliceResponse(success: bool, message: str, data: Any = None, error: str = None) -> dict:
    """Create an AliceResponse dict."""
    return {
        "success": success,
        "message": message,
        "data": data,
        "error": error
    }


class NaturalInterfaceBase:
    """Base class with common functionality for natural language interface operations."""

    def __init__(self, config_path: Path | None = None):
        """Initialize natural language interface.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path)
        self.config.enhanced_metadata = True  # Always use enhanced metadata
        self.organizer = None
        self.initialization_error = None

        try:
            self._ensure_organizer()
        except Exception as e:
            # Store error for later - allow interface to be created
            self.initialization_error = e
            logger.warning(f"Failed to initialize organizer: {e}")

        self.asset_repo = None
        self.project_repo = None
        # Initialize project service with config
        self.project_service = ProjectService(config=self.config)
        logger.info("Running in file-based mode")

    def _ensure_organizer(self) -> None:
        """Ensure organizer is initialized."""
        if not self.organizer:
            self.organizer = EnhancedMediaOrganizer(self.config)
            # Ensure search engine is initialized
            if not self.organizer.search_engine:
                self.organizer._update_search_engine()

    def _parse_time_reference(self, time_ref: str) -> datetime | None:
        """Parse natural language time references.

        Args:
            time_ref: Natural language time like "last week", "yesterday"

        Returns:
            Datetime object or None
        """
        now = datetime.now()
        time_ref = time_ref.lower()

        if "yesterday" in time_ref:
            return now - timedelta(days=1)
        elif "last week" in time_ref:
            return now - timedelta(weeks=1)
        elif "last month" in time_ref:
            return now - timedelta(days=30)
        elif "today" in time_ref:
            return now.replace(hour=0, minute=0, second=0)

        # Try to parse month names
        months = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
        for i, month in enumerate(months):
            if month in time_ref:
                # Assume current year
                return datetime(now.year, i + 1, 1)

        return None

    def _simplify_asset_info(self, asset: dict) -> AssetInfo:
        """Convert full metadata to simplified info for AI.

        Args:
            asset: Full asset metadata

        Returns:
            Simplified asset information
        """
        # Combine all tags
        all_tags = (
            asset.get("style_tags", [])
            + asset.get("mood_tags", [])
            + asset.get("subject_tags", [])
            + asset.get("custom_tags", [])
        )

        # Build relationships
        relationships = {}
        if asset.get("parent_id"):
            relationships["parent"] = [asset["parent_id"]]
        if asset.get("similar_to"):
            relationships["similar"] = asset["similar_to"]
        if asset.get("grouped_with"):
            relationships["grouped"] = asset["grouped_with"]

        return {
            "id": asset.get("asset_id", asset.get("file_hash", "unknown")),
            "filename": asset.get("file_name", asset.get("filename", "unknown")),
            "prompt": asset.get("prompt"),
            "tags": all_tags,
            "quality_stars": asset.get("quality_stars", asset.get("quality_star")),
            "role": (
                asset.get("role", AssetRole.WIP).value
                if hasattr(asset.get("role"), "value")
                else str(asset.get("role", "wip"))
            ),
            "created": asset.get("created_at", asset.get("date_taken", datetime.now().isoformat())),
            "source": asset.get("source_type", asset.get("ai_source", "unknown")),
            "relationships": relationships,
        }

    def _persist_organized_assets(self) -> None:
        """Persist any changes to assets."""
        try:
            if self.asset_repo:
                # Repository mode - not implemented
                logger.info("Database persistence not available in file mode")
            else:
                # File-based persistence happens automatically
                pass
        except Exception as e:
            logger.error(f"Failed to persist assets: {e}")

    def _search_database(
        self,
        query: str | None = None,
        filters: dict | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Search database with filters.

        Args:
            query: Optional text query
            filters: Optional filters
            limit: Maximum results
            offset: Results offset

        Returns:
            List of matching assets
        """
        try:
            # For file-based mode, we need to search through metadata
            all_metadata = self.organizer.metadata_cache.get_all_metadata()
            results = []

            for file_path, metadata in all_metadata.items():
                # Apply filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key == "roles" and value:
                            # Check if asset role matches any in the list
                            asset_role = metadata.get("role", "wip")
                            if asset_role not in value:
                                match = False
                                break
                        elif key == "quality_min":
                            if metadata.get("quality_stars", 0) < value:
                                match = False
                                break
                        elif key == "sources" and value:
                            if metadata.get("source_type", "unknown") not in value:
                                match = False
                                break

                    if not match:
                        continue

                # Apply text search if query provided
                if query:
                    query_lower = query.lower()
                    searchable_text = " ".join(
                        [
                            str(metadata.get("prompt", "")),
                            str(metadata.get("file_name", "")),
                            " ".join(metadata.get("style_tags", [])),
                            " ".join(metadata.get("mood_tags", [])),
                            " ".join(metadata.get("subject_tags", [])),
                            " ".join(metadata.get("custom_tags", [])),
                        ]
                    ).lower()

                    if query_lower not in searchable_text:
                        continue

                # Add file_path to metadata for reference
                metadata["file_path"] = str(file_path)
                results.append(metadata)

            # Apply limit and offset
            return results[offset : offset + limit]

        except Exception as e:
            logger.error(f"Database search failed: {e}")
            return []
