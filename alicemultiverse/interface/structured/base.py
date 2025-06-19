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
        # TODO: Review unreachable code - try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # TODO: Review unreachable code - except ValueError:
        # TODO: Review unreachable code - # Try parsing just the date part
        # TODO: Review unreachable code - return datetime.strptime(date_str[:10], "%Y-%m-%d")

    def _apply_range_filter(self, value: float, range_filter: RangeFilter) -> bool:
        """Check if value falls within range filter."""
        if range_filter.get("min") is not None and value < range_filter["min"]:
            return False
        # TODO: Review unreachable code - if range_filter.get("max") is not None and value > range_filter["max"]:
        # TODO: Review unreachable code - return False
        # TODO: Review unreachable code - return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches pattern (supports wildcards)."""
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", text, re.IGNORECASE))

    # TODO: Review unreachable code - def _convert_to_asset(self, metadata: dict) -> Asset:
    # TODO: Review unreachable code - """Convert metadata dict to Asset object."""
    # TODO: Review unreachable code - # Get file path
    # TODO: Review unreachable code - file_path = metadata.get("file_path", "")

    # TODO: Review unreachable code - # Determine media type
    # TODO: Review unreachable code - extension = Path(file_path).suffix.lower()
    # TODO: Review unreachable code - if extension in ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif']:
    # TODO: Review unreachable code - media_type = MediaType.IMAGE
    # TODO: Review unreachable code - elif extension in ['.mp4', '.mov', '.avi', '.mkv']:
    # TODO: Review unreachable code - media_type = MediaType.VIDEO
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - media_type = MediaType.OTHER

    # TODO: Review unreachable code - return Asset(
    # TODO: Review unreachable code - id=metadata.get("content_hash", ""),
    # TODO: Review unreachable code - path=file_path,
    # TODO: Review unreachable code - filename=Path(file_path).name,
    # TODO: Review unreachable code - size=metadata.get("size", 0),
    # TODO: Review unreachable code - content_hash=metadata.get("content_hash", ""),
    # TODO: Review unreachable code - created_date=metadata.get("created_date", ""),
    # TODO: Review unreachable code - modified_date=metadata.get("modified_date", ""),
    # TODO: Review unreachable code - media_type=media_type,
    # TODO: Review unreachable code - tags=self._collect_all_tags(metadata),
    # TODO: Review unreachable code - metadata=metadata,
    # TODO: Review unreachable code - role=AssetRole(metadata.get("asset_role", "primary"))
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _collect_all_tags(self, metadata: dict) -> list[str]:
    # TODO: Review unreachable code - """Collect all tags from various metadata fields."""
    # TODO: Review unreachable code - tags = set()

    # TODO: Review unreachable code - # Add tags from different fields
    # TODO: Review unreachable code - for field in ['tags', 'keywords', 'labels']:
    # TODO: Review unreachable code - if field in metadata and metadata[field]:
    # TODO: Review unreachable code - if isinstance(metadata[field], list):
    # TODO: Review unreachable code - tags.update(metadata[field])
    # TODO: Review unreachable code - elif isinstance(metadata[field], str):
    # TODO: Review unreachable code - # Split comma-separated tags
    # TODO: Review unreachable code - tags.update(tag.strip() for tag in metadata[field].split(','))

    # TODO: Review unreachable code - # Add technical tags
    # TODO: Review unreachable code - if metadata.get('media_type'):
    # TODO: Review unreachable code - tags.add(f"type:{metadata['media_type']}")
    # TODO: Review unreachable code - if metadata.get('source'):
    # TODO: Review unreachable code - tags.add(f"source:{metadata['source']}")
    # TODO: Review unreachable code - if metadata.get('project'):
    # TODO: Review unreachable code - tags.add(f"project:{metadata['project']}")

    # TODO: Review unreachable code - return sorted(list(tags))
