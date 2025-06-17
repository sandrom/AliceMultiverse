#!/usr/bin/env python3
"""Demo script for multi-path storage functionality."""

import asyncio
import logging
from pathlib import Path
from uuid import uuid4

from alicemultiverse.core.config import load_config
from alicemultiverse.storage.location_registry import (
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)
from alicemultiverse.storage.multi_path_scanner import MultiPathScanner
from alicemultiverse.storage.unified_duckdb import DuckDBSearchCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run multi-path storage demo."""
    # Load configuration
    config = load_config()

    # Setup paths
    demo_dir = Path("demo_multipath")
    demo_dir.mkdir(exist_ok=True)

    # Create test locations
    primary_dir = demo_dir / "primary"
    archive_dir = demo_dir / "archive"
    primary_dir.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)

    print("🚀 Multi-Path Storage Demo\n")

    # Initialize storage components
    cache_db = demo_dir / "search.duckdb"
    registry_db = demo_dir / "locations.duckdb"

    cache = DuckDBSearchCache(cache_db)
    registry = StorageRegistry(registry_db)
    scanner = MultiPathScanner(cache, registry)

    print("1️⃣ Registering storage locations...")

    # Register primary storage (for recent, high-quality files)
    primary_location = StorageLocation(
        location_id=uuid4(),
        name="Primary SSD",
        type=StorageType.LOCAL,
        path=str(primary_dir.absolute()),
        priority=100,
        rules=[
            StorageRule(max_age_days=30, min_quality_stars=4)
        ]
    )
    registry.register_location(primary_location)
    print(f"   ✅ Registered: {primary_location.name} (priority: {primary_location.priority})")

    # Register archive storage (for older files)
    archive_location = StorageLocation(
        location_id=uuid4(),
        name="Archive HDD",
        type=StorageType.LOCAL,
        path=str(archive_dir.absolute()),
        priority=50,
        rules=[
            StorageRule(min_age_days=30)
        ]
    )
    registry.register_location(archive_location)
    print(f"   ✅ Registered: {archive_location.name} (priority: {archive_location.priority})")

    print("\n2️⃣ Listing all storage locations...")
    locations = registry.get_locations()
    for loc in locations:
        print(f"   📁 {loc.name}: {loc.path} (priority: {loc.priority})")

    print("\n3️⃣ Testing storage rules...")

    # Test file metadata
    new_file_metadata = {
        "age_days": 5,
        "quality_stars": 5,
        "file_type": "image/png"
    }

    old_file_metadata = {
        "age_days": 60,
        "quality_stars": 3,
        "file_type": "image/jpeg"
    }

    # Test where files would be stored
    new_file_location = registry.get_location_for_file("hash123", new_file_metadata)
    print(f"   🆕 New high-quality file → {new_file_location.name}")

    old_file_location = registry.get_location_for_file("hash456", old_file_metadata)
    print(f"   📦 Old file → {old_file_location.name}")

    print("\n4️⃣ Storage statistics...")
    stats = registry.get_statistics()
    print(f"   Total locations: {stats['total_locations']}")
    print(f"   By type: {stats['by_type']}")
    print(f"   Total unique files: {stats['total_unique_files']}")

    print("\n5️⃣ Location summary...")
    summaries = await scanner.get_location_summary()
    for summary in summaries:
        print(f"   {summary['name']}:")
        print(f"     - Files: {summary['file_count']}")
        print(f"     - Size: {summary['total_size_gb']:.2f} GB")
        print(f"     - Last scan: {summary['last_scan'] or 'Never'}")

    # Cleanup
    cache.close()
    registry.close()

    print("\n✅ Demo complete! Check the 'demo_multipath' directory for the databases.")
    print("\nNext steps:")
    print("1. Run 'alice storage discover' to scan actual media files")
    print("2. Use 'alice storage find-project <name>' to find project assets")
    print("3. Configure rules in settings.yaml for automatic placement")


if __name__ == "__main__":
    asyncio.run(main())
