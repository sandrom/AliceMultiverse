#!/usr/bin/env python3
"""
One-time migration script to consolidate scattered .metadata folders
into a single centralized .metadata folder at the inbox root.
"""

import hashlib
import json
import sys
from pathlib import Path


def get_content_hash(file_path: Path) -> str:
    """Compute full SHA256 hash of file content"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def find_metadata_folders(root_dir: Path) -> list[Path]:
    """Find all .metadata folders under the root directory"""
    metadata_folders = []
    for item in root_dir.rglob(".metadata"):
        if item.is_dir() and item != root_dir / ".metadata":
            metadata_folders.append(item)
    return metadata_folders


def migrate_metadata(inbox_dir: Path, dry_run: bool = False):
    """Migrate scattered .metadata folders to centralized location"""
    print(f"Migrating metadata in: {inbox_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Create central metadata folder
    central_metadata = inbox_dir / ".metadata"
    if not dry_run:
        central_metadata.mkdir(exist_ok=True)

    # Find all scattered metadata folders
    old_metadata_folders = find_metadata_folders(inbox_dir)

    if not old_metadata_folders:
        print("No scattered .metadata folders found. Nothing to migrate.")
        return

    print(f"Found {len(old_metadata_folders)} scattered .metadata folders")

    # Statistics
    stats = {"files_migrated": 0, "files_skipped": 0, "folders_removed": 0, "errors": 0}

    # Process each metadata folder
    for old_folder in old_metadata_folders:
        print(f"\nProcessing: {old_folder.relative_to(inbox_dir)}")

        # Find all JSON files in the metadata folder
        json_files = list(old_folder.glob("*.json"))

        for json_file in json_files:
            try:
                # Read the metadata
                with open(json_file) as f:
                    metadata = json.load(f)

                # Find the corresponding media file
                media_name = json_file.stem  # Remove .json extension
                media_file = old_folder.parent / media_name

                if not media_file.exists():
                    print(f"  ⚠️  Media file not found: {media_name}")
                    stats["files_skipped"] += 1
                    continue

                # Get content hash for the media file
                content_hash = get_content_hash(media_file)

                # Update metadata with new structure
                metadata["content_hash"] = content_hash
                metadata["original_path"] = str(media_file.relative_to(inbox_dir))
                metadata["file_name"] = media_file.name

                # New metadata file path
                new_json_path = central_metadata / f"{content_hash}.json"

                if not dry_run:
                    # Write to new location
                    with open(new_json_path, "w") as f:
                        json.dump(metadata, f, indent=2)

                print(f"  ✓ Migrated: {media_name} → {content_hash[:8]}...json")
                stats["files_migrated"] += 1

            except Exception as e:
                print(f"  ✗ Error processing {json_file.name}: {e}")
                stats["errors"] += 1

        # Remove old metadata folder if empty
        if not dry_run and not any(old_folder.iterdir()):
            old_folder.rmdir()
            stats["folders_removed"] += 1
            print(f"  🗑️  Removed empty folder: {old_folder.relative_to(inbox_dir)}")

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Files migrated: {stats['files_migrated']}")
    print(f"Files skipped: {stats['files_skipped']}")
    print(f"Folders removed: {stats['folders_removed']}")
    print(f"Errors: {stats['errors']}")

    if dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Run without --dry-run to perform the actual migration.")
    else:
        print(f"\nMigration complete! Centralized metadata is now in: {central_metadata}")

        # Clean up remaining empty folders
        remaining = find_metadata_folders(inbox_dir)
        if remaining:
            print(f"\n⚠️  {len(remaining)} .metadata folders still contain files:")
            for folder in remaining:
                print(f"  - {folder.relative_to(inbox_dir)}")
            print("\nThese may contain metadata for files that no longer exist.")
            print("You can manually review and delete them if needed.")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate scattered .metadata folders to centralized location"
    )
    parser.add_argument("inbox", help="Path to the inbox directory")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without making them"
    )

    args = parser.parse_args()

    inbox_path = Path(args.inbox)
    if not inbox_path.exists():
        print(f"Error: Inbox directory not found: {inbox_path}")
        sys.exit(1)

    if not inbox_path.is_dir():
        print(f"Error: Not a directory: {inbox_path}")
        sys.exit(1)

    migrate_metadata(inbox_path, args.dry_run)


if __name__ == "__main__":
    main()
