"""Asset discovery and tracking system."""

import logging
from datetime import datetime
from pathlib import Path

# PostgreSQL removed - SQLAlchemy and database imports no longer available
# from sqlalchemy.orm import Session

from ..core.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
# from ..database import Asset, AssetPath, get_session
from .hashing import calculate_content_hash, get_or_calculate_content_hash

logger = logging.getLogger(__name__)


class AssetDiscovery:
    """Handles finding and tracking assets regardless of location.
    
    Note: This class requires PostgreSQL which has been removed.
    Most methods will return None or empty results.
    """

    def __init__(self, search_paths: list[Path] | None = None):
        """Initialize asset discovery.

        Args:
            search_paths: Additional paths to search for assets
        """
        self.search_paths = search_paths or []
        # Add common locations
        self.search_paths.extend(
            [
                Path.home() / "Pictures" / "AliceMultiverse",
                Path.home() / "Documents" / "AliceMultiverse",
                Path.home() / "organized",
                Path("/inbox"),
                Path("/organized"),
            ]
        )
        # Remove non-existent paths
        self.search_paths = [p for p in self.search_paths if p.exists()]
        logger.info(f"Asset discovery initialized with {len(self.search_paths)} search paths")
        logger.warning("Asset discovery is non-functional without PostgreSQL")

    def find_by_content_hash(self, content_hash: str) -> Path | None:
        """Find asset by content hash.

        PostgreSQL removed - this method searches filesystem only.

        Args:
            content_hash: Content hash to search for

        Returns:
            Path to file if found, None otherwise
        """
        # Search filesystem only since database is not available
        for search_path in self.search_paths:
            for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
                for file_path in search_path.rglob(f"*{ext}"):
                    try:
                        if get_or_calculate_content_hash(file_path) == content_hash:
                            return file_path
                    except Exception as e:
                        logger.debug(f"Error checking {file_path}: {e}")
        
        return None

    def track_asset(
        self,
        file_path: Path,
        content_hash: str | None = None,
        metadata: dict | None = None,
        **kwargs,
    ) -> str:
        """Track an asset in the system.

        PostgreSQL removed - this method only calculates hash.

        Args:
            file_path: Path to the asset file
            content_hash: Optional pre-calculated content hash
            metadata: Optional metadata
            **kwargs: Additional asset attributes

        Returns:
            Content hash
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Calculate content hash if not provided
        if not content_hash:
            content_hash = calculate_content_hash(file_path)

        logger.info(f"Tracked asset: {content_hash} at {file_path}")
        logger.debug("Database tracking skipped - PostgreSQL removed")
        
        return content_hash

    def update_asset_location(self, content_hash: str, new_path: Path) -> bool:
        """Update asset location.

        PostgreSQL removed - this method is non-functional.

        Args:
            content_hash: Content hash of the asset
            new_path: New file path

        Returns:
            False (database not available)
        """
        logger.warning(f"Cannot update asset location for {content_hash} - PostgreSQL removed")
        return False

    def find_duplicates(self) -> dict[str, list[Path]]:
        """Find duplicate assets by content hash.

        Searches filesystem only since database is not available.

        Returns:
            Dict mapping content hash to list of file paths
        """
        duplicates = {}
        seen_hashes = {}

        for search_path in self.search_paths:
            for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
                for file_path in search_path.rglob(f"*{ext}"):
                    try:
                        content_hash = get_or_calculate_content_hash(file_path)
                        if content_hash in seen_hashes:
                            if content_hash not in duplicates:
                                duplicates[content_hash] = [seen_hashes[content_hash]]
                            duplicates[content_hash].append(file_path)
                        else:
                            seen_hashes[content_hash] = file_path
                    except Exception as e:
                        logger.debug(f"Error processing {file_path}: {e}")

        return duplicates

    def find_moved_assets(self) -> list:
        """Find assets that may have been moved.

        PostgreSQL removed - this method is non-functional.

        Returns:
            Empty list (database not available)
        """
        logger.warning("Cannot find moved assets - PostgreSQL removed")
        return []

    def scan_directory(self, directory: Path, recursive: bool = True) -> int:
        """Scan directory for new assets.

        PostgreSQL removed - this method only counts files.

        Args:
            directory: Directory to scan
            recursive: Whether to scan recursively

        Returns:
            Number of media files found
        """
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return 0

        count = 0
        pattern = "**/*" if recursive else "*"

        for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
            for file_path in directory.glob(f"{pattern}{ext}"):
                if file_path.is_file():
                    count += 1

        logger.info(f"Found {count} media files in {directory}")
        return count

    def get_asset_history(self, content_hash: str) -> list[dict]:
        """Get location history for an asset.

        PostgreSQL removed - this method is non-functional.

        Returns:
            Empty list (database not available)
        """
        logger.warning(f"Cannot get asset history for {content_hash} - PostgreSQL removed")
        return []