"""Automatic file migration based on storage rules.

This module implements rule-based file movement between storage locations,
enabling automatic archival, tiering, and lifecycle management.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from ..core.structured_logging import get_logger
# TODO: Fix missing import - duckdb_cache doesn't exist
# from .duckdb_cache import DuckDBSearchCache
from .duckdb_storage import DuckDBStorage as DuckDBSearchCache  # Use closest match
from .location_registry import StorageLocation, StorageRegistry
from .multi_path_scanner import MultiPathScanner
from typing import Any

logger = get_logger(__name__)


class AutoMigrationService:
    """Service for automatic file migration based on rules."""

    def __init__(
        self,
        cache: DuckDBSearchCache,
        registry: StorageRegistry,
        scanner: MultiPathScanner | None = None
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
    ) -> dict[str, list[dict]]:
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

    # TODO: Review unreachable code - async def execute_migrations(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - migrations: dict[str, list[dict]],
    # TODO: Review unreachable code - move_files: bool = False,
    # TODO: Review unreachable code - show_progress: bool = True,
    # TODO: Review unreachable code - max_concurrent: int = 5
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Execute the migration plan.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - migrations: Migration plan from analyze_migrations
    # TODO: Review unreachable code - move_files: If True, move files; if False, copy them
    # TODO: Review unreachable code - show_progress: Show progress bars
    # TODO: Review unreachable code - max_concurrent: Maximum concurrent transfers

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Migration statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - 'files_migrated': 0,
    # TODO: Review unreachable code - 'files_failed': 0,
    # TODO: Review unreachable code - 'bytes_transferred': 0,
    # TODO: Review unreachable code - 'errors': []
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - if not migrations:
    # TODO: Review unreachable code - logger.info("No migrations to execute")
    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - total_migrations = sum(len(plans) for plans in migrations.values())
    # TODO: Review unreachable code - logger.info(f"Executing {total_migrations} migrations")

    # TODO: Review unreachable code - if show_progress:
    # TODO: Review unreachable code - progress = tqdm(total=total_migrations, desc="Migrating files")

    # TODO: Review unreachable code - # Create semaphore for concurrent transfers
    # TODO: Review unreachable code - semaphore = asyncio.Semaphore(max_concurrent)

    # TODO: Review unreachable code - async def migrate_file(migration_plan: dict):
    # TODO: Review unreachable code - """Migrate a single file."""
    # TODO: Review unreachable code - async with semaphore:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - content_hash = migration_plan['content_hash']
    # TODO: Review unreachable code - target_location = migration_plan['target_location']
    # TODO: Review unreachable code - current_locations = migration_plan['current_locations']

    # TODO: Review unreachable code - # Find source location with highest priority
    # TODO: Review unreachable code - source_location = None
    # TODO: Review unreachable code - source_path = None

    # TODO: Review unreachable code - for loc in current_locations:
    # TODO: Review unreachable code - if loc['location_status'] == 'active':
    # TODO: Review unreachable code - source_path = loc['file_path']
    # TODO: Review unreachable code - source_location = self.registry.get_location_by_id(
    # TODO: Review unreachable code - loc['location_id']
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - if not source_location or not source_path:
    # TODO: Review unreachable code - raise ValueError("No active source location found")

    # TODO: Review unreachable code - # Perform transfer
    # TODO: Review unreachable code - await self.scanner._transfer_file(
    # TODO: Review unreachable code - source_path,
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - target_location,
    # TODO: Review unreachable code - move=move_files
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Update stats
    # TODO: Review unreachable code - file_size = migration_plan['file_info'].get('file_size', 0)
    # TODO: Review unreachable code - stats['files_migrated'] += 1
    # TODO: Review unreachable code - stats['bytes_transferred'] += file_size

    # TODO: Review unreachable code - # If moving, remove from source location
    # TODO: Review unreachable code - if move_files:
    # TODO: Review unreachable code - self.registry.remove_file_from_location(
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - source_location.location_id
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Migrated {Path(source_path).name} to {target_location.name}"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to migrate {content_hash}: {e}")
    # TODO: Review unreachable code - stats['files_failed'] += 1
    # TODO: Review unreachable code - stats['errors'].append({
    # TODO: Review unreachable code - 'content_hash': content_hash,
    # TODO: Review unreachable code - 'error': str(e)
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - finally:
    # TODO: Review unreachable code - if show_progress:
    # TODO: Review unreachable code - progress.update(1)

    # TODO: Review unreachable code - # Execute migrations concurrently
    # TODO: Review unreachable code - tasks = []
    # TODO: Review unreachable code - for content_hash, plans in migrations.items():
    # TODO: Review unreachable code - for plan in plans:
    # TODO: Review unreachable code - tasks.append(migrate_file(plan))

    # TODO: Review unreachable code - await asyncio.gather(*tasks, return_exceptions=True)

    # TODO: Review unreachable code - if show_progress:
    # TODO: Review unreachable code - progress.close()

    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Migration complete: {stats['files_migrated']} succeeded, "
    # TODO: Review unreachable code - f"{stats['files_failed']} failed, "
    # TODO: Review unreachable code - f"{stats['bytes_transferred'] / (1024**3):.2f} GB transferred"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - async def run_auto_migration(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - dry_run: bool = False,
    # TODO: Review unreachable code - move_files: bool = False,
    # TODO: Review unreachable code - show_progress: bool = True
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Run complete auto-migration process.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - dry_run: If True, only analyze without making changes
    # TODO: Review unreachable code - move_files: If True, move files; if False, copy them
    # TODO: Review unreachable code - show_progress: Show progress bars

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Migration results
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # First, analyze what needs to be migrated
    # TODO: Review unreachable code - migrations = await self.analyze_migrations(
    # TODO: Review unreachable code - dry_run=dry_run,
    # TODO: Review unreachable code - show_progress=show_progress
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - results = {
    # TODO: Review unreachable code - 'analysis': {
    # TODO: Review unreachable code - 'files_to_migrate': len(migrations),
    # TODO: Review unreachable code - 'migrations': []
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - 'execution': None
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Prepare summary of migrations
    # TODO: Review unreachable code - for content_hash, plans in migrations.items():
    # TODO: Review unreachable code - for plan in plans:
    # TODO: Review unreachable code - migration_summary = {
    # TODO: Review unreachable code - 'file': Path(plan['file_info'].get('path', '')).name,
    # TODO: Review unreachable code - 'size': plan['file_info'].get('file_size', 0),
    # TODO: Review unreachable code - 'from': [loc['location_name'] for loc in plan['current_locations']],
    # TODO: Review unreachable code - 'to': plan['target_location'].name,
    # TODO: Review unreachable code - 'reason': plan['reason']
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - results['analysis']['migrations'].append(migration_summary)

    # TODO: Review unreachable code - if not dry_run and migrations:
    # TODO: Review unreachable code - # Execute the migrations
    # TODO: Review unreachable code - execution_stats = await self.execute_migrations(
    # TODO: Review unreachable code - migrations,
    # TODO: Review unreachable code - move_files=move_files,
    # TODO: Review unreachable code - show_progress=show_progress
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - results['execution'] = execution_stats

    # TODO: Review unreachable code - return results

    # TODO: Review unreachable code - def _prepare_metadata(self, asset: dict) -> dict:
    # TODO: Review unreachable code - """Prepare metadata for rule evaluation.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - asset: Asset information from cache

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Metadata dictionary for rule evaluation
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - metadata = asset.get('metadata', {})

    # TODO: Review unreachable code - # Calculate age in days
    # TODO: Review unreachable code - # For testing, use path to get file age
    # TODO: Review unreachable code - age_days = 0
    # TODO: Review unreachable code - path = asset.get('path', '')
    # TODO: Review unreachable code - if path and Path(path).exists():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - import os
    # TODO: Review unreachable code - stat = os.stat(path)
    # TODO: Review unreachable code - file_date = datetime.fromtimestamp(stat.st_mtime)
    # TODO: Review unreachable code - age_days = (datetime.now() - file_date).days
    # TODO: Review unreachable code - except (OSError, IOError):
    # TODO: Review unreachable code - pass

    # TODO: Review unreachable code - # Build metadata for rule evaluation
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - 'age_days': age_days,
    # TODO: Review unreachable code - 'file_size': asset.get('file_size', 0),
    # TODO: Review unreachable code - 'file_type': metadata.get('media_type', 'unknown'),
    # TODO: Review unreachable code - 'tags': metadata.get('tags', []),
    # TODO: Review unreachable code - 'quality_stars': 0  # Quality system removed - default to 0
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def _get_migration_reason(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - metadata: dict,
    # TODO: Review unreachable code - target_location: StorageLocation
    # TODO: Review unreachable code - ) -> str:
    # TODO: Review unreachable code - """Get human-readable reason for migration.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - metadata: File metadata
    # TODO: Review unreachable code - target_location: Target storage location

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Reason string
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - reasons = []

    # TODO: Review unreachable code - for rule in target_location.rules:
    # TODO: Review unreachable code - if rule.max_age_days and metadata['age_days'] <= rule.max_age_days:
    # TODO: Review unreachable code - reasons.append(f"File age ({metadata['age_days']} days) within limit")

    # TODO: Review unreachable code - if rule.min_age_days and metadata['age_days'] >= rule.min_age_days:
    # TODO: Review unreachable code - reasons.append(f"File age ({metadata['age_days']} days) exceeds minimum")

    # TODO: Review unreachable code - if rule.min_quality_stars and metadata['quality_stars'] >= rule.min_quality_stars:
    # TODO: Review unreachable code - reasons.append(f"Quality rating ({metadata['quality_stars']}) meets threshold")

    # TODO: Review unreachable code - if rule.include_types and metadata['file_type'] in rule.include_types:
    # TODO: Review unreachable code - reasons.append(f"File type ({metadata['file_type']}) is included")

    # TODO: Review unreachable code - return "; ".join(reasons) if reasons else "Matches storage rules"


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
