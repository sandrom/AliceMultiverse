"""Demo script for multi-path storage with progress tracking."""

import asyncio
import tempfile
from pathlib import Path

from PIL import Image

from alicemultiverse.storage.duckdb_cache import DuckDBSearchCache
from alicemultiverse.storage.location_registry import (
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)
from alicemultiverse.storage.multi_path_scanner import MultiPathScanner


def create_test_images(directory: Path, count: int = 50):
    """Create test images for demonstration."""
    print(f"Creating {count} test images in {directory}...")
    for i in range(count):
        img = Image.new('RGB', (100, 100), color=(i % 255, (i * 2) % 255, (i * 3) % 255))
        img.save(directory / f"test_image_{i:03d}.png", 'PNG')


async def main():
    """Run the storage progress demo."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test directories
        inbox = tmp_path / "inbox"
        organized = tmp_path / "organized"
        archive = tmp_path / "archive"
        
        inbox.mkdir()
        organized.mkdir()
        archive.mkdir()
        
        # Create test images in different locations
        create_test_images(inbox, 30)
        create_test_images(organized, 20)
        create_test_images(archive, 50)
        
        # Initialize storage system
        cache_db = tmp_path / "cache.db"
        registry_db = tmp_path / "registry.db"
        
        cache = DuckDBSearchCache(cache_db)
        registry = StorageRegistry(registry_db)
        
        print("\n📁 Setting up storage locations...")
        
        # Register storage locations with different priorities and rules
        locations = [
            StorageLocation(
                location_id=None,
                name="Inbox",
                type=StorageType.LOCAL,
                path=str(inbox),
                priority=100,
                rules=[
                    StorageRule(max_age_days=7)
                ]
            ),
            StorageLocation(
                location_id=None,
                name="Organized",
                type=StorageType.LOCAL,
                path=str(organized),
                priority=75,
                rules=[
                    StorageRule(min_age_days=7, max_age_days=30)
                ]
            ),
            StorageLocation(
                location_id=None,
                name="Archive",
                type=StorageType.LOCAL,
                path=str(archive),
                priority=50,
                rules=[
                    StorageRule(min_age_days=30)
                ]
            )
        ]
        
        for location in locations:
            registered = registry.register_location(location)
            print(f"  ✓ Registered {location.name} (priority: {location.priority})")
        
        # Create scanner
        scanner = MultiPathScanner(cache, registry)
        
        # Demo 1: Discover all assets with progress
        print("\n🔍 Discovering all assets across locations...")
        
        def progress_callback(message: str, current: int, total: int):
            print(f"  [{current}/{total}] {message}")
        
        stats = await scanner.discover_all_assets(
            force_scan=True,
            show_progress=True,
            progress_callback=progress_callback
        )
        
        print(f"\n📊 Discovery Results:")
        print(f"  - Locations scanned: {stats['locations_scanned']}")
        print(f"  - Total files found: {stats['total_files_found']}")
        print(f"  - New files discovered: {stats['new_files_discovered']}")
        print(f"  - Projects found: {len(stats['projects_found'])}")
        
        if stats['errors']:
            print(f"  - Errors: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"    • {error['location']}: {error['error']}")
        
        # Demo 2: Get location summary
        print("\n📈 Storage Location Summary:")
        summary = await scanner.get_location_summary()
        
        for loc in summary:
            print(f"\n  {loc['name']}:")
            print(f"    - Type: {loc['type']}")
            print(f"    - Status: {loc['status']}")
            print(f"    - Priority: {loc['priority']}")
            print(f"    - Files: {loc['file_count']}")
            print(f"    - Size: {loc['total_size_gb']:.2f} GB")
            print(f"    - Rules: {loc['rules']}")
        
        # Demo 3: Find project assets (simulate project structure)
        project_dir = organized / "my_project"
        project_dir.mkdir()
        create_test_images(project_dir, 10)
        
        # Re-scan to pick up project
        print("\n🔄 Re-scanning for project assets...")
        await scanner.discover_all_assets(force_scan=True, show_progress=False)
        
        print("\n🎯 Finding assets for project 'my_project'...")
        project_assets = await scanner.find_project_assets("my_project")
        print(f"  Found {len(project_assets)} assets in project")
        
        # Clean up
        cache.close()
        registry.close()
        
        print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())