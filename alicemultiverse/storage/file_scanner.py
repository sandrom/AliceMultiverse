"""File scanner to rebuild DuckDB cache from files.

This module scans directories and extracts metadata from files
to populate the DuckDB search cache.
"""

import hashlib
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from ..core.structured_logging import get_logger
from .metadata_extractor import MetadataExtractor
from .unified_duckdb import DuckDBSearchCache

logger = get_logger(__name__)


class FileScanner:
    """Scan files and rebuild search cache from embedded metadata."""

    SUPPORTED_EXTENSIONS = {
        # Images
        ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif",
        # Videos
        ".mp4", ".mov",
        # Audio
        ".mp3", ".wav", ".m4a"
    }

    def __init__(self, cache: DuckDBSearchCache):
        """Initialize file scanner.

        Args:
            cache: DuckDB search cache to populate
        """
        self.cache = cache
        self.extractor = MetadataExtractor()
        self._processed_hashes: set[str] = set()

    async def scan_directory(
        self,
        directory: Path,
        storage_type: str = "local",
        recursive: bool = True,
        show_progress: bool = True
    ) -> int:
        """Scan a directory and update cache with file metadata.

        Args:
            directory: Directory to scan
            storage_type: Type of storage (local, s3, gcs, network)
            recursive: Whether to scan subdirectories
            show_progress: Whether to show progress bar

        Returns:
            Number of files processed
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        # Collect all media files
        logger.info(f"Scanning directory: {directory}")
        files = self._collect_files(directory, recursive)

        if not files:
            logger.info("No supported media files found")
            return 0

        logger.info(f"Found {len(files)} media files to process")

        # Process files
        processed = 0
        if show_progress:
            files = tqdm(files, desc="Scanning files")

        for file_path in files:
            try:
                await self._process_file(file_path, storage_type)
                processed += 1
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

        logger.info(f"Processed {processed} files")
        return processed

    async def scan_multiple_directories(
        self,
        directories: list[tuple[Path, str]],
        show_progress: bool = True
    ) -> int:
        """Scan multiple directories with different storage types.

        Args:
            directories: List of (directory, storage_type) tuples
            show_progress: Whether to show progress bar

        Returns:
            Total number of files processed
        """
        total_processed = 0

        for directory, storage_type in directories:
            try:
                processed = await self.scan_directory(
                    directory,
                    storage_type,
                    show_progress=show_progress
                )
                total_processed += processed
            except Exception as e:
                logger.error(f"Error scanning {directory}: {e}")

        return total_processed

    def _collect_files(self, directory: Path, recursive: bool) -> list[Path]:
        """Collect all supported media files in directory.

        Args:
            directory: Directory to search
            recursive: Whether to search subdirectories

        Returns:
            List of file paths
        """
        files = []

        if recursive:
            for ext in self.SUPPORTED_EXTENSIONS:
                files.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in self.SUPPORTED_EXTENSIONS:
                files.extend(directory.glob(f"*{ext}"))

        # Filter out hidden files and directories, and sorted-out folders
        files = [
            f for f in files
            if not any(part.startswith('.') for part in f.parts)
            and not any(part in ['sorted-out', 'sorted_out'] for part in f.parts)
        ]

        return sorted(files)

    async def _process_file(self, file_path: Path, storage_type: str) -> None:
        """Process a single file and update cache.

        Args:
            file_path: Path to the file
            storage_type: Type of storage
        """
        # Calculate content hash
        content_hash = await self._calculate_file_hash(file_path)

        # Skip if already processed in this session
        if content_hash in self._processed_hashes:
            logger.debug(f"Skipping already processed file: {file_path}")
            return

        # Extract metadata
        try:
            metadata = self.extractor.extract_metadata(file_path)

            # Add content hash if not already in metadata
            if "content_hash" not in metadata:
                metadata["content_hash"] = content_hash

            # Update cache
            self.cache.upsert_asset(
                content_hash,
                file_path,
                metadata,
                storage_type
            )

            self._processed_hashes.add(content_hash)

            # Log based on metadata presence
            if self.extractor.has_alice_metadata(file_path):
                logger.debug(f"Updated cache with Alice metadata: {file_path.name}")
            else:
                logger.debug(f"Added file without Alice metadata: {file_path.name}")

        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content.

        Args:
            file_path: Path to the file

        Returns:
            Hex string of SHA-256 hash
        """
        sha256_hash = hashlib.sha256()

        # Read file in chunks to handle large files
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    async def verify_cache_integrity(
        self,
        remove_missing: bool = False
    ) -> dict:
        """Verify that all cached files still exist.

        Args:
            remove_missing: Whether to remove missing files from cache

        Returns:
            Dictionary with verification statistics
        """
        logger.info("Verifying cache integrity")

        stats = {
            "total_assets": 0,
            "verified": 0,
            "missing": 0,
            "errors": 0
        }

        # Get all assets from cache
        # For now, we'll do a simple query - in production this would be paginated
        assets = self.cache.conn.execute(
            "SELECT content_hash, locations FROM assets"
        ).fetchall()

        stats["total_assets"] = len(assets)

        for content_hash, locations in assets:
            asset_exists = False
            valid_locations = []

            for location in locations:
                file_path = Path(location["path"])

                try:
                    if file_path.exists():
                        # Verify hash matches
                        actual_hash = await self._calculate_file_hash(file_path)
                        if actual_hash == content_hash:
                            asset_exists = True
                            valid_locations.append(location)
                        else:
                            logger.warning(
                                f"Hash mismatch for {file_path}: "
                                f"expected {content_hash}, got {actual_hash}"
                            )
                except Exception as e:
                    logger.error(f"Error verifying {file_path}: {e}")
                    stats["errors"] += 1

            if asset_exists:
                stats["verified"] += 1

                # Update locations if some were invalid
                if len(valid_locations) < len(locations):
                    self.cache.conn.execute(
                        "UPDATE assets SET locations = ? WHERE content_hash = ?",
                        [valid_locations, content_hash]
                    )
            else:
                stats["missing"] += 1

                if remove_missing:
                    logger.info(f"Removing missing asset: {content_hash}")
                    self.cache.delete_asset(content_hash)

        logger.info(
            f"Verification complete: {stats['verified']} verified, "
            f"{stats['missing']} missing, {stats['errors']} errors"
        )

        return stats

    async def rebuild_cache(
        self,
        directories: list[tuple[Path, str]],
        clear_first: bool = True
    ) -> dict:
        """Rebuild entire cache from scratch.

        Args:
            directories: List of (directory, storage_type) tuples to scan
            clear_first: Whether to clear cache before rebuilding

        Returns:
            Dictionary with rebuild statistics
        """
        logger.info("Starting cache rebuild")

        if clear_first:
            self.cache.rebuild_from_scratch()
            self._processed_hashes.clear()

        # Scan all directories
        start_time = datetime.now()
        total_processed = await self.scan_multiple_directories(directories)

        # Get final statistics
        stats = self.cache.get_statistics()
        stats["rebuild_time"] = (datetime.now() - start_time).total_seconds()
        stats["files_processed"] = total_processed

        logger.info(
            f"Cache rebuild complete: {total_processed} files processed "
            f"in {stats['rebuild_time']:.1f} seconds"
        )

        return stats
