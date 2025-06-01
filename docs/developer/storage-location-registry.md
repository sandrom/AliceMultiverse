# Storage Location Registry

The Storage Location Registry system enables AliceMultiverse to track files across multiple storage locations (local, S3, GCS, network drives) using content-addressed storage with SHA-256 hashes.

## Key Features

- **Multi-location tracking**: Track the same file across multiple storage locations
- **Rule-based placement**: Automatically determine optimal storage based on file metadata
- **Content-addressed**: Files tracked by SHA-256 hash, enabling deduplication
- **Storage tiering**: Support for hot/warm/cold storage strategies
- **Sync management**: Track and manage file synchronization between locations

## Architecture

### Core Components

1. **StorageLocation**: Represents a storage location with rules and configuration
2. **StorageRule**: Defines criteria for file placement (age, quality, type, tags)
3. **StorageRegistry**: Main registry managing locations and file tracking
4. **DuckDB Backend**: Fast analytical database for queries and statistics

### Database Schema

- `storage_locations`: Registry of storage locations
- `file_locations`: Tracks where each file exists
- `rule_evaluations`: Caches rule evaluation results

## Usage Example

```python
from alicemultiverse.storage import (
    StorageRegistry,
    StorageLocation,
    StorageRule,
    StorageType,
    LocationStatus
)

# Create registry
registry = StorageRegistry()

# Define storage location with rules
hot_storage = StorageLocation(
    name="Hot SSD Storage",
    type=StorageType.LOCAL,
    path="/mnt/ssd/media",
    priority=100,  # Higher = preferred
    rules=[
        StorageRule(
            max_age_days=7,
            include_tags=["hero", "featured"],
            include_types=["image/jpeg", "image/png"]
        )
    ],
    status=LocationStatus.ACTIVE
)

# Register location
registry.register_location(hot_storage)

# Determine best location for a file
metadata = {
    "age_days": 2,
    "tags": ["hero", "production", "portrait"],
    "file_type": "image/jpeg",
    "file_size": 1024000,
    "tags": ["hero", "production"]
}

location = registry.get_location_for_file("content_hash", metadata)

# Track file in location
registry.track_file(
    content_hash="abc123...",
    location_id=location.location_id,
    file_path="/mnt/ssd/media/image.jpg",
    file_size=1024000,
    metadata_embedded=True
)
```

## Storage Rules

Rules determine which files should be stored in each location:

- **Age rules**: `max_age_days`, `min_age_days`
- **Tag rules**: `include_tags`, `exclude_tags`
- **Type rules**: `include_types`, `exclude_types` (MIME types)
- **Size rules**: `max_size_bytes`, `min_size_bytes`
- **Tag rules**: `require_tags`, `exclude_tags`

## Storage Types

- `LOCAL`: Local filesystem
- `S3`: Amazon S3 or compatible
- `GCS`: Google Cloud Storage
- `NETWORK`: Network drives (SMB, NFS)

## Advanced Features

### Multi-Location Tracking

The same file can exist in multiple locations:

```python
# Get all locations for a file
locations = registry.get_file_locations("content_hash")
for loc in locations:
    print(f"{loc['location_name']}: {loc['file_path']}")
```

### Sync Management

Mark files for synchronization between locations:

```python
registry.mark_file_for_sync(
    content_hash="abc123...",
    source_location_id=hot_storage.location_id,
    target_location_id=archive_storage.location_id,
    action="upload"
)

# Get pending syncs
pending = registry.get_pending_syncs()
```

### Statistics

Get comprehensive statistics about storage usage:

```python
stats = registry.get_statistics()
print(f"Total files: {stats['total_unique_files']}")
print(f"Total instances: {stats['total_file_instances']}")
print(f"Files with duplicates: {stats['files_with_multiple_copies']}")
```

## Integration with AliceMultiverse

The storage registry integrates with the existing file-first architecture:

1. Files maintain embedded metadata
2. Registry tracks locations by content hash
3. Supports the existing understanding and tagging system
4. Works with the asset organization system

## Future Enhancements

- Actual cloud storage integration (S3, GCS)
- Automatic sync orchestration
- Storage cost optimization
- Lifecycle policies
- Bandwidth-aware sync scheduling