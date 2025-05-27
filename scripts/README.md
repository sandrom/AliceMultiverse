# Scripts Directory

Utility scripts for development, maintenance, and monitoring of AliceMultiverse.

## Main Scripts

- **alice.py** - Direct CLI entry point for development
- **event_monitor.py** - Real-time event monitoring with metrics
- **setup_api_keys.sh** - Interactive API key setup wizard

## Subdirectories

### database/
Database management scripts:
- **init_db.py** - Initialize the AliceMultiverse database with proper schema

### maintenance/
One-time maintenance and cleanup scripts:
- **cleanup_project.sh** - Remove temporary files and build artifacts
- **cleanup_empty_metadata.py** - Remove empty .metadata folders
- **cleanup_root.py** - Organize files in the project root
- **migrate_metadata.py** - Migrate from old to new metadata format
- **remove_duplicates.py** - Find and remove duplicate media files
- **remove_old_metadata.py** - Clean up outdated metadata files

## Usage Examples

### Event Monitoring
```bash
# Monitor all events in real-time
python scripts/event_monitor.py

# Verbose mode with full event data
python scripts/event_monitor.py --verbose

# Collect metrics
python scripts/event_monitor.py --metrics
```

### Database Setup
```bash
# Initialize the database
python scripts/database/init_db.py
```

### Project Cleanup
```bash
# Remove temporary files
./scripts/maintenance/cleanup_project.sh

# Clean empty metadata folders
python scripts/maintenance/cleanup_empty_metadata.py
```

## Note

For main functionality, use the `alice` command directly:
```bash
# Organize media
alice -i ~/Downloads -o ~/Pictures/AI

# Manage API keys
alice keys setup

# Start AI interface
alice interface
```