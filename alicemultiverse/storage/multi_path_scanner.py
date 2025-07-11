"""Multi-path file scanner with project-aware discovery.

This module extends the file scanner to work with multiple storage locations
and provides project-aware file discovery across all registered paths.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from ..core.structured_logging import get_logger
from ..projects.service import ProjectService
# TODO: Fix missing import - duckdb_cache doesn't exist
# from .duckdb_cache import DuckDBSearchCache
from .duckdb_storage import DuckDBStorage as DuckDBSearchCache  # Use closest match
from .file_scanner import FileScanner
from .location_registry import StorageLocation, StorageRegistry, StorageType
from typing import Any

logger = get_logger(__name__)


class MultiPathScanner:
    """Scanner that discovers files across multiple storage locations."""

    def __init__(
        self,
        cache: DuckDBSearchCache,
        registry: StorageRegistry,
        project_service: ProjectService | None = None
    ):
        """Initialize multi-path scanner.

        Args:
            cache: DuckDB search cache
            registry: Storage location registry
            project_service: Optional project service for project awareness
        """
        self.cache = cache
        self.registry = registry
        self.project_service = project_service
        self.scanner = FileScanner(cache)

    async def discover_all_assets(
        self,
        force_scan: bool = False,
        show_progress: bool = True,
        progress_callback: Callable[[str, int, int], None] | None = None
    ) -> dict[str, Any]:
        """Discover all assets across all registered storage locations.

        Args:
            force_scan: Force re-scan even if location was recently scanned
            show_progress: Show progress bars
            progress_callback: Optional callback for progress updates (message, current, total)

        Returns:
            Dictionary with discovery statistics
        """
        logger.info("Starting multi-path asset discovery")

        stats = {
            "locations_scanned": 0,
            "total_files_found": 0,
            "new_files_discovered": 0,
            "projects_found": set(),
            "errors": []
        }

        # Get all active storage locations
        from .location_registry import LocationStatus
        locations = self.registry.get_locations(status=LocationStatus.ACTIVE)

        # Create progress bar if needed
        location_progress = None
        if show_progress and locations:
            location_progress = tqdm(
                total=len(locations),
                desc="Scanning locations",
                unit="location"
            )

        for idx, location in enumerate(locations):
            if progress_callback:
                progress_callback(
                    f"Scanning {location.name}",
                    idx + 1,
                    len(locations)
                )
            try:
                location_stats = await self._scan_location(
                    location,
                    force_scan,
                    show_progress
                )

                if location_stats:  # Only count if scan was successful
                    stats["locations_scanned"] += 1
                    stats["total_files_found"] += location_stats["files_found"]
                    stats["new_files_discovered"] += location_stats["new_files"]
                    stats["projects_found"].update(location_stats["projects"])

                if location_progress:
                    location_progress.update(1)

            except Exception as e:
                logger.error(f"Error scanning location {location.name}: {e}")
                stats["errors"].append({
                    "location": location.name,
                    "error": str(e)
                })
                if location_progress:
                    location_progress.update(1)

        # Convert set to list for JSON serialization
        if stats is not None:
            stats["projects_found"] = list(stats["projects_found"])

        if location_progress:
            location_progress.close()

        logger.info(
            f"Discovery complete: {stats['total_files_found']} files found, "
            f"{stats['new_files_discovered']} new files, "
            f"{len(stats['projects_found'])} projects"
        )

        # Update scan times for successfully scanned locations
        # Do this after all file operations are complete to avoid FK issues
        for location in locations:
            if not any(e["location"] == location.name for e in stats["errors"]):
                try:
                    self.registry.update_scan_time(location.location_id)
                except Exception as e:
                    logger.warning(f"Could not update scan time for {location.name}: {e}")

        return stats

    async def _scan_location(
        self,
        location: StorageLocation,
        force_scan: bool,
        show_progress: bool
    ) -> dict[str, Any]:
        """Scan a single storage location.

        Args:
            location: Storage location to scan
            force_scan: Force re-scan
            show_progress: Show progress

        Returns:
            Scan statistics for this location
        """
        stats = {
            "files_found": 0,
            "new_files": 0,
            "projects": set()
        }

        # Check if scan is needed
        if not force_scan and location.last_scan:
            # Skip if scanned within last 24 hours
            hours_since_scan = (datetime.now() - location.last_scan).total_seconds() / 3600
            if hours_since_scan < 24:
                logger.info(
                    f"Skipping {location.name} - last scanned {hours_since_scan:.1f} hours ago"
                )
                return stats

        logger.info(f"Scanning location: {location.name} ({location.type.value})")

        # Handle different storage types
        if location.type == StorageType.LOCAL:
            stats = await self._scan_local_location(location, show_progress)
        elif location.type == StorageType.S3:
            stats = await self._scan_s3_location(location)
        elif location.type == StorageType.GCS:
            stats = await self._scan_gcs_location(location)
        elif location.type == StorageType.NETWORK:
            stats = await self._scan_network_location(location)

        # Don't update last scan time here - it causes FK constraint issues
        # when file_locations are added during the scan
        # Instead, let the caller handle this if needed

        return stats

    async def _scan_local_location(
        self,
        location: StorageLocation,
        show_progress: bool
    ) -> dict[str, Any]:
        """Scan a local filesystem location.

        Args:
            location: Local storage location
            show_progress: Show progress

        Returns:
            Scan statistics
        """
        path = Path(location.path).expanduser()

        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

        # Track current files before scan
        before_count = self.cache.get_statistics()["total_assets"]

        # Scan the directory
        files_processed = await self.scanner.scan_directory(
            path,
            storage_type="local",
            recursive=True,
            show_progress=show_progress
        )

        # Track new files after scan
        after_count = self.cache.get_statistics()["total_assets"]
        new_files = after_count - before_count

        # Discover projects if project service is available
        projects = set()
        if self.project_service:
            # Look for project folders
            for project_dir in path.glob("*/"):
                if project_dir.is_dir() and not project_dir.name.startswith('.'):
                    projects.add(project_dir.name)

        # Also track files in registry
        await self._update_registry_from_scan(location, path)

        return {
            "files_found": files_processed,
            "new_files": new_files,
            "projects": projects
        }

    async def _scan_s3_location(self, location: StorageLocation) -> dict[str, Any]:
        """Scan an S3 bucket location.

        Args:
            location: S3 storage location

        Returns:
            Scan statistics
        """
        from .cloud_scanners import S3Scanner

        scanner = S3Scanner(location)
        scan_results = await scanner.scan(show_progress=True)

        # Track files in cache and registry
        new_files = 0
        projects = set()

        for file_info in scan_results.get("media_files", []):
            # Add to cache
            metadata = {
                "path": file_info["path"],
                "file_size": file_info["size"],
                "last_modified": file_info["last_modified"].isoformat() if hasattr(file_info["last_modified"], 'isoformat') else str(file_info["last_modified"]),
                "content_hash": file_info["content_hash"],
                "media_type": self._guess_media_type(file_info["key"])
            }

            # Check if file already exists
            existing = self.cache.search(content_hash=file_info["content_hash"])
            if not existing:
                new_files += 1

            # Add to cache with S3 location
            self.cache.add_asset(
                path=Path(file_info["path"]),
                metadata=metadata,
                content_hash=file_info["content_hash"],
                storage_type="s3"
            )

            # Track in registry
            self.registry.track_file(
                file_info["content_hash"],
                location.location_id,
                file_info["path"],
                file_info["size"],
                metadata_embedded=False  # Cloud files don't have embedded metadata yet
            )

            # Extract project from path
            key_parts = file_info["key"].split('/')
            if len(key_parts) > 1:
                # Assume first non-empty part might be project
                potential_project = key_parts[0]
                if potential_project and not potential_project.startswith('.'):
                    projects.add(potential_project)

        return {
            "files_found": scan_results["files_found"],
            "new_files": new_files,
            "projects": projects
        }

    async def _scan_gcs_location(self, location: StorageLocation) -> dict[str, Any]:
        """Scan a Google Cloud Storage location.

        Args:
            location: GCS storage location

        Returns:
            Scan statistics
        """
        from .cloud_scanners import GCSScanner

        scanner = GCSScanner(location)
        scan_results = await scanner.scan(show_progress=True)

        # Track files in cache and registry
        new_files = 0
        projects = set()

        for file_info in scan_results.get("media_files", []):
            # Add to cache
            metadata = {
                "path": file_info["path"],
                "file_size": file_info["size"],
                "last_modified": file_info["last_modified"].isoformat() if hasattr(file_info["last_modified"], 'isoformat') else str(file_info["last_modified"]),
                "content_hash": file_info["content_hash"],
                "media_type": self._guess_media_type(file_info["name"])
            }

            # Check if file already exists
            existing = self.cache.search(content_hash=file_info["content_hash"])
            if not existing:
                new_files += 1

            # Add to cache with GCS location
            self.cache.add_asset(
                path=Path(file_info["path"]),
                metadata=metadata,
                content_hash=file_info["content_hash"],
                storage_type="gcs"
            )

            # Track in registry
            self.registry.track_file(
                file_info["content_hash"],
                location.location_id,
                file_info["path"],
                file_info["size"],
                metadata_embedded=False  # Cloud files don't have embedded metadata yet
            )

            # Extract project from path
            name_parts = file_info["name"].split('/')
            if len(name_parts) > 1:
                # Assume first non-empty part might be project
                potential_project = name_parts[0]
                if potential_project and not potential_project.startswith('.'):
                    projects.add(potential_project)

        return {
            "files_found": scan_results["files_found"],
            "new_files": new_files,
            "projects": projects
        }

    async def _scan_network_location(self, location: StorageLocation) -> dict[str, Any]:
        """Scan a network drive location.

        Args:
            location: Network storage location

        Returns:
            Scan statistics
        """
        # Network drives can often be treated as local paths
        return await self._scan_local_location(location, show_progress=False)

    async def _update_registry_from_scan(
        self,
        location: StorageLocation,
        base_path: Path
    ) -> None:
        """Update registry with files found during scan.

        Args:
            location: Storage location
            base_path: Base path that was scanned
        """
        # Get all files from this location in the cache
        # Note: DuckDB arrays are 1-indexed
        results = self.cache.conn.execute("""
            SELECT
                content_hash,
                locations,
                file_size
            FROM assets
            WHERE len(locations) > 0
        """).fetchall()

        for content_hash, locations, file_size in results:
            # Check if any location matches this base path
            if locations:  # Make sure locations is not None
                for loc in locations:
                    # DuckDB returns structs as dicts
                    if loc and loc.get("path", "").startswith(str(base_path)):
                        # Track in registry
                        metadata_embedded = loc.get("has_embedded_metadata", False)

                        self.registry.track_file(
                            content_hash,
                            location.location_id,
                            loc["path"],
                            file_size,
                            metadata_embedded
                        )

    async def find_project_assets(
        self,
        project_name: str,
        asset_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Find all assets belonging to a specific project.

        Args:
            project_name: Name of the project
            asset_types: Optional list of asset types to filter

        Returns:
            List of assets with their locations
        """
        logger.info(f"Finding assets for project: {project_name}")

        # Search across all locations
        assets = []

        # Query cache for project assets
        # DuckDB doesn't support EXISTS with UNNEST in WHERE clause
        # Instead, we'll fetch all assets and filter in Python
        query = """
            SELECT content_hash, locations, media_type
            FROM assets
            WHERE len(locations) > 0
        """
        params = []

        # Add type filter if specified
        if asset_types:
            placeholders = ",".join(["?" for _ in asset_types])
            query += f" AND a.media_type IN ({placeholders})"
            params.extend(asset_types)

        results = self.cache.conn.execute(query, params).fetchall()

        # Filter for project assets
        project_pattern = f"/{project_name}/"

        for content_hash, locations, media_type in results:
            # Check if any location contains the project name
            if locations:
                project_match = False
                primary_path = ""

                for loc in locations:
                    if loc and project_pattern in loc.get("path", ""):
                        project_match = True
                        primary_path = loc["path"]
                        break

                if project_match:
                    # Get all locations from registry
                    registry_locations = self.registry.get_file_locations(content_hash)

                    assets.append({
                        "content_hash": content_hash,
                        "path": primary_path,
                        "metadata": {"media_type": media_type},
                        "locations": locations,
                        "registry_locations": registry_locations
                    })

        logger.info(f"Found {len(assets)} assets for project {project_name}")
        return assets

    async def consolidate_project(
        self,
        project_name: str,
        target_location_id: str,
        move_files: bool = False,
        show_progress: bool = True,
        progress_callback: Callable[[str, int, int], None] | None = None
    ) -> dict[str, Any]:
        """Consolidate all project assets to a single location.

        Args:
            project_name: Name of the project
            target_location_id: Target location ID
            move_files: Whether to move files (vs copy)
            show_progress: Whether to show progress bar
            progress_callback: Optional callback for progress updates

        Returns:
            Consolidation statistics
        """
        logger.info(
            f"Consolidating project {project_name} to location {target_location_id}"
        )

        stats = {
            "files_found": 0,
            "files_copied": 0,
            "files_moved": 0,
            "errors": []
        }

        # Get target location
        target_location = self.registry.get_location_by_id(target_location_id)
        if not target_location:
            raise ValueError(f"Target location {target_location_id} not found")

        # Find all project assets
        assets = await self.find_project_assets(project_name)
        stats["files_found"] = len(assets)

        # Create progress bar if needed
        file_progress = None
        if show_progress and assets:
            file_progress = tqdm(
                total=len(assets),
                desc=f"{'Moving' if move_files else 'Copying'} files",
                unit="file"
            )

        # Process each asset
        for idx, asset in enumerate(assets):
            if progress_callback:
                progress_callback(
                    f"Processing {Path(asset['path']).name}",
                    idx + 1,
                    len(assets)
                )
            try:
                # Check if already in target location
                in_target = any(
                    loc["location_id"] == str(target_location_id)
                    for loc in asset["registry_locations"]
                )

                if not in_target:
                    # Perform actual file operation
                    try:
                        await self._transfer_file(
                            asset["path"],
                            asset["content_hash"],
                            target_location,
                            move=move_files
                        )

                        if move_files:
                            stats["files_moved"] += 1
                        else:
                            stats["files_copied"] += 1

                    except Exception as e:
                        logger.error(f"Failed to transfer {asset['path']}: {e}")
                        stats["errors"].append({
                            "file": asset["path"],
                            "error": str(e)
                        })

                if file_progress:
                    file_progress.update(1)

            except Exception as e:
                logger.error(f"Error processing {asset['path']}: {e}")
                stats["errors"].append({
                    "file": asset["path"],
                    "error": str(e)
                })
                if file_progress:
                    file_progress.update(1)

        if file_progress:
            file_progress.close()

        return stats

    async def get_location_summary(self) -> list[dict[str, Any]]:
        """Get summary of all storage locations with statistics.

        Returns:
            List of location summaries
        """
        summaries = []

        for location in self.registry.get_locations():
            # Get file count and size for this location
            result = self.registry.conn.execute("""
                SELECT
                    COUNT(DISTINCT content_hash) as file_count,
                    SUM(file_size) as total_size
                FROM file_locations
                WHERE location_id = ?
            """, [str(location.location_id)]).fetchone()

            file_count, total_size = result if result else (0, 0)

            summaries.append({
                "location_id": str(location.location_id),
                "name": location.name,
                "type": location.type.value,
                "path": location.path,
                "status": location.status.value,
                "priority": location.priority,
                "last_scan": location.last_scan.isoformat() if location.last_scan else None,
                "file_count": file_count,
                "total_size_gb": (total_size or 0) / (1024 ** 3),
                "rules": len(location.rules)
            })

        return sorted(summaries, key=lambda x: x["priority"], reverse=True)

    async def _transfer_file(
        self,
        source_path: str,
        content_hash: str,
        target_location: StorageLocation,
        move: bool = False
    ) -> None:
        """Transfer a file to a target location.

        Args:
            source_path: Source file path
            content_hash: File content hash
            target_location: Target storage location
            move: Whether to move (vs copy) the file
        """
        import shutil
        from pathlib import Path

        source = Path(source_path)

        if target_location.type == StorageType.LOCAL:
            # Local file transfer
            target_base = Path(target_location.path).expanduser()

            # Preserve directory structure
            # Extract relative path after finding common pattern
            relative_parts = []
            for part in source.parts:
                if part in ["organized", "inbox", "projects"]:
                    # Start collecting after these known directories
                    relative_parts = []
                else:
                    relative_parts.append(part)

            # Create target path
            if relative_parts:
                target_path = target_base / Path(*relative_parts[1:])  # Skip first part (date or project)
            else:
                target_path = target_base / source.name

            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Perform operation
            if move:
                shutil.move(str(source), str(target_path))
                logger.info(f"Moved {source} to {target_path}")
            else:
                shutil.copy2(str(source), str(target_path))
                logger.info(f"Copied {source} to {target_path}")

            # Track in registry
            self.registry.track_file(
                content_hash,
                target_location.location_id,
                str(target_path),
                source.stat().st_size,
                metadata_embedded=True  # Assume embedded if we're moving organized files
            )

            # Update cache with new location
            self.cache._add_file_location(content_hash, target_path, "local")

        elif target_location.type == StorageType.S3:
            # S3 upload
            from .cloud_scanners import S3Scanner

            scanner = S3Scanner(target_location)

            # Determine S3 key from source path
            # Try to preserve some directory structure
            source_parts = source.parts
            key_parts = []

            # Find project or date pattern
            for i, part in enumerate(source_parts):
                if part in ["organized", "inbox", "projects"] and i < len(source_parts) - 1:
                    # Start from the next part
                    key_parts = source_parts[i+1:]
                    break

            if not key_parts:
                # Fallback to just filename
                key_parts = [source.name]

            # Add prefix if configured
            prefix = target_location.config.get("prefix", "")
            if prefix:
                s3_key = f"{prefix.rstrip('/')}/{'/'.join(key_parts)}"
            else:
                s3_key = '/'.join(key_parts)

            # Upload file
            await scanner.upload_file(source, s3_key)

            # Track in registry
            s3_path = f"s3://{target_location.path}/{s3_key}"
            self.registry.track_file(
                content_hash,
                target_location.location_id,
                s3_path,
                source.stat().st_size,
                metadata_embedded=False  # Cloud files don't have embedded metadata yet
            )

            # Update cache with new location
            self.cache._add_file_location(content_hash, Path(s3_path), "s3")

            logger.info(f"Uploaded {source} to {s3_path}")

        elif target_location.type == StorageType.GCS:
            # GCS upload
            from .cloud_scanners import GCSScanner

            scanner = GCSScanner(target_location)

            # Determine GCS blob name from source path
            # Try to preserve some directory structure
            source_parts = source.parts
            name_parts = []

            # Find project or date pattern
            for i, part in enumerate(source_parts):
                if part in ["organized", "inbox", "projects"] and i < len(source_parts) - 1:
                    # Start from the next part
                    name_parts = source_parts[i+1:]
                    break

            if not name_parts:
                # Fallback to just filename
                name_parts = [source.name]

            # Add prefix if configured
            prefix = target_location.config.get("prefix", "")
            if prefix:
                blob_name = f"{prefix.rstrip('/')}/{'/'.join(name_parts)}"
            else:
                blob_name = '/'.join(name_parts)

            # Upload file
            await scanner.upload_file(source, blob_name)

            # Track in registry
            gcs_path = f"gs://{target_location.path}/{blob_name}"
            self.registry.track_file(
                content_hash,
                target_location.location_id,
                gcs_path,
                source.stat().st_size,
                metadata_embedded=False  # Cloud files don't have embedded metadata yet
            )

            # Update cache with new location
            self.cache._add_file_location(content_hash, Path(gcs_path), "gcs")

            logger.info(f"Uploaded {source} to {gcs_path}")

        else:
            raise ValueError(f"Unsupported storage type: {target_location.type}")

    def _guess_media_type(self, filename: str) -> str:
        """Guess media type from filename extension.

        Args:
            filename: File name or path

        Returns:
            Media type string
        """
        ext = Path(filename).suffix.lower()

        # Image types
        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif']:
            return 'image'
        # Video types
        elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            return 'video'
        # Audio types
        elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
            return 'audio'
        else:
            return 'unknown'
