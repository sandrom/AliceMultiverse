"""Demo script for sync tracking and conflict resolution."""

import asyncio
import shutil
import tempfile
from pathlib import Path

from PIL import Image

from alicemultiverse.storage.unified_duckdb import DuckDBSearchCache
from alicemultiverse.storage.location_registry import (
    StorageLocation,
    StorageRegistry,
    StorageType,
)
from alicemultiverse.storage.multi_path_scanner import MultiPathScanner
from alicemultiverse.storage.sync_tracker import (
    ConflictResolution,
    SyncTracker,
    VersionTracker,
)


def create_test_image(path: Path, color: tuple = (255, 0, 0), size: tuple = (100, 100)):
    """Create a test image with specific color and size."""
    img = Image.new('RGB', size, color=color)
    img.save(path, 'PNG')


async def main():
    """Run the sync tracking demo."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create storage locations
        primary = tmp_path / "primary-storage"
        secondary = tmp_path / "secondary-storage"
        backup = tmp_path / "backup-storage"

        primary.mkdir()
        secondary.mkdir()
        backup.mkdir()

        # Initialize storage system
        cache_db = tmp_path / "cache.db"
        registry_db = tmp_path / "registry.db"

        cache = DuckDBSearchCache(cache_db)
        registry = StorageRegistry(registry_db)

        print("📁 Setting up storage locations...")

        # Register storage locations
        locations = [
            StorageLocation(
                location_id=None,
                name="Primary Storage",
                type=StorageType.LOCAL,
                path=str(primary),
                priority=100  # Highest priority
            ),
            StorageLocation(
                location_id=None,
                name="Secondary Storage",
                type=StorageType.LOCAL,
                path=str(secondary),
                priority=75
            ),
            StorageLocation(
                location_id=None,
                name="Backup Storage",
                type=StorageType.LOCAL,
                path=str(backup),
                priority=50
            )
        ]

        loc_ids = {}
        for location in locations:
            registered = registry.register_location(location)
            loc_ids[location.name] = registered.location_id
            print(f"  ✓ {location.name} (priority: {location.priority})")

        # Create scanner and tracker
        scanner = MultiPathScanner(cache, registry)
        tracker = SyncTracker(registry)
        version_tracker = VersionTracker(registry)

        # Demo 1: Create synchronized files
        print("\n📝 Creating synchronized files...")

        # Create same file in multiple locations
        test_file = "synced_image.png"
        create_test_image(primary / test_file, color=(0, 255, 0))  # Green
        shutil.copy2(primary / test_file, secondary / test_file)
        shutil.copy2(primary / test_file, backup / test_file)

        # Scan all locations
        await scanner.discover_all_assets(force_scan=True, show_progress=False)

        # Check sync status
        print("\n🔍 Checking sync status...")

        # Get the content hash of our test file
        results = cache.conn.execute("""
            SELECT DISTINCT content_hash 
            FROM assets 
            WHERE len(locations) > 0
        """).fetchall()

        if results:
            content_hash = results[0][0]
            status = await tracker.check_sync_status(content_hash)
            print(f"  File status: {status['status']}")
            print(f"  Locations: {len(status['locations'])}")

        # Demo 2: Create conflict by modifying file in one location
        print("\n⚠️  Creating sync conflict...")

        # Modify file in secondary location (make it larger)
        create_test_image(
            secondary / test_file,
            color=(255, 0, 0),  # Red
            size=(200, 200)     # Larger size
        )

        # Wait a moment to ensure different timestamps
        await asyncio.sleep(1)

        # Modify file in backup location (different change)
        create_test_image(
            backup / test_file,
            color=(0, 0, 255),  # Blue
            size=(150, 150)     # Medium size
        )

        # Clear cache and rescan to detect changes
        cache.conn.execute("DELETE FROM assets")
        await scanner.discover_all_assets(force_scan=True, show_progress=False)

        # Detect conflicts
        print("\n🔍 Detecting conflicts...")
        conflicts = await tracker.detect_conflicts(show_progress=False)

        print(f"  Found {len(conflicts)} conflicts")

        if conflicts:
            conflict = conflicts[0]
            print(f"  Conflict hash: {conflict['content_hash'][:16]}...")
            print(f"  Locations involved: {len(conflict['locations'])}")

        # Demo 3: Resolve conflicts with different strategies
        print("\n🔧 Resolving conflicts...")

        # Try different resolution strategies
        strategies = [
            (ConflictResolution.NEWEST_WINS, "Newest file wins"),
            (ConflictResolution.LARGEST_WINS, "Largest file wins"),
            (ConflictResolution.PRIMARY_WINS, "Primary location wins")
        ]

        for strategy, description in strategies:
            print(f"\n  Strategy: {description}")

            if conflicts:
                result = await tracker.resolve_conflict(
                    conflicts[0]['content_hash'],
                    strategy
                )

                if result['resolved']:
                    print(f"    ✓ Winner: {result['winner']['file_path']}")
                    print(f"    Actions needed: {len(result.get('actions', []))}")
                else:
                    print(f"    ✗ Could not resolve: {result['reason']}")

        # Demo 4: Sync queue processing
        print("\n📤 Processing sync queue...")

        # Mark some files for sync
        if results:
            registry.mark_file_for_sync(
                content_hash,
                str(loc_ids["Primary Storage"]),
                str(loc_ids["Secondary Storage"]),
                action="upload"
            )

        # Check pending syncs
        pending = tracker.get_sync_queue()
        print(f"  Pending sync operations: {len(pending)}")

        # Process sync queue
        sync_stats = await tracker.process_sync_queue(
            scanner=scanner,
            show_progress=False
        )

        print(f"  Processed: {sync_stats['processed']}")
        print(f"  Failed: {sync_stats['failed']}")

        # Demo 5: Version tracking
        print("\n📚 Version tracking demo...")

        if results:
            # Track versions
            for loc in ["Primary Storage", "Secondary Storage", "Backup Storage"]:
                await version_tracker.track_version(
                    content_hash,
                    str(Path(locations[0].path) / test_file),
                    str(loc_ids[loc]),
                    metadata={"location": loc, "demo": True}
                )

            # Get version history
            history = version_tracker.get_version_history(content_hash)
            print(f"  Version history entries: {len(history)}")

            for i, version in enumerate(history):
                print(f"    {i+1}. {version['location_id']} - {version['timestamp']}")

        # Clean up
        cache.close()
        registry.close()

        print("\n✅ Demo complete!")
        print("\nKey takeaways:")
        print("- Files can exist in multiple locations")
        print("- Conflicts occur when files differ across locations")
        print("- Multiple strategies available for conflict resolution")
        print("- Sync queue enables batch processing of updates")
        print("- Version tracking maintains history of changes")


if __name__ == "__main__":
    asyncio.run(main())
