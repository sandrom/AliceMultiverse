# Multi-Path Storage Guide

The multi-path storage system enables you to manage your AI-generated assets across multiple storage locations, including local drives, network storage, and cloud services (S3, GCS). This guide covers all features of the system.

## Overview

Multi-path storage provides:
- **Multiple storage locations** with priorities and rules
- **Automatic file placement** based on age, type, size, and quality
- **Cloud storage integration** (Amazon S3, Google Cloud Storage)
- **Lifecycle management** with auto-migration
- **Sync tracking** and conflict resolution
- **Progress tracking** for long operations

## Configuration

Configure storage locations in your `settings.yaml`:

```yaml
storage:
  # Database locations
  search_db: data/search.duckdb
  location_registry_db: data/locations.duckdb
  
  # Storage locations with rules
  locations:
    - name: "Fast SSD"
      type: "local"
      path: "~/Pictures/AI-Active"
      priority: 100  # Higher = preferred
      rules:
        - max_age_days: 30
          min_quality_stars: 4
    
    - name: "Archive HDD"
      type: "local"
      path: "/Volumes/Archive/AI"
      priority: 50
      rules:
        - min_age_days: 30
          max_age_days: 180
    
    - name: "S3 Cold Storage"
      type: "s3"
      path: "my-ai-archive-bucket"
      priority: 25
      config:
        region: "us-west-2"
        prefix: "alice-archive/"
      rules:
        - min_age_days: 180
```

## CLI Commands

### Initialize Storage System

```bash
# Initialize from configuration
alice storage from-config

# Or initialize empty
alice storage init
```

### Manage Storage Locations

```bash
# List all locations
alice storage list

# Add a new location
alice storage add --name "Backup Drive" --path "/mnt/backup" --priority 75

# Add with rules
alice storage add --name "Premium Storage" \
  --path "/fast/storage" \
  --priority 100 \
  --rule '{"max_age_days": 30, "min_quality_stars": 4}'

# Update location
alice storage update --location-id <id> --priority 90 --status active
```

### Discover and Scan Files

```bash
# Discover all assets across all locations
alice storage discover

# Scan specific location
alice storage scan <location-id>

# Find project assets
alice storage find-project "my-project" --type image --type video
```

### Auto-Migration

```bash
# Preview migrations (dry run)
alice storage migrate --dry-run

# Execute migrations (copy files)
alice storage migrate

# Move files instead of copying
alice storage migrate --move

# Disable progress bars
alice storage migrate --no-progress
```

### Consolidate Projects

```bash
# Consolidate project to single location
alice storage consolidate "my-project" <target-location-id>

# Move files instead of copying
alice storage consolidate "my-project" <target-location-id> --move
```

### Sync Management

```bash
# Check sync status
alice storage sync-status

# Resolve conflicts
alice storage resolve-conflict <content-hash> --strategy newest
# Strategies: newest, largest, primary, manual

# Process sync queue
alice storage sync-process --max-concurrent 10
```

## Storage Rules

Storage rules determine where files are automatically placed:

### Rule Types

1. **Age Rules**
   - `max_age_days`: Files newer than N days
   - `min_age_days`: Files older than N days

2. **Type Rules**
   - `include_types`: Only these file types
   - `exclude_types`: Exclude these file types

3. **Size Rules**
   - `max_size_bytes`: Files smaller than N bytes
   - `min_size_bytes`: Files larger than N bytes

4. **Tag Rules**
   - `require_tags`: Must have all these tags
   - `exclude_tags`: Must not have any of these tags

5. **Quality Rules**
   - `min_quality_stars`: Minimum quality rating
   - `max_quality_stars`: Maximum quality rating

### Rule Examples

```yaml
# High-quality recent work on fast storage
- max_age_days: 30
  min_quality_stars: 4

# Archive old files except videos
- min_age_days: 180
  exclude_types: ["video/mp4", "video/mov"]

# Large files to specific location
- min_size_bytes: 104857600  # 100MB

# Tagged content
- require_tags: ["portfolio", "client-work"]
```

## Cloud Storage

### Amazon S3

```yaml
- name: "S3 Archive"
  type: "s3"
  path: "my-bucket-name"
  priority: 50
  config:
    # Optional: specify credentials
    aws_access_key_id: "YOUR_KEY"
    aws_secret_access_key: "YOUR_SECRET"
    region: "us-west-2"
    prefix: "alice/"  # Optional prefix
```

Required: `pip install boto3`

### Google Cloud Storage

```yaml
- name: "GCS Backup"
  type: "gcs"
  path: "my-bucket-name"
  priority: 50
  config:
    # Optional: service account key
    credentials_path: "~/path/to/key.json"
    prefix: "alice/"
```

Required: `pip install google-cloud-storage`

## Sync Tracking

The sync tracking system monitors file consistency across locations:

### Sync Status Types
- **Synced**: All locations have the same version
- **Pending Upload**: Needs to be uploaded to location
- **Pending Update**: Newer version available
- **Conflict**: Different versions in different locations
- **Missing**: File missing from expected location

### Conflict Resolution Strategies
1. **Newest Wins**: Use the most recently modified version
2. **Largest Wins**: Use the largest file (assumed higher quality)
3. **Primary Wins**: Use version from highest priority location
4. **Manual**: Require manual intervention

## Progress Tracking

All long-running operations show progress bars by default:

```bash
# Progress enabled by default
alice storage discover

# Disable progress
alice storage discover --no-progress

# Custom progress in scripts
async def progress_callback(message: str, current: int, total: int):
    print(f"[{current}/{total}] {message}")

await scanner.discover_all_assets(
    show_progress=True,
    progress_callback=progress_callback
)
```

## Python API

```python
from alicemultiverse.storage.location_registry import StorageRegistry, StorageLocation
from alicemultiverse.storage.multi_path_scanner import MultiPathScanner
from alicemultiverse.storage.auto_migration import AutoMigrationService
from alicemultiverse.storage.sync_tracker import SyncTracker

# Initialize
registry = StorageRegistry(Path("data/locations.db"))
cache = DuckDBSearchCache(Path("data/search.duckdb"))
scanner = MultiPathScanner(cache, registry)

# Discover assets
stats = await scanner.discover_all_assets(force_scan=True)

# Find project assets
assets = await scanner.find_project_assets("my-project")

# Auto-migration
migration_service = AutoMigrationService(cache, registry, scanner)
results = await migration_service.run_auto_migration(dry_run=True)

# Sync tracking
tracker = SyncTracker(registry)
conflicts = await tracker.detect_conflicts()
```

## Best Practices

1. **Priority Strategy**
   - Highest priority (100): Fast, frequently accessed storage
   - Medium priority (50-75): Secondary storage, archives
   - Low priority (0-25): Cold storage, backups

2. **Rule Design**
   - Start simple, add complexity as needed
   - Test rules with dry-run before applying
   - Monitor migration patterns

3. **Sync Management**
   - Regular sync-status checks
   - Automate conflict resolution where possible
   - Keep primary location as source of truth

4. **Performance**
   - Use progress tracking for large operations
   - Limit concurrent operations for network/cloud storage
   - Schedule migrations during off-peak times

## Examples

See the `examples/advanced/` directory for complete examples:
- `storage_progress_demo.py` - Progress tracking demonstration
- `auto_migration_demo.py` - Lifecycle management example
- `sync_tracking_demo.py` - Conflict detection and resolution
- `cloud_storage_config.yaml` - Cloud configuration example