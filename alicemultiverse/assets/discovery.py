"""Asset discovery and tracking system."""

import logging
from pathlib import Path

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

        Search filesystem for media assets.

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

    # TODO: Review unreachable code - def track_asset(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - file_path: Path,
    # TODO: Review unreachable code - content_hash: str | None = None,
    # TODO: Review unreachable code - metadata: dict | None = None,
    # TODO: Review unreachable code - **kwargs,
    # TODO: Review unreachable code - ) -> str:
    # TODO: Review unreachable code - """Track an asset in the system.

    # TODO: Review unreachable code - PostgreSQL removed - this method only calculates hash.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to the asset file
    # TODO: Review unreachable code - content_hash: Optional pre-calculated content hash
    # TODO: Review unreachable code - metadata: Optional metadata
    # TODO: Review unreachable code - **kwargs: Additional asset attributes

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Content hash
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not file_path.exists():
    # TODO: Review unreachable code - raise FileNotFoundError(f"File not found: {file_path}")

    # TODO: Review unreachable code - # Calculate content hash if not provided
    # TODO: Review unreachable code - if not content_hash:
    # TODO: Review unreachable code - content_hash = calculate_content_hash(file_path)

    # TODO: Review unreachable code - logger.info(f"Tracked asset: {content_hash} at {file_path}")
    # TODO: Review unreachable code - logger.debug("Database tracking skipped - PostgreSQL removed")

    # TODO: Review unreachable code - return content_hash

    # TODO: Review unreachable code - def update_asset_location(self, content_hash: str, new_path: Path) -> bool:
    # TODO: Review unreachable code - """Update asset location.

    # TODO: Review unreachable code - PostgreSQL removed - this method is non-functional.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - content_hash: Content hash of the asset
    # TODO: Review unreachable code - new_path: New file path

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - False (database not available)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - logger.warning(f"Cannot update asset location for {content_hash} - PostgreSQL removed")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - def find_duplicates(self) -> dict[str, list[Path]]:
    # TODO: Review unreachable code - """Find duplicate assets by content hash.

    # TODO: Review unreachable code - Searches filesystem only since database is not available.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dict mapping content hash to list of file paths
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - duplicates = {}
    # TODO: Review unreachable code - seen_hashes = {}

    # TODO: Review unreachable code - for search_path in self.search_paths:
    # TODO: Review unreachable code - for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
    # TODO: Review unreachable code - for file_path in search_path.rglob(f"*{ext}"):
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - content_hash = get_or_calculate_content_hash(file_path)
    # TODO: Review unreachable code - if content_hash in seen_hashes:
    # TODO: Review unreachable code - if content_hash not in duplicates:
    # TODO: Review unreachable code - duplicates[content_hash] = [seen_hashes[content_hash]]
    # TODO: Review unreachable code - duplicates[content_hash].append(file_path)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - seen_hashes[content_hash] = file_path
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.debug(f"Error processing {file_path}: {e}")

    # TODO: Review unreachable code - return duplicates

    # TODO: Review unreachable code - def find_moved_assets(self) -> list:
    # TODO: Review unreachable code - """Find assets that may have been moved.

    # TODO: Review unreachable code - PostgreSQL removed - this method is non-functional.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Empty list (database not available)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - logger.warning("Cannot find moved assets - PostgreSQL removed")
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - def scan_directory(self, directory: Path, recursive: bool = True) -> int:
    # TODO: Review unreachable code - """Scan directory for new assets.

    # TODO: Review unreachable code - PostgreSQL removed - this method only counts files.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - directory: Directory to scan
    # TODO: Review unreachable code - recursive: Whether to scan recursively

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Number of media files found
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not directory.exists():
    # TODO: Review unreachable code - logger.warning(f"Directory does not exist: {directory}")
    # TODO: Review unreachable code - return 0

    # TODO: Review unreachable code - count = 0
    # TODO: Review unreachable code - pattern = "**/*" if recursive else "*"

    # TODO: Review unreachable code - for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
    # TODO: Review unreachable code - for file_path in directory.glob(f"{pattern}{ext}"):
    # TODO: Review unreachable code - if file_path.is_file():
    # TODO: Review unreachable code - count += 1

    # TODO: Review unreachable code - logger.info(f"Found {count} media files in {directory}")
    # TODO: Review unreachable code - return count

    # TODO: Review unreachable code - def get_asset_history(self, content_hash: str) -> list[dict]:
    # TODO: Review unreachable code - """Get location history for an asset.

    # TODO: Review unreachable code - PostgreSQL removed - this method is non-functional.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Empty list (database not available)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - logger.warning(f"Cannot get asset history for {content_hash} - PostgreSQL removed")
    # TODO: Review unreachable code - return []
