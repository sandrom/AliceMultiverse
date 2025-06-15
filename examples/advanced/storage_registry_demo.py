"""Demo of the storage location registry system.

This example shows how to:
1. Set up multiple storage locations with different rules
2. Track files across locations
3. Determine optimal storage for new files
4. Query file locations and statistics
"""

import hashlib
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alicemultiverse.storage import (
    LocationStatus,
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    """Run the storage registry demo."""
    print("=== Storage Location Registry Demo ===\n")

    # Create registry (in-memory for demo)
    registry = StorageRegistry()

    # 1. Set up storage locations
    print("1. Setting up storage locations...")

    # Hot storage for recent, high-quality files
    hot_storage = StorageLocation(
        location_id=uuid4(),
        name="Hot SSD Storage",
        type=StorageType.LOCAL,
        path="/mnt/ssd/media/hot",
        priority=100,  # Highest priority
        rules=[
            StorageRule(
                max_age_days=7,  # Only files less than 7 days old
                min_quality_stars=4,  # Only high quality
                include_types=["image/jpeg", "image/png", "image/webp"],
                max_size_bytes=50_000_000  # Max 50MB
            )
        ],
        status=LocationStatus.ACTIVE
    )

    # Standard storage for medium-term files
    standard_storage = StorageLocation(
        location_id=uuid4(),
        name="Standard HDD Storage",
        type=StorageType.LOCAL,
        path="/mnt/hdd/media/standard",
        priority=75,
        rules=[
            StorageRule(
                max_age_days=90,  # Files up to 90 days old
                min_age_days=7,   # But older than 7 days
                min_quality_stars=3  # Medium quality or better
            )
        ],
        status=LocationStatus.ACTIVE
    )

    # Cloud archive for old or low-quality files
    archive_storage = StorageLocation(
        location_id=uuid4(),
        name="S3 Archive",
        type=StorageType.S3,
        path="my-media-archive",
        priority=50,
        rules=[
            StorageRule(
                min_age_days=90,  # Files older than 90 days
                max_quality_stars=2  # Or low quality files
            )
        ],
        status=LocationStatus.ACTIVE,
        config={
            "region": "us-west-2",
            "storage_class": "GLACIER",
            "lifecycle_rules": {"transition_days": 30}
        }
    )

    # Backup storage (accepts everything)
    backup_storage = StorageLocation(
        location_id=uuid4(),
        name="GCS Backup",
        type=StorageType.GCS,
        path="my-media-backup",
        priority=25,
        rules=[],  # No rules - accepts all files
        status=LocationStatus.ACTIVE,
        config={
            "project": "my-project",
            "location": "us-central1",
            "storage_class": "NEARLINE"
        }
    )

    # Register all locations
    for location in [hot_storage, standard_storage, archive_storage, backup_storage]:
        registry.register_location(location)
        print(f"  ✓ Registered: {location.name} (priority: {location.priority})")

    print("\n2. Simulating file processing...")

    # Simulate different types of files
    test_files = [
        {
            "name": "hero_shot.jpg",
            "hash": "abc123" + "0" * 58,  # Fake hash for demo
            "metadata": {
                "age_days": 2,
                "quality_stars": 5,
                "file_type": "image/jpeg",
                "file_size": 3_500_000,  # 3.5MB
                "tags": ["hero", "approved", "production"],
                "created_at": datetime.now() - timedelta(days=2)
            }
        },
        {
            "name": "draft_concept.png",
            "hash": "def456" + "0" * 58,
            "metadata": {
                "age_days": 15,
                "quality_stars": 3,
                "file_type": "image/png",
                "file_size": 8_000_000,  # 8MB
                "tags": ["draft", "concept"],
                "created_at": datetime.now() - timedelta(days=15)
            }
        },
        {
            "name": "old_archive.jpg",
            "hash": "ghi789" + "0" * 58,
            "metadata": {
                "age_days": 120,
                "quality_stars": 2,
                "file_type": "image/jpeg",
                "file_size": 1_200_000,  # 1.2MB
                "tags": ["archive", "historical"],
                "created_at": datetime.now() - timedelta(days=120)
            }
        },
        {
            "name": "large_video.mp4",
            "hash": "jkl012" + "0" * 58,
            "metadata": {
                "age_days": 5,
                "quality_stars": 4,
                "file_type": "video/mp4",
                "file_size": 150_000_000,  # 150MB
                "tags": ["video", "production"],
                "created_at": datetime.now() - timedelta(days=5)
            }
        }
    ]

    # Process each file
    for file_info in test_files:
        print(f"\n  Processing: {file_info['name']}")
        print(f"    Age: {file_info['metadata']['age_days']} days")
        print(f"    Quality: {file_info['metadata']['quality_stars']} stars")
        print(f"    Type: {file_info['metadata']['file_type']}")
        print(f"    Size: {file_info['metadata']['file_size'] / 1_000_000:.1f} MB")

        # Determine best location
        location = registry.get_location_for_file(
            file_info["hash"],
            file_info["metadata"]
        )

        print(f"    → Best location: {location.name}")

        # Track the file
        file_path = f"{location.path}/{file_info['name']}"
        registry.track_file(
            content_hash=file_info["hash"],
            location_id=location.location_id,
            file_path=file_path,
            file_size=file_info["metadata"]["file_size"],
            metadata_embedded=True
        )

        print(f"    ✓ Tracked at: {file_path}")

    print("\n3. Querying file locations...")

    # Query specific files
    for file_info in test_files[:2]:  # Just first two
        print(f"\n  Locations for {file_info['name']}:")
        locations = registry.get_file_locations(file_info["hash"])
        for loc in locations:
            print(f"    - {loc['location_name']}: {loc['file_path']}")
            print(f"      Last verified: {loc['last_verified']}")
            print(f"      Metadata embedded: {loc['metadata_embedded']}")

    print("\n4. Simulating file duplication for backup...")

    # Duplicate hero shot to backup
    hero_file = test_files[0]
    print(f"\n  Backing up {hero_file['name']} to GCS...")

    registry.track_file(
        content_hash=hero_file["hash"],
        location_id=backup_storage.location_id,
        file_path=f"{backup_storage.path}/backups/2024/{hero_file['name']}",
        file_size=hero_file["metadata"]["file_size"],
        metadata_embedded=True
    )

    # Now check locations again
    locations = registry.get_file_locations(hero_file["hash"])
    print(f"  File now exists in {len(locations)} locations:")
    for loc in locations:
        print(f"    - {loc['location_name']}")

    print("\n5. Storage statistics...")

    stats = registry.get_statistics()
    print(f"\n  Total storage locations: {stats['total_locations']}")
    print("  Locations by type:")
    for storage_type, count in stats['by_type'].items():
        print(f"    - {storage_type}: {count}")

    print(f"\n  Total unique files: {stats['total_unique_files']}")
    print(f"  Total file instances: {stats['total_file_instances']}")
    print(f"  Files with multiple copies: {stats['files_with_multiple_copies']}")

    print("\n  Storage usage by location:")
    for loc_stat in stats['by_location']:
        size_mb = loc_stat['total_size_bytes'] / 1_000_000
        print(f"    - {loc_stat['name']}: {loc_stat['file_count']} files, {size_mb:.1f} MB")

    print("\n6. Simulating location scan...")

    # Scan hot storage
    print(f"\n  Scanning {hot_storage.name}...")
    scan_results = registry.scan_location(hot_storage.location_id)
    print(f"  Scan completed at: {scan_results['scan_time']}")
    print(f"  Files discovered: {scan_results['files_discovered']} (placeholder)")

    # Check that last_scan was updated
    updated_location = registry.get_location_by_id(hot_storage.location_id)
    print(f"  Location last_scan updated: {updated_location.last_scan is not None}")

    print("\n7. Testing sync operations...")

    # Mark old file for sync from standard to archive
    old_file = test_files[2]  # old_archive.jpg
    print(f"\n  Marking {old_file['name']} for archive sync...")

    # First track it in standard storage
    registry.track_file(
        content_hash=old_file["hash"],
        location_id=standard_storage.location_id,
        file_path=f"{standard_storage.path}/{old_file['name']}",
        file_size=old_file["metadata"]["file_size"]
    )

    # Mark for sync to archive
    registry.mark_file_for_sync(
        content_hash=old_file["hash"],
        source_location_id=standard_storage.location_id,
        target_location_id=archive_storage.location_id,
        action="upload"
    )

    # Check pending syncs
    pending = registry.get_pending_syncs()
    print(f"  Pending sync operations: {len(pending)}")
    for sync in pending:
        print(f"    - {sync['content_hash'][:12]}... from {sync['location_name']}: {sync['sync_status']}")

    print("\n8. Advanced rule examples...")

    # Create a specialized location for AI-generated content
    ai_storage = StorageLocation(
        location_id=uuid4(),
        name="AI Generated Content",
        type=StorageType.LOCAL,
        path="/mnt/ssd/ai-generated",
        priority=90,
        rules=[
            StorageRule(
                require_tags=["ai-generated", "stable-diffusion"],
                min_quality_stars=4,
                max_size_bytes=10_000_000,  # 10MB max
                include_types=["image/png", "image/webp"]
            )
        ],
        status=LocationStatus.ACTIVE
    )

    registry.register_location(ai_storage)

    # Test with AI-generated file
    ai_file = {
        "name": "sd_artwork.png",
        "hash": "xyz999" + "0" * 58,
        "metadata": {
            "age_days": 1,
            "quality_stars": 5,
            "file_type": "image/png",
            "file_size": 4_000_000,
            "tags": ["ai-generated", "stable-diffusion", "artwork"]
        }
    }

    location = registry.get_location_for_file(ai_file["hash"], ai_file["metadata"])
    print(f"\n  AI-generated file would go to: {location.name}")

    # Close registry
    registry.close()
    print("\n✓ Demo completed!")


if __name__ == "__main__":
    main()
