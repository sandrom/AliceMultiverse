"""Base class for structured interface operations."""

import logging
import re
from datetime import datetime
from pathlib import Path

from ...core.config import load_config
from ...organizer.enhanced_organizer import EnhancedMediaOrganizer
from ...projects.service import ProjectService
from ...selections.service import SelectionService
from ..rate_limiter import RateLimiter
from ..search_handler import OptimizedSearchHandler
from ..structured_models import (
    Asset,
    AssetRole,
    MediaType,
    RangeFilter,
)

logger = logging.getLogger(__name__)


class StructuredInterfaceBase:
    """Base class with common functionality for structured interface operations."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize base structured interface.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path)
        self.config.enhanced_metadata = True  # Always use enhanced metadata
        self.organizer = None
        self._ensure_organizer()

        # Initialize rate limiter
        self.rate_limiter = RateLimiter()

        # Initialize optimized search handler with config
        self.search_handler = OptimizedSearchHandler(config=self.config)

        # Initialize project and selection services
        self.project_service = ProjectService(config=self.config)
        self.selection_service = SelectionService(project_service=self.project_service)

    def _ensure_organizer(self) -> None:
        """Ensure organizer is initialized."""
        if not self.organizer:
            self.organizer = EnhancedMediaOrganizer(self.config)

    def _parse_iso_date(self, date_str: str) -> datetime:
        """Parse ISO 8601 date string."""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            # Try parsing just the date part
            return datetime.strptime(date_str[:10], "%Y-%m-%d")

    def _apply_range_filter(self, value: float, range_filter: RangeFilter) -> bool:
        """Check if value falls within range filter."""
        if range_filter.get("min") is not None and value < range_filter["min"]:
            return False
        if range_filter.get("max") is not None and value > range_filter["max"]:
            return False
        return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches pattern (supports wildcards)."""
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", text, re.IGNORECASE))

    def _convert_to_asset(self, metadata: dict) -> Asset:
        """Convert metadata dict to Asset object."""
        # Get file path
        file_path = metadata.get("file_path", "")

        # Determine media type
        extension = Path(file_path).suffix.lower()
        if extension in ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif']:
            media_type = MediaType.IMAGE
        elif extension in ['.mp4', '.mov', '.avi', '.mkv']:
            media_type = MediaType.VIDEO
        else:
            media_type = MediaType.OTHER

        return Asset(
            id=metadata.get("content_hash", ""),
            path=file_path,
            filename=Path(file_path).name,
            size=metadata.get("size", 0),
            content_hash=metadata.get("content_hash", ""),
            created_date=metadata.get("created_date", ""),
            modified_date=metadata.get("modified_date", ""),
            media_type=media_type,
            tags=self._collect_all_tags(metadata),
            metadata=metadata,
            role=AssetRole(metadata.get("asset_role", "primary"))
        )

    def _collect_all_tags(self, metadata: dict) -> list[str]:
        """Collect all tags from various metadata fields."""
        tags = set()

        # Add tags from different fields
        for field in ['tags', 'keywords', 'labels']:
            if field in metadata and metadata[field]:
                if isinstance(metadata[field], list):
                    tags.update(metadata[field])
                elif isinstance(metadata[field], str):
                    # Split comma-separated tags
                    tags.update(tag.strip() for tag in metadata[field].split(','))

        # Add technical tags
        if metadata.get('media_type'):
            tags.add(f"type:{metadata['media_type']}")
        if metadata.get('source'):
            tags.add(f"source:{metadata['source']}")
        if metadata.get('project'):
            tags.add(f"project:{metadata['project']}")

        return sorted(list(tags))
