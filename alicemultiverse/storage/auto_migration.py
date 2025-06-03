"""Automatic file migration based on storage rules.

This module implements rule-based file movement between storage locations,
enabling automatic archival, tiering, and lifecycle management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tqdm import tqdm

from ..core.structured_logging import get_logger
from .duckdb_cache import DuckDBSearchCache
from .location_registry import StorageLocation, StorageRegistry, StorageType
from .multi_path_scanner import MultiPathScanner

logger = get_logger(__name__)


class AutoMigrationService:
    """Service for automatic file migration based on rules."""
    
    def __init__(
        self,
        cache: DuckDBSearchCache,
        registry: StorageRegistry,
        scanner: Optional[MultiPathScanner] = None
    ):
        """Initialize auto-migration service.
        
        Args:
            cache: DuckDB search cache
            registry: Storage location registry
            scanner: Optional multi-path scanner (will create if not provided)
        """
        self.cache = cache
        self.registry = registry
        self.scanner = scanner or MultiPathScanner(cache, registry)
    
    async def analyze_migrations(
        self,
        dry_run: bool = True,
        show_progress: bool = True
    ) -> Dict[str, List[Dict]]:
        """Analyze which files should be migrated based on rules.
        
        Args:
            dry_run: If True, only analyze without making changes
            show_progress: Show progress bars
            
        Returns:
            Dictionary mapping file hashes to proposed migrations
        """
        logger.info("Analyzing files for migration based on storage rules")
        
        migrations = {}
        files_analyzed = 0
        
        # Get all active storage locations
        from .location_registry import LocationStatus
        locations = self.registry.get_locations(status=LocationStatus.ACTIVE)
        
        # Get all unique files
        # Query the cache directly for all assets
        results = self.cache.conn.execute("""
            SELECT content_hash, locations, file_size, media_type, created_at
            FROM assets
            WHERE len(locations) > 0
        """).fetchall()
        
        all_files = []
        for row in results:
            content_hash, locations, file_size, media_type, created_date = row
            if locations and len(locations) > 0:
                # Use first location as primary path
                primary_loc = locations[0]
                all_files.append({
                    'content_hash': content_hash,
                    'path': primary_loc.get('path', ''),
                    'file_size': file_size,
                    'metadata': {
                        'media_type': media_type,
                        'created_date': created_date.isoformat() if created_date else None
                    }
                })
        
        if show_progress:
            progress = tqdm(total=len(all_files), desc="Analyzing files")
        
        for asset in all_files:
            content_hash = asset.get('content_hash')
            if not content_hash:
                continue
            
            # Get current file metadata
            metadata = self._prepare_metadata(asset)
            
            # Find best location based on rules
            best_location = self.registry.get_location_for_file(
                content_hash,
                metadata
            )
            
            if best_location:
                # Check if file needs to move
                current_locations = self.registry.get_file_locations(content_hash)
                
                # Check if file is already in the best location
                in_best_location = any(
                    loc['location_id'] == str(best_location.location_id)
                    for loc in current_locations
                )
                
                if not in_best_location and current_locations:
                    # File should be migrated
                    migration_plan = {
                        'content_hash': content_hash,
                        'current_locations': current_locations,
                        'target_location': best_location,
                        'reason': self._get_migration_reason(metadata, best_location),
                        'file_info': asset
                    }
                    
                    if content_hash not in migrations:
                        migrations[content_hash] = []
                    migrations[content_hash].append(migration_plan)
            
            files_analyzed += 1
            if show_progress:
                progress.update(1)
        
        if show_progress:
            progress.close()
        
        logger.info(
            f"Analysis complete: {len(migrations)} files need migration out of "
            f"{files_analyzed} analyzed"
        )
        
        return migrations
    
    async def execute_migrations(
        self,
        migrations: Dict[str, List[Dict]],
        move_files: bool = False,
        show_progress: bool = True,
        max_concurrent: int = 5
    ) -> Dict[str, any]:
        """Execute the migration plan.
        
        Args:
            migrations: Migration plan from analyze_migrations
            move_files: If True, move files; if False, copy them
            show_progress: Show progress bars
            max_concurrent: Maximum concurrent transfers
            
        Returns:
            Migration statistics
        """
        stats = {
            'files_migrated': 0,
            'files_failed': 0,
            'bytes_transferred': 0,
            'errors': []
        }
        
        if not migrations:
            logger.info("No migrations to execute")
            return stats
        
        total_migrations = sum(len(plans) for plans in migrations.values())
        logger.info(f"Executing {total_migrations} migrations")
        
        if show_progress:
            progress = tqdm(total=total_migrations, desc="Migrating files")
        
        # Create semaphore for concurrent transfers
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def migrate_file(migration_plan: Dict):
            """Migrate a single file."""
            async with semaphore:
                try:
                    content_hash = migration_plan['content_hash']
                    target_location = migration_plan['target_location']
                    current_locations = migration_plan['current_locations']
                    
                    # Find source location with highest priority
                    source_location = None
                    source_path = None
                    
                    for loc in current_locations:
                        if loc['location_status'] == 'active':
                            source_path = loc['file_path']
                            source_location = self.registry.get_location_by_id(
                                loc['location_id']
                            )
                            break
                    
                    if not source_location or not source_path:
                        raise ValueError("No active source location found")
                    
                    # Perform transfer
                    await self.scanner._transfer_file(
                        source_path,
                        content_hash,
                        target_location,
                        move=move_files
                    )
                    
                    # Update stats
                    file_size = migration_plan['file_info'].get('file_size', 0)
                    stats['files_migrated'] += 1
                    stats['bytes_transferred'] += file_size
                    
                    # If moving, remove from source location
                    if move_files:
                        self.registry.remove_file_from_location(
                            content_hash,
                            source_location.location_id
                        )
                    
                    logger.info(
                        f"Migrated {Path(source_path).name} to {target_location.name}"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to migrate {content_hash}: {e}")
                    stats['files_failed'] += 1
                    stats['errors'].append({
                        'content_hash': content_hash,
                        'error': str(e)
                    })
                
                finally:
                    if show_progress:
                        progress.update(1)
        
        # Execute migrations concurrently
        tasks = []
        for content_hash, plans in migrations.items():
            for plan in plans:
                tasks.append(migrate_file(plan))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        if show_progress:
            progress.close()
        
        logger.info(
            f"Migration complete: {stats['files_migrated']} succeeded, "
            f"{stats['files_failed']} failed, "
            f"{stats['bytes_transferred'] / (1024**3):.2f} GB transferred"
        )
        
        return stats
    
    async def run_auto_migration(
        self,
        dry_run: bool = False,
        move_files: bool = False,
        show_progress: bool = True
    ) -> Dict[str, any]:
        """Run complete auto-migration process.
        
        Args:
            dry_run: If True, only analyze without making changes
            move_files: If True, move files; if False, copy them
            show_progress: Show progress bars
            
        Returns:
            Migration results
        """
        # First, analyze what needs to be migrated
        migrations = await self.analyze_migrations(
            dry_run=dry_run,
            show_progress=show_progress
        )
        
        results = {
            'analysis': {
                'files_to_migrate': len(migrations),
                'migrations': []
            },
            'execution': None
        }
        
        # Prepare summary of migrations
        for content_hash, plans in migrations.items():
            for plan in plans:
                migration_summary = {
                    'file': Path(plan['file_info'].get('path', '')).name,
                    'size': plan['file_info'].get('file_size', 0),
                    'from': [loc['location_name'] for loc in plan['current_locations']],
                    'to': plan['target_location'].name,
                    'reason': plan['reason']
                }
                results['analysis']['migrations'].append(migration_summary)
        
        if not dry_run and migrations:
            # Execute the migrations
            execution_stats = await self.execute_migrations(
                migrations,
                move_files=move_files,
                show_progress=show_progress
            )
            results['execution'] = execution_stats
        
        return results
    
    def _prepare_metadata(self, asset: Dict) -> Dict:
        """Prepare metadata for rule evaluation.
        
        Args:
            asset: Asset information from cache
            
        Returns:
            Metadata dictionary for rule evaluation
        """
        metadata = asset.get('metadata', {})
        
        # Calculate age in days
        # For testing, use path to get file age
        age_days = 0
        path = asset.get('path', '')
        if path and Path(path).exists():
            try:
                import os
                stat = os.stat(path)
                file_date = datetime.fromtimestamp(stat.st_mtime)
                age_days = (datetime.now() - file_date).days
            except:
                pass
        
        # Build metadata for rule evaluation
        return {
            'age_days': age_days,
            'file_size': asset.get('file_size', 0),
            'file_type': metadata.get('media_type', 'unknown'),
            'tags': metadata.get('tags', []),
            'quality_stars': 0  # Quality system removed - default to 0
        }
    
    def _get_migration_reason(
        self,
        metadata: Dict,
        target_location: StorageLocation
    ) -> str:
        """Get human-readable reason for migration.
        
        Args:
            metadata: File metadata
            target_location: Target storage location
            
        Returns:
            Reason string
        """
        reasons = []
        
        for rule in target_location.rules:
            if rule.max_age_days and metadata['age_days'] <= rule.max_age_days:
                reasons.append(f"File age ({metadata['age_days']} days) within limit")
            
            if rule.min_age_days and metadata['age_days'] >= rule.min_age_days:
                reasons.append(f"File age ({metadata['age_days']} days) exceeds minimum")
            
            if rule.min_quality_stars and metadata['quality_stars'] >= rule.min_quality_stars:
                reasons.append(f"Quality rating ({metadata['quality_stars']}) meets threshold")
            
            if rule.include_types and metadata['file_type'] in rule.include_types:
                reasons.append(f"File type ({metadata['file_type']}) is included")
        
        return "; ".join(reasons) if reasons else "Matches storage rules"


class MigrationScheduler:
    """Scheduler for periodic auto-migration runs."""
    
    def __init__(self, migration_service: AutoMigrationService):
        """Initialize migration scheduler.
        
        Args:
            migration_service: Auto-migration service instance
        """
        self.service = migration_service
        self._running = False
        self._task = None
    
    async def start(
        self,
        interval_hours: int = 24,
        move_files: bool = False
    ):
        """Start periodic migration checks.
        
        Args:
            interval_hours: Hours between migration runs
            move_files: Whether to move files (vs copy)
        """
        self._running = True
        
        async def run_periodic():
            while self._running:
                try:
                    logger.info("Running scheduled auto-migration")
                    await self.service.run_auto_migration(
                        dry_run=False,
                        move_files=move_files,
                        show_progress=False
                    )
                except Exception as e:
                    logger.error(f"Scheduled migration failed: {e}")
                
                # Wait for next run
                await asyncio.sleep(interval_hours * 3600)
        
        self._task = asyncio.create_task(run_periodic())
        logger.info(f"Started migration scheduler (interval: {interval_hours} hours)")
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped migration scheduler")