#!/usr/bin/env python3
"""Rebuild the DuckDB search index from file metadata."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.storage.index_builder import SearchIndexBuilder
from alicemultiverse.core.config import load_config


def main():
    parser = argparse.ArgumentParser(description="Rebuild DuckDB search index from files")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths to scan for media files (defaults to configured paths)",
    )
    parser.add_argument(
        "--db-path",
        help="Path to DuckDB database file (defaults to config)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify index after rebuilding",
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Determine paths to scan
    if args.paths:
        paths = args.paths
    else:
        # Use default paths from config
        paths = []
        if hasattr(config, 'paths'):
            if hasattr(config.paths, 'inbox'):
                paths.append(config.paths.inbox)
            if hasattr(config.paths, 'organized'):
                paths.append(config.paths.organized)
        
        if not paths:
            print("No paths specified and no default paths in config")
            return 1
    
    # Determine database path
    db_path = args.db_path
    if not db_path and hasattr(config, 'storage') and hasattr(config.storage, 'search_db'):
        db_path = config.storage.search_db
    
    print(f"Rebuilding search index...")
    print(f"Database: {db_path or 'in-memory'}")
    print(f"Paths to scan: {', '.join(paths)}")
    print()
    
    # Create index builder
    builder = SearchIndexBuilder(db_path)
    
    # Rebuild index
    indexed_count = builder.rebuild_from_paths(paths, show_progress=not args.no_progress)
    
    print(f"\nIndexed {indexed_count} files")
    
    # Verify if requested
    if args.verify:
        print("\nVerifying index...")
        results = builder.verify_index()
        print(f"Total indexed: {results['total_indexed']}")
        print(f"Valid files: {results['valid_files']}")
        print(f"Missing files: {results['missing_files']}")
        
        if results['missing_files'] > 0:
            print("\nFirst 10 missing files:")
            for path in results['missing_file_paths'][:10]:
                print(f"  - {path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())