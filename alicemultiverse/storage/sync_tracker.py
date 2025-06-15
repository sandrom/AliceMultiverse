"""Sync tracking for multi-location file management.

This module handles synchronization tracking, conflict detection,
and version management for files that exist across multiple storage locations.
"""

import asyncio
from datetime import datetime
from enum import Enum

from ..core.structured_logging import get_logger
from .location_registry import StorageRegistry

logger = get_logger(__name__)


class SyncStatus(Enum):
    """Synchronization status for files."""

    SYNCED = "synced"              # All locations have same version
    PENDING_UPLOAD = "pending_upload"   # Needs to be uploaded to location
    PENDING_UPDATE = "pending_update"   # Newer version available
    CONFLICT = "conflict"           # Different versions in different locations
    MISSING = "missing"             # File missing from location
    ERROR = "error"                 # Sync error occurred


class ConflictResolution(Enum):
    """Strategies for resolving sync conflicts."""

    NEWEST_WINS = "newest_wins"     # Use the most recently modified version
    LARGEST_WINS = "largest_wins"   # Use the largest file (highest quality)
    PRIMARY_WINS = "primary_wins"   # Use version from highest priority location
    MANUAL = "manual"               # Require manual resolution


class SyncTracker:
    """Track synchronization status across storage locations."""

    def __init__(self, registry: StorageRegistry):
        """Initialize sync tracker.
        
        Args:
            registry: Storage location registry
        """
        self.registry = registry

    async def check_sync_status(
        self,
        content_hash: str
    ) -> dict[str, any]:
        """Check synchronization status for a file.
        
        Args:
            content_hash: SHA-256 hash of the file
            
        Returns:
            Sync status information
        """
        locations = self.registry.get_file_locations(content_hash)

        if not locations:
            return {
                'status': 'not_found',
                'locations': []
            }

        # Group by actual content (re-hash to detect changes)
        versions = {}
        for loc in locations:
            if loc['sync_status'] != 'error':
                # For local files, we could re-hash to detect changes
                # For now, use the stored hash
                version_key = content_hash

                if version_key not in versions:
                    versions[version_key] = []
                versions[version_key].append(loc)

        # Analyze sync status
        if len(versions) == 1:
            # All locations have same version
            return {
                'status': 'synced',
                'locations': locations,
                'version_count': 1
            }
        else:
            # Multiple versions exist - conflict
            return {
                'status': 'conflict',
                'locations': locations,
                'version_count': len(versions),
                'versions': versions
            }

    async def detect_conflicts(
        self,
        show_progress: bool = True
    ) -> list[dict[str, any]]:
        """Detect all files with sync conflicts.
        
        Args:
            show_progress: Show progress bar
            
        Returns:
            List of conflicts
        """
        logger.info("Detecting sync conflicts across locations")

        conflicts = []

        # Get all unique content hashes
        result = self.registry.conn.execute("""
            SELECT DISTINCT content_hash
            FROM file_locations
        """).fetchall()

        content_hashes = [row[0] for row in result]

        from tqdm import tqdm
        if show_progress:
            progress = tqdm(total=len(content_hashes), desc="Checking sync status")

        for content_hash in content_hashes:
            status = await self.check_sync_status(content_hash)

            if status['status'] == 'conflict':
                conflicts.append({
                    'content_hash': content_hash,
                    'status': status,
                    'locations': status['locations']
                })

            if show_progress:
                progress.update(1)

        if show_progress:
            progress.close()

        logger.info(f"Found {len(conflicts)} files with sync conflicts")
        return conflicts

    async def resolve_conflict(
        self,
        content_hash: str,
        strategy: ConflictResolution = ConflictResolution.NEWEST_WINS
    ) -> dict[str, any]:
        """Resolve a sync conflict using the specified strategy.
        
        Args:
            content_hash: File content hash
            strategy: Resolution strategy
            
        Returns:
            Resolution result
        """
        status = await self.check_sync_status(content_hash)

        if status['status'] != 'conflict':
            return {
                'resolved': False,
                'reason': 'No conflict to resolve'
            }

        locations = status['locations']

        # Choose winning version based on strategy
        winner = None

        if strategy == ConflictResolution.NEWEST_WINS:
            # Sort by last verified time
            winner = max(locations, key=lambda x: x['last_verified'])

        elif strategy == ConflictResolution.LARGEST_WINS:
            # Sort by file size
            winner = max(locations, key=lambda x: x['file_size'] or 0)

        elif strategy == ConflictResolution.PRIMARY_WINS:
            # Get location priorities
            location_priorities = {}
            for loc in locations:
                location = self.registry.get_location_by_id(loc['location_id'])
                if location:
                    location_priorities[loc['location_id']] = location.priority

            # Choose highest priority
            winner = max(
                locations,
                key=lambda x: location_priorities.get(x['location_id'], 0)
            )

        elif strategy == ConflictResolution.MANUAL:
            return {
                'resolved': False,
                'reason': 'Manual resolution required',
                'options': locations
            }

        if winner:
            # Mark winner as source of truth
            result = {
                'resolved': True,
                'winner': winner,
                'strategy': strategy.value,
                'actions': []
            }

            # Plan sync actions for other locations
            for loc in locations:
                if loc['location_id'] != winner['location_id']:
                    result['actions'].append({
                        'action': 'update',
                        'source': winner['location_id'],
                        'target': loc['location_id'],
                        'file': loc['file_path']
                    })

            return result

        return {
            'resolved': False,
            'reason': 'Could not determine winner'
        }

    async def sync_file(
        self,
        content_hash: str,
        source_location_id: str,
        target_location_id: str,
        scanner = None  # MultiPathScanner instance
    ) -> dict[str, any]:
        """Sync a file from source to target location.
        
        Args:
            content_hash: File content hash
            source_location_id: Source location ID
            target_location_id: Target location ID
            scanner: Optional MultiPathScanner for file transfers
            
        Returns:
            Sync result
        """
        # Get locations
        source_location = self.registry.get_location_by_id(source_location_id)
        target_location = self.registry.get_location_by_id(target_location_id)

        if not source_location or not target_location:
            return {
                'success': False,
                'error': 'Invalid location IDs'
            }

        # Get file info
        file_locations = self.registry.get_file_locations(content_hash)
        source_file = None

        for loc in file_locations:
            if loc['location_id'] == source_location_id:
                source_file = loc
                break

        if not source_file:
            return {
                'success': False,
                'error': 'File not found in source location'
            }

        # Mark for sync
        self.registry.mark_file_for_sync(
            content_hash,
            source_location_id,
            target_location_id,
            action='upload'
        )

        # Perform sync if scanner provided
        if scanner:
            try:
                await scanner._transfer_file(
                    source_file['file_path'],
                    content_hash,
                    target_location,
                    move=False  # Always copy for sync
                )

                return {
                    'success': True,
                    'source': source_file['file_path'],
                    'target': target_location.name
                }

            except Exception as e:
                logger.error(f"Sync failed: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }

        return {
            'success': True,
            'marked_for_sync': True
        }

    def get_sync_queue(self) -> list[dict[str, any]]:
        """Get all pending sync operations.
        
        Returns:
            List of pending syncs
        """
        return self.registry.get_pending_syncs()

    async def process_sync_queue(
        self,
        scanner = None,
        max_concurrent: int = 5,
        show_progress: bool = True
    ) -> dict[str, any]:
        """Process all pending sync operations.
        
        Args:
            scanner: MultiPathScanner for file transfers
            max_concurrent: Maximum concurrent operations
            show_progress: Show progress bar
            
        Returns:
            Processing statistics
        """
        pending = self.get_sync_queue()

        if not pending:
            logger.info("No pending sync operations")
            return {'processed': 0, 'failed': 0}

        logger.info(f"Processing {len(pending)} pending sync operations")

        stats = {
            'processed': 0,
            'failed': 0,
            'errors': []
        }

        from tqdm import tqdm
        if show_progress:
            progress = tqdm(total=len(pending), desc="Processing syncs")

        # Create semaphore for concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_one(sync_item):
            async with semaphore:
                try:
                    # Determine source and target
                    # This is simplified - real implementation would be more complex
                    if sync_item['sync_status'] == 'pending_upload':
                        # Find source location
                        all_locations = self.registry.get_file_locations(
                            sync_item['content_hash']
                        )

                        source_loc = None
                        for loc in all_locations:
                            if loc['sync_status'] == 'synced':
                                source_loc = loc
                                break

                        if source_loc and scanner:
                            result = await self.sync_file(
                                sync_item['content_hash'],
                                source_loc['location_id'],
                                sync_item['location_id'],
                                scanner
                            )

                            if result['success']:
                                stats['processed'] += 1
                            else:
                                stats['failed'] += 1
                                stats['errors'].append(result)

                except Exception as e:
                    logger.error(f"Error processing sync: {e}")
                    stats['failed'] += 1
                    stats['errors'].append({
                        'content_hash': sync_item['content_hash'],
                        'error': str(e)
                    })

                finally:
                    if show_progress:
                        progress.update(1)

        # Process all pending syncs
        tasks = [process_one(item) for item in pending]
        await asyncio.gather(*tasks, return_exceptions=True)

        if show_progress:
            progress.close()

        logger.info(
            f"Sync processing complete: {stats['processed']} succeeded, "
            f"{stats['failed']} failed"
        )

        return stats


class VersionTracker:
    """Track file versions across locations."""

    def __init__(self, registry: StorageRegistry):
        """Initialize version tracker.
        
        Args:
            registry: Storage location registry
        """
        self.registry = registry
        self.version_cache = {}  # content_hash -> version info

    async def track_version(
        self,
        content_hash: str,
        file_path: str,
        location_id: str,
        metadata: dict | None = None
    ) -> None:
        """Track a new version of a file.
        
        Args:
            content_hash: Current content hash
            file_path: File path
            location_id: Location ID
            metadata: Optional metadata
        """
        # In a real implementation, this would:
        # 1. Store version history
        # 2. Track parent/child relationships
        # 3. Store metadata changes

        version_info = {
            'content_hash': content_hash,
            'file_path': file_path,
            'location_id': location_id,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }

        if content_hash not in self.version_cache:
            self.version_cache[content_hash] = []

        self.version_cache[content_hash].append(version_info)

        logger.debug(f"Tracked version for {content_hash}")

    def get_version_history(
        self,
        content_hash: str
    ) -> list[dict[str, any]]:
        """Get version history for a file.
        
        Args:
            content_hash: Content hash
            
        Returns:
            Version history
        """
        return self.version_cache.get(content_hash, [])
