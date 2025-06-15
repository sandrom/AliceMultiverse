"""Tests for sync tracking functionality."""

from uuid import uuid4

import pytest

from alicemultiverse.storage.location_registry import (
    StorageLocation,
    StorageRegistry,
    StorageType,
)
from alicemultiverse.storage.sync_tracker import (
    ConflictResolution,
    SyncTracker,
    VersionTracker,
)


class TestSyncTracker:
    """Test sync tracking functionality."""

    @pytest.mark.asyncio
    async def test_check_sync_status_synced(self, tmp_path):
        """Test checking sync status for synchronized files."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")

        # Register locations
        loc1 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 1",
            type=StorageType.LOCAL,
            path="/path1",
            priority=100
        ))

        loc2 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 2",
            type=StorageType.LOCAL,
            path="/path2",
            priority=50
        ))

        # Track same file in both locations
        content_hash = "test_hash_123"
        registry.track_file(content_hash, loc1.location_id, "/path1/file.png", 1024)
        registry.track_file(content_hash, loc2.location_id, "/path2/file.png", 1024)

        # Check sync status
        tracker = SyncTracker(registry)
        status = await tracker.check_sync_status(content_hash)

        assert status['status'] == 'synced'
        assert len(status['locations']) == 2
        assert status['version_count'] == 1

        registry.close()

    @pytest.mark.asyncio
    async def test_detect_conflicts(self, tmp_path):
        """Test detecting sync conflicts."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")

        # Register location
        loc1 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 1",
            type=StorageType.LOCAL,
            path="/path1",
            priority=100
        ))

        # Track files
        registry.track_file("hash1", loc1.location_id, "/path1/file1.png", 1024)
        registry.track_file("hash2", loc1.location_id, "/path1/file2.png", 2048)

        # Detect conflicts (none expected)
        tracker = SyncTracker(registry)
        conflicts = await tracker.detect_conflicts(show_progress=False)

        assert len(conflicts) == 0

        registry.close()

    @pytest.mark.asyncio
    async def test_resolve_conflict_newest_wins(self, tmp_path):
        """Test resolving conflicts with newest wins strategy."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")

        # Register locations
        loc1 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 1",
            type=StorageType.LOCAL,
            path="/path1",
            priority=100
        ))

        loc2 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 2",
            type=StorageType.LOCAL,
            path="/path2",
            priority=50
        ))

        # Track files with different timestamps
        content_hash = "conflict_hash"
        registry.track_file(content_hash, loc1.location_id, "/path1/file.png", 1024)

        # Update second location to have newer timestamp
        import time
        time.sleep(0.1)
        registry.track_file(content_hash, loc2.location_id, "/path2/file.png", 2048)

        # Resolve conflict
        tracker = SyncTracker(registry)
        result = await tracker.resolve_conflict(
            content_hash,
            ConflictResolution.NEWEST_WINS
        )

        # Should resolve with location 2 as winner (newer)
        assert result['resolved'] == True
        assert result['strategy'] == 'newest_wins'
        assert len(result['actions']) > 0

        registry.close()

    @pytest.mark.asyncio
    async def test_resolve_conflict_largest_wins(self, tmp_path):
        """Test resolving conflicts with largest wins strategy."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")

        # Register locations
        loc1 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 1",
            type=StorageType.LOCAL,
            path="/path1",
            priority=50
        ))

        loc2 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 2",
            type=StorageType.LOCAL,
            path="/path2",
            priority=100
        ))

        # Track files with different sizes
        content_hash = "size_conflict"
        registry.track_file(content_hash, loc1.location_id, "/path1/file.png", 1024)
        registry.track_file(content_hash, loc2.location_id, "/path2/file.png", 2048)

        # Resolve conflict
        tracker = SyncTracker(registry)
        result = await tracker.resolve_conflict(
            content_hash,
            ConflictResolution.LARGEST_WINS
        )

        # Should resolve with location 2 as winner (larger)
        assert result['resolved'] == True
        assert result['winner']['file_size'] == 2048

        registry.close()

    @pytest.mark.asyncio
    async def test_resolve_conflict_primary_wins(self, tmp_path):
        """Test resolving conflicts with primary wins strategy."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")

        # Register locations with different priorities
        loc1 = registry.register_location(StorageLocation(
            location_id=None,
            name="Primary",
            type=StorageType.LOCAL,
            path="/primary",
            priority=100  # Higher priority
        ))

        loc2 = registry.register_location(StorageLocation(
            location_id=None,
            name="Secondary",
            type=StorageType.LOCAL,
            path="/secondary",
            priority=50  # Lower priority
        ))

        # Track same file in both
        content_hash = "priority_conflict"
        registry.track_file(content_hash, loc1.location_id, "/primary/file.png", 1024)
        registry.track_file(content_hash, loc2.location_id, "/secondary/file.png", 1024)

        # Resolve conflict
        tracker = SyncTracker(registry)
        result = await tracker.resolve_conflict(
            content_hash,
            ConflictResolution.PRIMARY_WINS
        )

        # Should resolve with location 1 as winner (higher priority)
        assert result['resolved'] == True
        assert "/primary" in result['winner']['file_path']

        registry.close()

    def test_get_sync_queue(self, tmp_path):
        """Test getting pending sync operations."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")

        # Register location
        loc1 = registry.register_location(StorageLocation(
            location_id=None,
            name="Location 1",
            type=StorageType.LOCAL,
            path="/path1",
            priority=100
        ))

        # Mark file for sync
        content_hash = "pending_sync"
        registry.mark_file_for_sync(
            content_hash,
            str(loc1.location_id),
            str(uuid4()),  # Some other location
            action="upload"
        )

        # Get sync queue
        tracker = SyncTracker(registry)
        queue = tracker.get_sync_queue()

        assert len(queue) > 0
        assert queue[0]['content_hash'] == content_hash
        assert queue[0]['sync_status'] != 'synced'

        registry.close()


class TestVersionTracker:
    """Test version tracking functionality."""

    @pytest.mark.asyncio
    async def test_track_version(self, tmp_path):
        """Test tracking file versions."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")
        tracker = VersionTracker(registry)

        # Track versions
        content_hash = "version_test"

        await tracker.track_version(
            content_hash,
            "/path1/file.png",
            str(uuid4()),
            metadata={"version": 1}
        )

        await tracker.track_version(
            content_hash,
            "/path2/file.png",
            str(uuid4()),
            metadata={"version": 2}
        )

        # Get history
        history = tracker.get_version_history(content_hash)

        assert len(history) == 2
        assert history[0]['metadata']['version'] == 1
        assert history[1]['metadata']['version'] == 2

        registry.close()

    def test_empty_version_history(self, tmp_path):
        """Test getting version history for unknown file."""
        # Setup
        registry = StorageRegistry(tmp_path / "registry.db")
        tracker = VersionTracker(registry)

        # Get history for unknown hash
        history = tracker.get_version_history("unknown_hash")

        assert len(history) == 0

        registry.close()
