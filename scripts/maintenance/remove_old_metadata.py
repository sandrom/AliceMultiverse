#!/usr/bin/env python3
"""
Remove old .metadata folders after successful migration.
Only removes if the central .metadata folder exists with files.
"""

import shutil
import sys
from pathlib import Path


def remove_old_metadata(inbox_dir: Path, dry_run: bool = False):
    """Remove old scattered .metadata folders"""
    print(f"Removing old .metadata folders in: {inbox_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Check if central metadata exists and has files
    central_metadata = inbox_dir / ".metadata"
    if not central_metadata.exists():
        print("ERROR: Central .metadata folder not found!")
        print("Please run migrate_metadata.py first.")
        return

    metadata_files = list(central_metadata.glob("*.json"))
    if not metadata_files:
        print("ERROR: Central .metadata folder is empty!")
        print("Please run migrate_metadata.py first.")
        return

    print(f"✓ Central .metadata contains {len(metadata_files)} files")
    print()

    # Find all old metadata folders (excluding central one)
    old_folders = []
    for item in inbox_dir.rglob(".metadata"):
        if item.is_dir() and item != central_metadata:
            old_folders.append(item)

    if not old_folders:
        print("No old .metadata folders found.")
        return

    print(f"Found {len(old_folders)} old .metadata folders to remove:")

    removed_count = 0
    file_count = 0

    for folder in sorted(old_folders):
        # Count files in folder
        json_files = list(folder.glob("*.json"))
        file_count += len(json_files)

        print(f"  - {folder.relative_to(inbox_dir)} ({len(json_files)} files)")

        if not dry_run:
            shutil.rmtree(folder)
            removed_count += 1

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Folders to remove: {len(old_folders)}")
    print(f"Total files to remove: {file_count}")

    if dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Run without --dry-run to remove the old metadata folders.")
    else:
        print(f"\n✓ Removed {removed_count} old .metadata folders")
        print("Migration cleanup complete!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Remove old .metadata folders after migration")
    parser.add_argument("inbox", help="Path to the inbox directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview what would be removed")

    args = parser.parse_args()

    inbox_path = Path(args.inbox)
    if not inbox_path.exists() or not inbox_path.is_dir():
        print(f"Error: Invalid directory: {inbox_path}")
        sys.exit(1)

    remove_old_metadata(inbox_path, args.dry_run)


if __name__ == "__main__":
    main()
