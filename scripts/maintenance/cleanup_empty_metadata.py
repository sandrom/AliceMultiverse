#!/usr/bin/env python3
"""
Cleanup script to remove empty .metadata folders after migration
"""

import sys
from pathlib import Path

def cleanup_empty_metadata(root_dir: Path, dry_run: bool = False):
    """Remove empty .metadata folders"""
    print(f"Cleaning up empty .metadata folders in: {root_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()
    
    removed_count = 0
    
    # Find all .metadata folders (except the root one)
    for metadata_dir in root_dir.rglob(".metadata"):
        if metadata_dir == root_dir / ".metadata":
            continue  # Skip the central metadata folder
            
        # Check if directory is empty
        if metadata_dir.is_dir() and not any(metadata_dir.iterdir()):
            print(f"Removing empty folder: {metadata_dir.relative_to(root_dir)}")
            if not dry_run:
                metadata_dir.rmdir()
            removed_count += 1
    
    print(f"\n{'Would remove' if dry_run else 'Removed'} {removed_count} empty .metadata folders")
    
    if dry_run:
        print("\nRun without --dry-run to actually remove the folders.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Remove empty .metadata folders"
    )
    parser.add_argument(
        "directory",
        help="Root directory to clean"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be removed"
    )
    
    args = parser.parse_args()
    
    root_path = Path(args.directory)
    if not root_path.exists() or not root_path.is_dir():
        print(f"Error: Invalid directory: {root_path}")
        sys.exit(1)
    
    cleanup_empty_metadata(root_path, args.dry_run)

if __name__ == "__main__":
    main()