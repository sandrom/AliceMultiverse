"""Demo script for auto-migration based on storage rules."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image

from alicemultiverse.storage.auto_migration import AutoMigrationService
from alicemultiverse.storage.unified_duckdb import DuckDBSearchCache
from alicemultiverse.storage.location_registry import (
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)
from alicemultiverse.storage.multi_path_scanner import MultiPathScanner


def create_test_images_with_age(directory: Path, age_days: int, count: int = 5):
    """Create test images with specific age."""
    print(f"Creating {count} images aged {age_days} days in {directory}...")

    # Calculate timestamp
    file_date = datetime.now() - timedelta(days=age_days)

    for i in range(count):
        # Create image
        quality = (i % 5) + 1  # Quality 1-5
        img = Image.new('RGB', (100, 100), color=(quality * 50, 0, 0))

        # Add metadata
        metadata = {
            'created_date': file_date.isoformat(),
            'quality': {'overall_rating': quality}
        }

        # Save with metadata
        filepath = directory / f"image_age{age_days}_q{quality}_{i}.png"
        img.save(filepath, 'PNG', pnginfo=None)  # Simplified for demo

        # Touch file to set modification time
        import os
        timestamp = file_date.timestamp()
        os.utime(filepath, (timestamp, timestamp))


async def main():
    """Run the auto-migration demo."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create storage locations
        fast_ssd = tmp_path / "fast-ssd"
        archive_hdd = tmp_path / "archive-hdd"
        cold_storage = tmp_path / "cold-storage"

        fast_ssd.mkdir()
        archive_hdd.mkdir()
        cold_storage.mkdir()

        # Create test images of different ages
        create_test_images_with_age(fast_ssd, age_days=5, count=10)    # Recent files
        create_test_images_with_age(fast_ssd, age_days=45, count=10)   # Medium age
        create_test_images_with_age(fast_ssd, age_days=200, count=10)  # Old files

        # Initialize storage system
        cache_db = tmp_path / "cache.db"
        registry_db = tmp_path / "registry.db"

        cache = DuckDBSearchCache(cache_db)
        registry = StorageRegistry(registry_db)

        print("\n📁 Setting up storage locations with lifecycle rules...")

        # Register storage locations with rules
        locations = [
            StorageLocation(
                location_id=None,
                name="Fast SSD",
                type=StorageType.LOCAL,
                path=str(fast_ssd),
                priority=100,
                rules=[
                    StorageRule(max_age_days=30, min_quality_stars=4)
                ]
            ),
            StorageLocation(
                location_id=None,
                name="Archive HDD",
                type=StorageType.LOCAL,
                path=str(archive_hdd),
                priority=50,
                rules=[
                    StorageRule(min_age_days=31, max_age_days=180)
                ]
            ),
            StorageLocation(
                location_id=None,
                name="Cold Storage",
                type=StorageType.LOCAL,
                path=str(cold_storage),
                priority=25,
                rules=[
                    StorageRule(min_age_days=181)
                ]
            )
        ]

        for location in locations:
            registered = registry.register_location(location)
            print(f"  ✓ {location.name} - Priority: {location.priority}")
            for rule in location.rules:
                if rule.max_age_days:
                    print(f"    → Files newer than {rule.max_age_days} days")
                if rule.min_age_days:
                    print(f"    → Files older than {rule.min_age_days} days")
                if rule.min_quality_stars:
                    print(f"    → Quality >= {rule.min_quality_stars} stars")

        # Create scanner and discover files
        scanner = MultiPathScanner(cache, registry)

        print("\n🔍 Discovering files...")
        await scanner.discover_all_assets(force_scan=True, show_progress=False)

        # Create migration service
        migration_service = AutoMigrationService(cache, registry, scanner)

        # Run migration analysis (dry run)
        print("\n📊 Analyzing migrations (DRY RUN)...")
        results = await migration_service.run_auto_migration(
            dry_run=True,
            move_files=False,
            show_progress=True
        )

        # Display analysis
        analysis = results['analysis']
        print("\n📋 Migration Analysis:")
        print(f"  Files to migrate: {analysis['files_to_migrate']}")

        if analysis['migrations']:
            print("\n  Proposed migrations:")
            for i, migration in enumerate(analysis['migrations'][:10]):
                print(f"    {i+1}. {migration['file']}")
                print(f"       Size: {migration['size'] / 1024:.1f} KB")
                print(f"       From: {', '.join(migration['from'])}")
                print(f"       To: {migration['to']}")
                print(f"       Reason: {migration['reason']}")

        # Ask to proceed
        print("\n" + "="*60)
        print("Would you like to execute these migrations? (demo will proceed)")
        print("="*60)

        # Execute migrations
        print("\n🚀 Executing migrations...")
        results = await migration_service.run_auto_migration(
            dry_run=False,
            move_files=True,  # Move files to demonstrate
            show_progress=True
        )

        if results['execution']:
            exec_stats = results['execution']
            print("\n✅ Migration Results:")
            print(f"  Files migrated: {exec_stats['files_migrated']}")
            print(f"  Files failed: {exec_stats['files_failed']}")
            print(f"  Data transferred: {exec_stats['bytes_transferred'] / 1024:.1f} KB")

        # Show final file distribution
        print("\n📊 Final File Distribution:")
        for location in [fast_ssd, archive_hdd, cold_storage]:
            files = list(location.glob("*.png"))
            if files:
                print(f"\n  {location.name}:")
                for f in files[:5]:
                    print(f"    - {f.name}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")

        # Demo scheduler
        print("\n⏰ Migration Scheduler Demo:")
        print("  The MigrationScheduler can run migrations periodically:")
        print("  - Every 24 hours by default")
        print("  - Configurable interval")
        print("  - Runs in background")

        from alicemultiverse.storage.auto_migration import MigrationScheduler
        scheduler = MigrationScheduler(migration_service)
        # In production: await scheduler.start(interval_hours=24)

        # Clean up
        cache.close()
        registry.close()

        print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
