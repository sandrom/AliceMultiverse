"""Asset discovery and tracking system."""

import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ..database import Asset, AssetPath, get_session
from .hashing import calculate_content_hash, get_or_calculate_content_hash

logger = logging.getLogger(__name__)


class AssetDiscovery:
    """Handles finding and tracking assets regardless of location."""

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
                Path.cwd() / "organized",
                Path.cwd() / "inbox",
            ]
        )

    def find_asset(self, content_hash: str) -> Path | None:
        """Find an asset by content hash.

        Checks:
        1. Cached file_path in database
        2. Known historical paths
        3. Scans common locations if not found

        Args:
            content_hash: Content hash of the asset

        Returns:
            Path to the asset if found, None otherwise
        """
        with get_session() as session:
            asset = session.query(Asset).filter_by(content_hash=content_hash).first()
            if not asset:
                return None

            # 1. Check cached file_path first
            if asset.file_path:
                path = Path(asset.file_path)
                if path.exists() and self._verify_hash(path, content_hash):
                    logger.debug(f"Found asset at cached path: {path}")
                    return path

            # 2. Check known historical paths
            for known_path in asset.known_paths:
                if not known_path.is_active:
                    continue

                path = Path(known_path.file_path)
                if path.exists() and self._verify_hash(path, content_hash):
                    logger.debug(f"Found asset at historical path: {path}")
                    # Update cache
                    self._update_asset_location(session, asset, path)
                    return path

            # 3. Scan common locations if not found
            found_path = self._scan_for_asset(content_hash)
            if found_path:
                logger.info(f"Found asset through scan: {found_path}")
                self._update_asset_location(session, asset, found_path)
                return found_path

            return None

    def register_asset(self, file_path: Path, project_id: str | None = None) -> str:
        """Register a new asset or update existing one.

        Args:
            file_path: Path to the asset file
            project_id: Optional project to associate with

        Returns:
            Content hash of the asset
        """
        content_hash = get_or_calculate_content_hash(file_path)

        with get_session() as session:
            # Check if asset exists
            asset = session.query(Asset).filter_by(content_hash=content_hash).first()

            if not asset:
                # Create new asset
                asset = Asset(
                    content_hash=content_hash,
                    file_path=str(file_path),
                    file_path_verified=datetime.now(),
                    file_size=file_path.stat().st_size,
                    media_type=self._get_media_type(file_path),
                    project_id=project_id,
                )
                session.add(asset)
                logger.info(f"Registered new asset: {content_hash}")
            else:
                # Update existing asset
                asset.last_seen = datetime.now()
                asset.file_path = str(file_path)
                asset.file_path_verified = datetime.now()

                if project_id and not asset.project_id:
                    asset.project_id = project_id

            # Record path in history
            self._record_asset_path(session, content_hash, file_path)

            session.commit()
            return content_hash

    def register_asset_location(self, file_path: Path, content_hash: str) -> None:
        """Register where we found an asset.

        Args:
            file_path: Path where asset was found
            content_hash: Content hash of the asset
        """
        with get_session() as session:
            asset = session.query(Asset).filter_by(content_hash=content_hash).first()
            if not asset:
                logger.warning(f"Asset {content_hash} not found in database")
                return

            self._update_asset_location(session, asset, file_path)
            self._record_asset_path(session, content_hash, file_path)
            session.commit()

    def scan_directory(self, directory: Path, project_id: str | None = None) -> list[str]:
        """Scan a directory for assets and register them.

        Args:
            directory: Directory to scan
            project_id: Optional project to associate assets with

        Returns:
            List of content hashes found
        """
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []

        content_hashes = []
        extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                try:
                    content_hash = self.register_asset(file_path, project_id)
                    content_hashes.append(content_hash)
                except Exception as e:
                    logger.error(f"Error registering {file_path}: {e}")

        logger.info(f"Scanned {directory}, found {len(content_hashes)} assets")
        return content_hashes

    def find_moved_assets(self) -> list[Asset]:
        """Find assets whose cached paths no longer exist.

        Returns:
            List of assets that may have moved
        """
        with get_session() as session:
            moved_assets = []

            assets = session.query(Asset).filter(Asset.file_path.isnot(None)).all()
            for asset in assets:
                path = Path(asset.file_path)
                if not path.exists():
                    moved_assets.append(asset)
                    logger.debug(f"Asset may have moved: {asset.content_hash}")

            return moved_assets

    def update_asset_locations(self) -> int:
        """Update locations for all moved assets.

        Returns:
            Number of assets relocated
        """
        moved_assets = self.find_moved_assets()
        relocated_count = 0

        for asset in moved_assets:
            new_path = self.find_asset(asset.content_hash)
            if new_path:
                relocated_count += 1
                logger.info(f"Relocated asset {asset.content_hash} to {new_path}")

        return relocated_count

    def _verify_hash(self, file_path: Path, expected_hash: str) -> bool:
        """Verify a file has the expected content hash.

        Args:
            file_path: Path to file
            expected_hash: Expected content hash

        Returns:
            True if hash matches
        """
        try:
            actual_hash = calculate_content_hash(file_path)
            return actual_hash == expected_hash
        except Exception as e:
            logger.error(f"Error verifying hash for {file_path}: {e}")
            return False

    def _scan_for_asset(self, content_hash: str) -> Path | None:
        """Scan common locations for an asset.

        Args:
            content_hash: Content hash to find

        Returns:
            Path if found, None otherwise
        """
        extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            for file_path in search_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    try:
                        if calculate_content_hash(file_path) == content_hash:
                            return file_path
                    except Exception as e:
                        logger.debug(f"Error checking {file_path}: {e}")

        return None

    def _update_asset_location(self, session: Session, asset: Asset, file_path: Path) -> None:
        """Update the cached location of an asset.

        Args:
            session: Database session
            asset: Asset to update
            file_path: New file path
        """
        asset.file_path = str(file_path)
        asset.file_path_verified = datetime.now()
        asset.last_seen = datetime.now()

    def _record_asset_path(self, session: Session, content_hash: str, file_path: Path) -> None:
        """Record a path where an asset was found.

        Args:
            session: Database session
            content_hash: Asset content hash
            file_path: Path where asset was found
        """
        # Check if this path already exists
        existing = (
            session.query(AssetPath)
            .filter_by(content_hash=content_hash, file_path=str(file_path))
            .first()
        )

        if existing:
            existing.last_verified = datetime.now()
            existing.is_active = True
        else:
            # Add new path record
            asset_path = AssetPath(
                content_hash=content_hash, file_path=str(file_path), last_verified=datetime.now()
            )
            session.add(asset_path)

    def _get_media_type(self, file_path: Path) -> str:
        """Determine media type from file extension.

        Args:
            file_path: Path to file

        Returns:
            'image', 'video', or 'unknown'
        """
        suffix = file_path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return "image"
        elif suffix in VIDEO_EXTENSIONS:
            return "video"
        else:
            return "unknown"
