# Migration Guide: From Inbox/Organized to Multi-Path Storage

This guide helps you migrate from Alice's traditional inbox/organized folder structure to the new multi-path storage system that supports multiple locations with intelligent rules.

## Overview

The multi-path storage system allows you to:
- Store assets across multiple locations (local drives, network shares, cloud storage)
- Define rules for automatic file placement based on age, quality, type, and tags
- Track the same file across multiple locations for redundancy
- Consolidate projects to specific locations
- Prioritize storage locations for new files

## Migration Steps

### 1. Initialize Storage Registry

First, initialize the storage location registry:

```bash
alice storage init
```

This creates a new database to track your storage locations at `data/locations.duckdb`.

### 2. Configure Storage Locations

Update your `settings.yaml` to define storage locations:

```yaml
# Old structure (still supported for backward compatibility)
paths:
  inbox: ~/Downloads/ai-images
  organized: ~/Pictures/AI-Organized

# New multi-path structure
storage:
  # Databases
  search_db: data/search.duckdb
  location_registry_db: data/locations.duckdb
  
  # Disable legacy mode to use multi-path
  use_legacy_paths: false
  
  # Define your storage locations
  locations:
    # Fast SSD for recent work
    - name: "Primary SSD"
      type: "local"
      path: "~/Pictures/AI-Active"
      priority: 100  # Highest priority
      rules:
        - max_age_days: 30
        - min_quality_stars: 4
    
    # Slower storage for archives
    - name: "Archive HDD"
      type: "local"
      path: "/Volumes/Archive/AI-Images"
      priority: 50
      rules:
        - min_age_days: 30
```

### 3. Import Locations from Config

Load your configured storage locations:

```bash
alice storage from-config
```

### 4. Verify Storage Locations

Check that your locations are registered:

```bash
alice storage list
```

### 5. Discover Existing Assets

Scan your existing organized folder and any other locations:

```bash
# Discover all configured locations
alice storage discover

# Or scan specific location
alice storage scan <location-id>
```

### 6. Rebuild Search Index

Update the search index to include all locations:

```bash
alice index rebuild ~/Pictures/AI-Organized /Volumes/Archive/AI-Images
```

## Storage Rules

### Rule Types

- **Age Rules**: `max_age_days`, `min_age_days`
- **Quality Rules**: `min_quality_stars`, `max_quality_stars`
- **Type Rules**: `include_types`, `exclude_types`
- **Size Rules**: `min_size_bytes`, `max_size_bytes`
- **Tag Rules**: `require_tags`, `exclude_tags`

### Rule Examples

```yaml
# High-quality recent files on SSD
- name: "Fast SSD"
  priority: 100
  rules:
    - max_age_days: 7
    - min_quality_stars: 4

# Videos on dedicated drive
- name: "Video Storage"
  priority: 90
  rules:
    - include_types: ["video/mp4", "video/quicktime"]

# Team approved files on network
- name: "Team Share"
  priority: 75
  rules:
    - require_tags: ["approved", "final"]

# Long-term cold storage
- name: "Glacier Archive"
  priority: 10
  rules:
    - min_age_days: 365
    - exclude_tags: ["work-in-progress"]
```

## Working with Projects

### Find Project Assets

Locate all assets for a specific project:

```bash
alice storage find-project "MyProject"
alice storage find-project "MyProject" --type image/png --type image/jpeg
```

### Consolidate Projects

Move all project assets to a single location (future feature):

```bash
# Copy project to fast storage
alice storage consolidate "MyProject" --to "Primary SSD"

# Move project to archive
alice storage consolidate "MyProject" --to "Archive HDD" --move
```

## Monitoring and Maintenance

### View Statistics

Check storage usage across locations:

```bash
alice storage stats
```

### Update Location Status

Mark locations as offline or archived:

```bash
alice storage update --location-id <id> --status offline
alice storage update --location-id <id> --priority 25
```

## Best Practices

1. **Start Simple**: Begin with 2-3 locations and basic rules
2. **Test Rules**: Use `--dry-run` to preview where files would go
3. **Monitor Usage**: Regularly check `alice storage stats`
4. **Backup Critical Files**: Use multiple locations for important assets
5. **Review Rules**: Adjust rules based on actual usage patterns

## Backward Compatibility

The old inbox/organized structure remains fully supported:

```yaml
storage:
  use_legacy_paths: true  # Keep using old system
```

You can run both systems in parallel during migration.

## Troubleshooting

### Files Not Found
- Run `alice storage discover --force` to rescan all locations
- Check location status with `alice storage list`

### Wrong Location Assignment
- Review rules with `alice storage list --verbose`
- Check file metadata that rules depend on
- Adjust rule priorities if needed

### Performance Issues
- Index by location: `alice index update <path>`
- Consider splitting large locations
- Use SSDs for frequently accessed files

## Future Features

Planned enhancements include:
- Automatic file migration based on rules
- Cloud storage support (S3, GCS)
- Redundancy management
- Storage cost optimization
- Lifecycle policies