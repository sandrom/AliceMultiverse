# Scripts Directory

This directory contains command-line scripts for AliceMultiverse.

## Main Scripts

All main functionality has been moved to the modular `alicemultiverse` package. The scripts here are thin wrappers for backward compatibility:

- **alice.py** - Main entry point (runs `alicemultiverse.cli`)
- **organizer.py** - Legacy wrapper (forwards to `alice` command)
- **quality_pipeline.py** - Legacy wrapper (forwards to `alice` command)
- **quality_organizer_integration.py** - Legacy wrapper (forwards to `alice` command)
- **api_key_manager.py** - Legacy wrapper (forwards to `alice keys` command)

## Utility Scripts

These are one-time maintenance scripts:

- **cleanup_empty_metadata.py** - Remove empty .metadata folders after migration
- **cleanup_root.py** - Organize project root directory
- **migrate_metadata.py** - Migrate from old to new metadata format
- **remove_duplicates.py** - Find and remove duplicate files
- **remove_old_metadata.py** - Clean up old metadata files
- **setup_api_keys.sh** - Shell script for API key setup

## Usage

Instead of running scripts directly, use the `alice` command:

```bash
# Instead of: python scripts/organizer.py inbox
alice -i inbox

# Instead of: python scripts/api_key_manager.py setup
alice keys setup

# Instead of: python scripts/quality_pipeline.py --pipeline premium
alice --pipeline premium
```

## Note

The old script implementations (3,700+ lines) have been archived to `archive/old_scripts/`. The modular implementation in `alicemultiverse/` provides the same functionality with better maintainability.