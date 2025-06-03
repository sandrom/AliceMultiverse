"""Multi-path file scanner with project-aware discovery.

This module extends the file scanner to work with multiple storage locations
and provides project-aware file discovery across all registered paths.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..core.structured_logging import get_logger
from ..projects.service import ProjectService
from .duckdb_cache import DuckDBSearchCache
from .file_scanner import FileScanner
from .location_registry import StorageLocation, StorageRegistry, StorageType

logger = get_logger(__name__)


class MultiPathScanner:
    """Scanner that discovers files across multiple storage locations."""
    
    def __init__(
        self,
        cache: DuckDBSearchCache,
        registry: StorageRegistry,
        project_service: Optional[ProjectService] = None
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
        show_progress: bool = True
    ) -> Dict[str, any]:
        """Discover all assets across all registered storage locations.
        
        Args:
            force_scan: Force re-scan even if location was recently scanned
            show_progress: Show progress bars
            
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
        
        for location in locations:
            try:
                location_stats = await self._scan_location(
                    location,
                    force_scan,
                    show_progress
                )
                
                stats["locations_scanned"] += 1
                stats["total_files_found"] += location_stats["files_found"]
                stats["new_files_discovered"] += location_stats["new_files"]
                stats["projects_found"].update(location_stats["projects"])
                
            except Exception as e:
                logger.error(f"Error scanning location {location.name}: {e}")
                stats["errors"].append({
                    "location": location.name,
                    "error": str(e)
                })
        
        # Convert set to list for JSON serialization
        stats["projects_found"] = list(stats["projects_found"])
        
        logger.info(
            f"Discovery complete: {stats['total_files_found']} files found, "
            f"{stats['new_files_discovered']} new files, "
            f"{len(stats['projects_found'])} projects"
        )
        
        return stats
    
    async def _scan_location(
        self,
        location: StorageLocation,
        force_scan: bool,
        show_progress: bool
    ) -> Dict[str, any]:
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
        
        # Update last scan time
        location.last_scan = datetime.now()
        self.registry.update_location(location)
        
        return stats
    
    async def _scan_local_location(
        self,
        location: StorageLocation,
        show_progress: bool
    ) -> Dict[str, any]:
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
    
    async def _scan_s3_location(self, location: StorageLocation) -> Dict[str, any]:
        """Scan an S3 bucket location.
        
        Args:
            location: S3 storage location
            
        Returns:
            Scan statistics
        """
        # TODO: Implement S3 scanning
        logger.warning(f"S3 scanning not yet implemented for {location.name}")
        return {"files_found": 0, "new_files": 0, "projects": set()}
    
    async def _scan_gcs_location(self, location: StorageLocation) -> Dict[str, any]:
        """Scan a Google Cloud Storage location.
        
        Args:
            location: GCS storage location
            
        Returns:
            Scan statistics
        """
        # TODO: Implement GCS scanning
        logger.warning(f"GCS scanning not yet implemented for {location.name}")
        return {"files_found": 0, "new_files": 0, "projects": set()}
    
    async def _scan_network_location(self, location: StorageLocation) -> Dict[str, any]:
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
        # This is a simplified query - in production would be paginated
        results = self.cache.conn.execute("""
            SELECT content_hash, locations, file_size
            FROM assets
            WHERE locations[1].storage_type = 'local'
        """).fetchall()
        
        for content_hash, locations, file_size in results:
            # Check if any location matches this base path
            for loc in locations:
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
        asset_types: Optional[List[str]] = None
    ) -> List[Dict[str, any]]:
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
        query = """
            SELECT a.content_hash, a.locations, a.media_type
            FROM assets a
            WHERE EXISTS (
                SELECT 1 FROM unnest(a.locations) AS loc 
                WHERE loc.path LIKE ?
            )
        """
        params = [f"%/{project_name}/%"]
        
        # Add type filter if specified
        if asset_types:
            placeholders = ",".join(["?" for _ in asset_types])
            query += f" AND a.media_type IN ({placeholders})"
            params.extend(asset_types)
        
        results = self.cache.conn.execute(query, params).fetchall()
        
        for content_hash, locations, media_type in results:
            # Get all locations from registry
            registry_locations = self.registry.get_file_locations(content_hash)
            
            # Get primary path from first location
            primary_path = locations[0]["path"] if locations else ""
            
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
        move_files: bool = False
    ) -> Dict[str, any]:
        """Consolidate all project assets to a single location.
        
        Args:
            project_name: Name of the project
            target_location_id: Target location ID
            move_files: Whether to move files (vs copy)
            
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
        
        # Process each asset
        for asset in assets:
            try:
                # Check if already in target location
                in_target = any(
                    loc["location_id"] == str(target_location_id)
                    for loc in asset["registry_locations"]
                )
                
                if not in_target:
                    # Copy/move to target location
                    # TODO: Implement actual file operations
                    logger.info(
                        f"Would {'move' if move_files else 'copy'} "
                        f"{asset['path']} to {target_location.name}"
                    )
                    
                    if move_files:
                        stats["files_moved"] += 1
                    else:
                        stats["files_copied"] += 1
                        
            except Exception as e:
                logger.error(f"Error processing {asset['path']}: {e}")
                stats["errors"].append({
                    "file": asset["path"],
                    "error": str(e)
                })
        
        return stats
    
    async def get_location_summary(self) -> List[Dict[str, any]]:
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