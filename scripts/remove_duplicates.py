#!/usr/bin/env python3
"""Remove duplicate files from the organized folder."""

import hashlib
from pathlib import Path
from collections import defaultdict
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def find_duplicates(organized_dir: Path) -> dict[str, list[Path]]:
    """Find all duplicate files in the organized directory."""
    hash_to_files = defaultdict(list)
    total_files = 0
    
    logger.info(f"Scanning {organized_dir} for duplicates...")
    
    # Find all image and video files
    extensions = {
        '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.raw',
        '.cr2', '.nef', '.arw', '.dng', '.heic', '.gif',
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.wmv', '.flv',
        '.mpg', '.mpeg', '.3gp'
    }
    
    for ext in extensions:
        for file_path in organized_dir.rglob(f'*{ext}'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                total_files += 1
                file_hash = calculate_file_hash(file_path)
                hash_to_files[file_hash].append(file_path)
    
    # Filter to only duplicates
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
    
    logger.info(f"Found {total_files} total files")
    logger.info(f"Found {len(duplicates)} sets of duplicates")
    
    return duplicates


def remove_duplicates(duplicates: dict[str, list[Path]], dry_run: bool = True) -> None:
    """Remove duplicate files, keeping the first occurrence."""
    total_removed = 0
    total_size_saved = 0
    
    for file_hash, file_list in duplicates.items():
        # Sort by path to ensure consistent ordering
        file_list.sort()
        
        # Keep the first file, remove the rest
        keep_file = file_list[0]
        logger.info(f"\nKeeping: {keep_file}")
        
        for duplicate in file_list[1:]:
            size = duplicate.stat().st_size
            logger.info(f"  Removing duplicate: {duplicate} ({size:,} bytes)")
            
            if not dry_run:
                duplicate.unlink()
            
            total_removed += 1
            total_size_saved += size
    
    logger.info(f"\n{'Would remove' if dry_run else 'Removed'} {total_removed} duplicate files")
    logger.info(f"Space {'would be' if dry_run else ''} saved: {total_size_saved:,} bytes ({total_size_saved / 1024 / 1024:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description='Remove duplicate files from organized folder')
    parser.add_argument('organized_dir', type=Path, help='Path to organized directory')
    parser.add_argument('--remove', action='store_true', help='Actually remove duplicates (default is dry run)')
    
    args = parser.parse_args()
    
    if not args.organized_dir.exists():
        logger.error(f"Directory not found: {args.organized_dir}")
        return 1
    
    duplicates = find_duplicates(args.organized_dir)
    
    if duplicates:
        remove_duplicates(duplicates, dry_run=not args.remove)
    else:
        logger.info("No duplicates found!")
    
    return 0


if __name__ == '__main__':
    exit(main())