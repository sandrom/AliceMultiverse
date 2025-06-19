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
from .duckdb_cache import DuckDBSearchCache
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

    # TODO: Review unreachable code - async def _scan_location(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - location: StorageLocation,
    # TODO: Review unreachable code - force_scan: bool,
    # TODO: Review unreachable code - show_progress: bool
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan a single storage location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: Storage location to scan
    # TODO: Review unreachable code - force_scan: Force re-scan
    # TODO: Review unreachable code - show_progress: Show progress

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Scan statistics for this location
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - "files_found": 0,
    # TODO: Review unreachable code - "new_files": 0,
    # TODO: Review unreachable code - "projects": set()
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Check if scan is needed
    # TODO: Review unreachable code - if not force_scan and location.last_scan:
    # TODO: Review unreachable code - # Skip if scanned within last 24 hours
    # TODO: Review unreachable code - hours_since_scan = (datetime.now() - location.last_scan).total_seconds() / 3600
    # TODO: Review unreachable code - if hours_since_scan < 24:
    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Skipping {location.name} - last scanned {hours_since_scan:.1f} hours ago"
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - logger.info(f"Scanning location: {location.name} ({location.type.value})")

    # TODO: Review unreachable code - # Handle different storage types
    # TODO: Review unreachable code - if location.type == StorageType.LOCAL:
    # TODO: Review unreachable code - stats = await self._scan_local_location(location, show_progress)
    # TODO: Review unreachable code - elif location.type == StorageType.S3:
    # TODO: Review unreachable code - stats = await self._scan_s3_location(location)
    # TODO: Review unreachable code - elif location.type == StorageType.GCS:
    # TODO: Review unreachable code - stats = await self._scan_gcs_location(location)
    # TODO: Review unreachable code - elif location.type == StorageType.NETWORK:
    # TODO: Review unreachable code - stats = await self._scan_network_location(location)

    # TODO: Review unreachable code - # Don't update last scan time here - it causes FK constraint issues
    # TODO: Review unreachable code - # when file_locations are added during the scan
    # TODO: Review unreachable code - # Instead, let the caller handle this if needed

    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - async def _scan_local_location(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - location: StorageLocation,
    # TODO: Review unreachable code - show_progress: bool
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan a local filesystem location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: Local storage location
    # TODO: Review unreachable code - show_progress: Show progress

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Scan statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - path = Path(location.path).expanduser()

    # TODO: Review unreachable code - if not path.exists():
    # TODO: Review unreachable code - raise ValueError(f"Path does not exist: {path}")

    # TODO: Review unreachable code - # Track current files before scan
    # TODO: Review unreachable code - before_count = self.cache.get_statistics()["total_assets"]

    # TODO: Review unreachable code - # Scan the directory
    # TODO: Review unreachable code - files_processed = await self.scanner.scan_directory(
    # TODO: Review unreachable code - path,
    # TODO: Review unreachable code - storage_type="local",
    # TODO: Review unreachable code - recursive=True,
    # TODO: Review unreachable code - show_progress=show_progress
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Track new files after scan
    # TODO: Review unreachable code - after_count = self.cache.get_statistics()["total_assets"]
    # TODO: Review unreachable code - new_files = after_count - before_count

    # TODO: Review unreachable code - # Discover projects if project service is available
    # TODO: Review unreachable code - projects = set()
    # TODO: Review unreachable code - if self.project_service:
    # TODO: Review unreachable code - # Look for project folders
    # TODO: Review unreachable code - for project_dir in path.glob("*/"):
    # TODO: Review unreachable code - if project_dir.is_dir() and not project_dir.name.startswith('.'):
    # TODO: Review unreachable code - projects.add(project_dir.name)

    # TODO: Review unreachable code - # Also track files in registry
    # TODO: Review unreachable code - await self._update_registry_from_scan(location, path)

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "files_found": files_processed,
    # TODO: Review unreachable code - "new_files": new_files,
    # TODO: Review unreachable code - "projects": projects
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - async def _scan_s3_location(self, location: StorageLocation) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan an S3 bucket location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: S3 storage location

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Scan statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - from .cloud_scanners import S3Scanner

    # TODO: Review unreachable code - scanner = S3Scanner(location)
    # TODO: Review unreachable code - scan_results = await scanner.scan(show_progress=True)

    # TODO: Review unreachable code - # Track files in cache and registry
    # TODO: Review unreachable code - new_files = 0
    # TODO: Review unreachable code - projects = set()

    # TODO: Review unreachable code - for file_info in scan_results.get("media_files", []):
    # TODO: Review unreachable code - # Add to cache
    # TODO: Review unreachable code - metadata = {
    # TODO: Review unreachable code - "path": file_info["path"],
    # TODO: Review unreachable code - "file_size": file_info["size"],
    # TODO: Review unreachable code - "last_modified": file_info["last_modified"].isoformat() if hasattr(file_info["last_modified"], 'isoformat') else str(file_info["last_modified"]),
    # TODO: Review unreachable code - "content_hash": file_info["content_hash"],
    # TODO: Review unreachable code - "media_type": self._guess_media_type(file_info["key"])
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Check if file already exists
    # TODO: Review unreachable code - existing = self.cache.search(content_hash=file_info["content_hash"])
    # TODO: Review unreachable code - if not existing:
    # TODO: Review unreachable code - new_files += 1

    # TODO: Review unreachable code - # Add to cache with S3 location
    # TODO: Review unreachable code - self.cache.add_asset(
    # TODO: Review unreachable code - path=Path(file_info["path"]),
    # TODO: Review unreachable code - metadata=metadata,
    # TODO: Review unreachable code - content_hash=file_info["content_hash"],
    # TODO: Review unreachable code - storage_type="s3"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Track in registry
    # TODO: Review unreachable code - self.registry.track_file(
    # TODO: Review unreachable code - file_info["content_hash"],
    # TODO: Review unreachable code - location.location_id,
    # TODO: Review unreachable code - file_info["path"],
    # TODO: Review unreachable code - file_info["size"],
    # TODO: Review unreachable code - metadata_embedded=False  # Cloud files don't have embedded metadata yet
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Extract project from path
    # TODO: Review unreachable code - key_parts = file_info["key"].split('/')
    # TODO: Review unreachable code - if len(key_parts) > 1:
    # TODO: Review unreachable code - # Assume first non-empty part might be project
    # TODO: Review unreachable code - potential_project = key_parts[0]
    # TODO: Review unreachable code - if potential_project and not potential_project.startswith('.'):
    # TODO: Review unreachable code - projects.add(potential_project)

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "files_found": scan_results["files_found"],
    # TODO: Review unreachable code - "new_files": new_files,
    # TODO: Review unreachable code - "projects": projects
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - async def _scan_gcs_location(self, location: StorageLocation) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan a Google Cloud Storage location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: GCS storage location

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Scan statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - from .cloud_scanners import GCSScanner

    # TODO: Review unreachable code - scanner = GCSScanner(location)
    # TODO: Review unreachable code - scan_results = await scanner.scan(show_progress=True)

    # TODO: Review unreachable code - # Track files in cache and registry
    # TODO: Review unreachable code - new_files = 0
    # TODO: Review unreachable code - projects = set()

    # TODO: Review unreachable code - for file_info in scan_results.get("media_files", []):
    # TODO: Review unreachable code - # Add to cache
    # TODO: Review unreachable code - metadata = {
    # TODO: Review unreachable code - "path": file_info["path"],
    # TODO: Review unreachable code - "file_size": file_info["size"],
    # TODO: Review unreachable code - "last_modified": file_info["last_modified"].isoformat() if hasattr(file_info["last_modified"], 'isoformat') else str(file_info["last_modified"]),
    # TODO: Review unreachable code - "content_hash": file_info["content_hash"],
    # TODO: Review unreachable code - "media_type": self._guess_media_type(file_info["name"])
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Check if file already exists
    # TODO: Review unreachable code - existing = self.cache.search(content_hash=file_info["content_hash"])
    # TODO: Review unreachable code - if not existing:
    # TODO: Review unreachable code - new_files += 1

    # TODO: Review unreachable code - # Add to cache with GCS location
    # TODO: Review unreachable code - self.cache.add_asset(
    # TODO: Review unreachable code - path=Path(file_info["path"]),
    # TODO: Review unreachable code - metadata=metadata,
    # TODO: Review unreachable code - content_hash=file_info["content_hash"],
    # TODO: Review unreachable code - storage_type="gcs"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Track in registry
    # TODO: Review unreachable code - self.registry.track_file(
    # TODO: Review unreachable code - file_info["content_hash"],
    # TODO: Review unreachable code - location.location_id,
    # TODO: Review unreachable code - file_info["path"],
    # TODO: Review unreachable code - file_info["size"],
    # TODO: Review unreachable code - metadata_embedded=False  # Cloud files don't have embedded metadata yet
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Extract project from path
    # TODO: Review unreachable code - name_parts = file_info["name"].split('/')
    # TODO: Review unreachable code - if len(name_parts) > 1:
    # TODO: Review unreachable code - # Assume first non-empty part might be project
    # TODO: Review unreachable code - potential_project = name_parts[0]
    # TODO: Review unreachable code - if potential_project and not potential_project.startswith('.'):
    # TODO: Review unreachable code - projects.add(potential_project)

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "files_found": scan_results["files_found"],
    # TODO: Review unreachable code - "new_files": new_files,
    # TODO: Review unreachable code - "projects": projects
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - async def _scan_network_location(self, location: StorageLocation) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan a network drive location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: Network storage location

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Scan statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Network drives can often be treated as local paths
    # TODO: Review unreachable code - return await self._scan_local_location(location, show_progress=False)

    # TODO: Review unreachable code - async def _update_registry_from_scan(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - location: StorageLocation,
    # TODO: Review unreachable code - base_path: Path
    # TODO: Review unreachable code - ) -> None:
    # TODO: Review unreachable code - """Update registry with files found during scan.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: Storage location
    # TODO: Review unreachable code - base_path: Base path that was scanned
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Get all files from this location in the cache
    # TODO: Review unreachable code - # Note: DuckDB arrays are 1-indexed
    # TODO: Review unreachable code - results = self.cache.conn.execute("""
    # TODO: Review unreachable code - SELECT
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - locations,
    # TODO: Review unreachable code - file_size
    # TODO: Review unreachable code - FROM assets
    # TODO: Review unreachable code - WHERE len(locations) > 0
    # TODO: Review unreachable code - """).fetchall()

    # TODO: Review unreachable code - for content_hash, locations, file_size in results:
    # TODO: Review unreachable code - # Check if any location matches this base path
    # TODO: Review unreachable code - if locations:  # Make sure locations is not None
    # TODO: Review unreachable code - for loc in locations:
    # TODO: Review unreachable code - # DuckDB returns structs as dicts
    # TODO: Review unreachable code - if loc and loc.get("path", "").startswith(str(base_path)):
    # TODO: Review unreachable code - # Track in registry
    # TODO: Review unreachable code - metadata_embedded = loc.get("has_embedded_metadata", False)

    # TODO: Review unreachable code - self.registry.track_file(
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - location.location_id,
    # TODO: Review unreachable code - loc["path"],
    # TODO: Review unreachable code - file_size,
    # TODO: Review unreachable code - metadata_embedded
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - async def find_project_assets(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_name: str,
    # TODO: Review unreachable code - asset_types: list[str] | None = None
    # TODO: Review unreachable code - ) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Find all assets belonging to a specific project.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_name: Name of the project
    # TODO: Review unreachable code - asset_types: Optional list of asset types to filter

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of assets with their locations
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - logger.info(f"Finding assets for project: {project_name}")

    # TODO: Review unreachable code - # Search across all locations
    # TODO: Review unreachable code - assets = []

    # TODO: Review unreachable code - # Query cache for project assets
    # TODO: Review unreachable code - # DuckDB doesn't support EXISTS with UNNEST in WHERE clause
    # TODO: Review unreachable code - # Instead, we'll fetch all assets and filter in Python
    # TODO: Review unreachable code - query = """
    # TODO: Review unreachable code - SELECT content_hash, locations, media_type
    # TODO: Review unreachable code - FROM assets
    # TODO: Review unreachable code - WHERE len(locations) > 0
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - params = []

    # TODO: Review unreachable code - # Add type filter if specified
    # TODO: Review unreachable code - if asset_types:
    # TODO: Review unreachable code - placeholders = ",".join(["?" for _ in asset_types])
    # TODO: Review unreachable code - query += f" AND a.media_type IN ({placeholders})"
    # TODO: Review unreachable code - params.extend(asset_types)

    # TODO: Review unreachable code - results = self.cache.conn.execute(query, params).fetchall()

    # TODO: Review unreachable code - # Filter for project assets
    # TODO: Review unreachable code - project_pattern = f"/{project_name}/"

    # TODO: Review unreachable code - for content_hash, locations, media_type in results:
    # TODO: Review unreachable code - # Check if any location contains the project name
    # TODO: Review unreachable code - if locations:
    # TODO: Review unreachable code - project_match = False
    # TODO: Review unreachable code - primary_path = ""

    # TODO: Review unreachable code - for loc in locations:
    # TODO: Review unreachable code - if loc and project_pattern in loc.get("path", ""):
    # TODO: Review unreachable code - project_match = True
    # TODO: Review unreachable code - primary_path = loc["path"]
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - if project_match:
    # TODO: Review unreachable code - # Get all locations from registry
    # TODO: Review unreachable code - registry_locations = self.registry.get_file_locations(content_hash)

    # TODO: Review unreachable code - assets.append({
    # TODO: Review unreachable code - "content_hash": content_hash,
    # TODO: Review unreachable code - "path": primary_path,
    # TODO: Review unreachable code - "metadata": {"media_type": media_type},
    # TODO: Review unreachable code - "locations": locations,
    # TODO: Review unreachable code - "registry_locations": registry_locations
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - logger.info(f"Found {len(assets)} assets for project {project_name}")
    # TODO: Review unreachable code - return assets

    # TODO: Review unreachable code - async def consolidate_project(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_name: str,
    # TODO: Review unreachable code - target_location_id: str,
    # TODO: Review unreachable code - move_files: bool = False,
    # TODO: Review unreachable code - show_progress: bool = True,
    # TODO: Review unreachable code - progress_callback: Callable[[str, int, int], None] | None = None
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Consolidate all project assets to a single location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_name: Name of the project
    # TODO: Review unreachable code - target_location_id: Target location ID
    # TODO: Review unreachable code - move_files: Whether to move files (vs copy)
    # TODO: Review unreachable code - show_progress: Whether to show progress bar
    # TODO: Review unreachable code - progress_callback: Optional callback for progress updates

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Consolidation statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Consolidating project {project_name} to location {target_location_id}"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - "files_found": 0,
    # TODO: Review unreachable code - "files_copied": 0,
    # TODO: Review unreachable code - "files_moved": 0,
    # TODO: Review unreachable code - "errors": []
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Get target location
    # TODO: Review unreachable code - target_location = self.registry.get_location_by_id(target_location_id)
    # TODO: Review unreachable code - if not target_location:
    # TODO: Review unreachable code - raise ValueError(f"Target location {target_location_id} not found")

    # TODO: Review unreachable code - # Find all project assets
    # TODO: Review unreachable code - assets = await self.find_project_assets(project_name)
    # TODO: Review unreachable code - stats["files_found"] = len(assets)

    # TODO: Review unreachable code - # Create progress bar if needed
    # TODO: Review unreachable code - file_progress = None
    # TODO: Review unreachable code - if show_progress and assets:
    # TODO: Review unreachable code - file_progress = tqdm(
    # TODO: Review unreachable code - total=len(assets),
    # TODO: Review unreachable code - desc=f"{'Moving' if move_files else 'Copying'} files",
    # TODO: Review unreachable code - unit="file"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Process each asset
    # TODO: Review unreachable code - for idx, asset in enumerate(assets):
    # TODO: Review unreachable code - if progress_callback:
    # TODO: Review unreachable code - progress_callback(
    # TODO: Review unreachable code - f"Processing {Path(asset['path']).name}",
    # TODO: Review unreachable code - idx + 1,
    # TODO: Review unreachable code - len(assets)
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Check if already in target location
    # TODO: Review unreachable code - in_target = any(
    # TODO: Review unreachable code - loc["location_id"] == str(target_location_id)
    # TODO: Review unreachable code - for loc in asset["registry_locations"]
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if not in_target:
    # TODO: Review unreachable code - # Perform actual file operation
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - await self._transfer_file(
    # TODO: Review unreachable code - asset["path"],
    # TODO: Review unreachable code - asset["content_hash"],
    # TODO: Review unreachable code - target_location,
    # TODO: Review unreachable code - move=move_files
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if move_files:
    # TODO: Review unreachable code - stats["files_moved"] += 1
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - stats["files_copied"] += 1

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to transfer {asset['path']}: {e}")
    # TODO: Review unreachable code - stats["errors"].append({
    # TODO: Review unreachable code - "file": asset["path"],
    # TODO: Review unreachable code - "error": str(e)
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - if file_progress:
    # TODO: Review unreachable code - file_progress.update(1)

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error processing {asset['path']}: {e}")
    # TODO: Review unreachable code - stats["errors"].append({
    # TODO: Review unreachable code - "file": asset["path"],
    # TODO: Review unreachable code - "error": str(e)
    # TODO: Review unreachable code - })
    # TODO: Review unreachable code - if file_progress:
    # TODO: Review unreachable code - file_progress.update(1)

    # TODO: Review unreachable code - if file_progress:
    # TODO: Review unreachable code - file_progress.close()

    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - async def get_location_summary(self) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Get summary of all storage locations with statistics.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of location summaries
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - summaries = []

    # TODO: Review unreachable code - for location in self.registry.get_locations():
    # TODO: Review unreachable code - # Get file count and size for this location
    # TODO: Review unreachable code - result = self.registry.conn.execute("""
    # TODO: Review unreachable code - SELECT
    # TODO: Review unreachable code - COUNT(DISTINCT content_hash) as file_count,
    # TODO: Review unreachable code - SUM(file_size) as total_size
    # TODO: Review unreachable code - FROM file_locations
    # TODO: Review unreachable code - WHERE location_id = ?
    # TODO: Review unreachable code - """, [str(location.location_id)]).fetchone()

    # TODO: Review unreachable code - file_count, total_size = result if result else (0, 0)

    # TODO: Review unreachable code - summaries.append({
    # TODO: Review unreachable code - "location_id": str(location.location_id),
    # TODO: Review unreachable code - "name": location.name,
    # TODO: Review unreachable code - "type": location.type.value,
    # TODO: Review unreachable code - "path": location.path,
    # TODO: Review unreachable code - "status": location.status.value,
    # TODO: Review unreachable code - "priority": location.priority,
    # TODO: Review unreachable code - "last_scan": location.last_scan.isoformat() if location.last_scan else None,
    # TODO: Review unreachable code - "file_count": file_count,
    # TODO: Review unreachable code - "total_size_gb": (total_size or 0) / (1024 ** 3),
    # TODO: Review unreachable code - "rules": len(location.rules)
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - return sorted(summaries, key=lambda x: x["priority"], reverse=True)

    # TODO: Review unreachable code - async def _transfer_file(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - source_path: str,
    # TODO: Review unreachable code - content_hash: str,
    # TODO: Review unreachable code - target_location: StorageLocation,
    # TODO: Review unreachable code - move: bool = False
    # TODO: Review unreachable code - ) -> None:
    # TODO: Review unreachable code - """Transfer a file to a target location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - source_path: Source file path
    # TODO: Review unreachable code - content_hash: File content hash
    # TODO: Review unreachable code - target_location: Target storage location
    # TODO: Review unreachable code - move: Whether to move (vs copy) the file
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - import shutil
    # TODO: Review unreachable code - from pathlib import Path

    # TODO: Review unreachable code - source = Path(source_path)

    # TODO: Review unreachable code - if target_location.type == StorageType.LOCAL:
    # TODO: Review unreachable code - # Local file transfer
    # TODO: Review unreachable code - target_base = Path(target_location.path).expanduser()

    # TODO: Review unreachable code - # Preserve directory structure
    # TODO: Review unreachable code - # Extract relative path after finding common pattern
    # TODO: Review unreachable code - relative_parts = []
    # TODO: Review unreachable code - for part in source.parts:
    # TODO: Review unreachable code - if part in ["organized", "inbox", "projects"]:
    # TODO: Review unreachable code - # Start collecting after these known directories
    # TODO: Review unreachable code - relative_parts = []
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - relative_parts.append(part)

    # TODO: Review unreachable code - # Create target path
    # TODO: Review unreachable code - if relative_parts:
    # TODO: Review unreachable code - target_path = target_base / Path(*relative_parts[1:])  # Skip first part (date or project)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - target_path = target_base / source.name

    # TODO: Review unreachable code - # Ensure target directory exists
    # TODO: Review unreachable code - target_path.parent.mkdir(parents=True, exist_ok=True)

    # TODO: Review unreachable code - # Perform operation
    # TODO: Review unreachable code - if move:
    # TODO: Review unreachable code - shutil.move(str(source), str(target_path))
    # TODO: Review unreachable code - logger.info(f"Moved {source} to {target_path}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - shutil.copy2(str(source), str(target_path))
    # TODO: Review unreachable code - logger.info(f"Copied {source} to {target_path}")

    # TODO: Review unreachable code - # Track in registry
    # TODO: Review unreachable code - self.registry.track_file(
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - target_location.location_id,
    # TODO: Review unreachable code - str(target_path),
    # TODO: Review unreachable code - source.stat().st_size,
    # TODO: Review unreachable code - metadata_embedded=True  # Assume embedded if we're moving organized files
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Update cache with new location
    # TODO: Review unreachable code - self.cache._add_file_location(content_hash, target_path, "local")

    # TODO: Review unreachable code - elif target_location.type == StorageType.S3:
    # TODO: Review unreachable code - # S3 upload
    # TODO: Review unreachable code - from .cloud_scanners import S3Scanner

    # TODO: Review unreachable code - scanner = S3Scanner(target_location)

    # TODO: Review unreachable code - # Determine S3 key from source path
    # TODO: Review unreachable code - # Try to preserve some directory structure
    # TODO: Review unreachable code - source_parts = source.parts
    # TODO: Review unreachable code - key_parts = []

    # TODO: Review unreachable code - # Find project or date pattern
    # TODO: Review unreachable code - for i, part in enumerate(source_parts):
    # TODO: Review unreachable code - if part in ["organized", "inbox", "projects"] and i < len(source_parts) - 1:
    # TODO: Review unreachable code - # Start from the next part
    # TODO: Review unreachable code - key_parts = source_parts[i+1:]
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - if not key_parts:
    # TODO: Review unreachable code - # Fallback to just filename
    # TODO: Review unreachable code - key_parts = [source.name]

    # TODO: Review unreachable code - # Add prefix if configured
    # TODO: Review unreachable code - prefix = target_location.config.get("prefix", "")
    # TODO: Review unreachable code - if prefix:
    # TODO: Review unreachable code - s3_key = f"{prefix.rstrip('/')}/{'/'.join(key_parts)}"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - s3_key = '/'.join(key_parts)

    # TODO: Review unreachable code - # Upload file
    # TODO: Review unreachable code - await scanner.upload_file(source, s3_key)

    # TODO: Review unreachable code - # Track in registry
    # TODO: Review unreachable code - s3_path = f"s3://{target_location.path}/{s3_key}"
    # TODO: Review unreachable code - self.registry.track_file(
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - target_location.location_id,
    # TODO: Review unreachable code - s3_path,
    # TODO: Review unreachable code - source.stat().st_size,
    # TODO: Review unreachable code - metadata_embedded=False  # Cloud files don't have embedded metadata yet
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Update cache with new location
    # TODO: Review unreachable code - self.cache._add_file_location(content_hash, Path(s3_path), "s3")

    # TODO: Review unreachable code - logger.info(f"Uploaded {source} to {s3_path}")

    # TODO: Review unreachable code - elif target_location.type == StorageType.GCS:
    # TODO: Review unreachable code - # GCS upload
    # TODO: Review unreachable code - from .cloud_scanners import GCSScanner

    # TODO: Review unreachable code - scanner = GCSScanner(target_location)

    # TODO: Review unreachable code - # Determine GCS blob name from source path
    # TODO: Review unreachable code - # Try to preserve some directory structure
    # TODO: Review unreachable code - source_parts = source.parts
    # TODO: Review unreachable code - name_parts = []

    # TODO: Review unreachable code - # Find project or date pattern
    # TODO: Review unreachable code - for i, part in enumerate(source_parts):
    # TODO: Review unreachable code - if part in ["organized", "inbox", "projects"] and i < len(source_parts) - 1:
    # TODO: Review unreachable code - # Start from the next part
    # TODO: Review unreachable code - name_parts = source_parts[i+1:]
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - if not name_parts:
    # TODO: Review unreachable code - # Fallback to just filename
    # TODO: Review unreachable code - name_parts = [source.name]

    # TODO: Review unreachable code - # Add prefix if configured
    # TODO: Review unreachable code - prefix = target_location.config.get("prefix", "")
    # TODO: Review unreachable code - if prefix:
    # TODO: Review unreachable code - blob_name = f"{prefix.rstrip('/')}/{'/'.join(name_parts)}"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - blob_name = '/'.join(name_parts)

    # TODO: Review unreachable code - # Upload file
    # TODO: Review unreachable code - await scanner.upload_file(source, blob_name)

    # TODO: Review unreachable code - # Track in registry
    # TODO: Review unreachable code - gcs_path = f"gs://{target_location.path}/{blob_name}"
    # TODO: Review unreachable code - self.registry.track_file(
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - target_location.location_id,
    # TODO: Review unreachable code - gcs_path,
    # TODO: Review unreachable code - source.stat().st_size,
    # TODO: Review unreachable code - metadata_embedded=False  # Cloud files don't have embedded metadata yet
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Update cache with new location
    # TODO: Review unreachable code - self.cache._add_file_location(content_hash, Path(gcs_path), "gcs")

    # TODO: Review unreachable code - logger.info(f"Uploaded {source} to {gcs_path}")

    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - raise ValueError(f"Unsupported storage type: {target_location.type}")

    # TODO: Review unreachable code - def _guess_media_type(self, filename: str) -> str:
    # TODO: Review unreachable code - """Guess media type from filename extension.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - filename: File name or path

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Media type string
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - ext = Path(filename).suffix.lower()

    # TODO: Review unreachable code - # Image types
    # TODO: Review unreachable code - if ext in ['.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif']:
    # TODO: Review unreachable code - return 'image'
    # TODO: Review unreachable code - # Video types
    # TODO: Review unreachable code - elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
    # TODO: Review unreachable code - return 'video'
    # TODO: Review unreachable code - # Audio types
    # TODO: Review unreachable code - elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
    # TODO: Review unreachable code - return 'audio'
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return 'unknown'
