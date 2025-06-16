#!/usr/bin/env python3
"""Regular maintenance and cleanup script for AliceMultiverse."""

import argparse
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path


def cleanup_pycache(root_dir: Path) -> int:
    """Remove all __pycache__ directories and .pyc files."""
    count = 0
    
    # Remove __pycache__ directories
    for pycache_dir in root_dir.rglob("__pycache__"):
        if pycache_dir.is_dir():
            shutil.rmtree(pycache_dir)
            count += 1
    
    # Remove .pyc files
    for pyc_file in root_dir.rglob("*.pyc"):
        if pyc_file.is_file():
            pyc_file.unlink()
            count += 1
    
    return count


def cleanup_temp_files(root_dir: Path) -> int:
    """Remove temporary files."""
    count = 0
    patterns = ["*.tmp", "*.temp", "*.bak", "*.log", ".DS_Store"]
    
    for pattern in patterns:
        for temp_file in root_dir.rglob(pattern):
            if temp_file.is_file():
                # Skip important log files
                if temp_file.name in ["development.log", "production.log"]:
                    continue
                temp_file.unlink()
                count += 1
    
    return count


def cleanup_old_cache(cache_dir: Path, days: int = 30) -> int:
    """Remove cache files older than specified days."""
    if not cache_dir.exists():
        return 0
    
    count = 0
    cutoff = datetime.now() - timedelta(days=days)
    
    for cache_file in cache_dir.rglob("*"):
        if cache_file.is_file():
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if mtime < cutoff:
                cache_file.unlink()
                count += 1
    
    return count


def find_todo_comments(root_dir: Path) -> list[tuple[Path, int, str]]:
    """Find all TODO/FIXME/DEPRECATED comments in Python files."""
    todos = []
    patterns = ["TODO", "FIXME", "DEPRECATED", "HACK", "XXX"]
    
    for py_file in root_dir.rglob("*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    for pattern in patterns:
                        if pattern in line:
                            todos.append((py_file, line_num, line.strip()))
                            break
        except Exception:
            continue
    
    return todos


def find_large_files(root_dir: Path, min_lines: int = 1000) -> list[tuple[Path, int]]:
    """Find Python files larger than specified line count."""
    large_files = []
    
    for py_file in root_dir.rglob("*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f)
                if line_count >= min_lines:
                    large_files.append((py_file, line_count))
        except Exception:
            continue
    
    return sorted(large_files, key=lambda x: x[1], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="AliceMultiverse maintenance and cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    parser.add_argument("--cache-days", type=int, default=30, help="Remove cache files older than N days")
    parser.add_argument("--find-todos", action="store_true", help="Find TODO/FIXME comments")
    parser.add_argument("--find-large-files", action="store_true", help="Find large Python files")
    parser.add_argument("--min-lines", type=int, default=1000, help="Minimum lines for large file detection")
    
    args = parser.parse_args()
    
    # Get project root
    root_dir = Path(__file__).parent.parent
    
    print(f"AliceMultiverse Maintenance - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {root_dir}")
    print()
    
    if args.find_todos:
        print("Finding TODO/FIXME comments...")
        todos = find_todo_comments(root_dir)
        print(f"\nFound {len(todos)} TODO/FIXME comments:")
        for file_path, line_num, line in todos[:20]:  # Show first 20
            rel_path = file_path.relative_to(root_dir)
            print(f"  {rel_path}:{line_num} - {line[:80]}")
        if len(todos) > 20:
            print(f"  ... and {len(todos) - 20} more")
        print()
    
    if args.find_large_files:
        print(f"Finding Python files with {args.min_lines}+ lines...")
        large_files = find_large_files(root_dir, args.min_lines)
        print(f"\nFound {len(large_files)} large files:")
        for file_path, line_count in large_files[:10]:  # Show top 10
            rel_path = file_path.relative_to(root_dir)
            print(f"  {rel_path}: {line_count} lines")
        print()
    
    if not args.find_todos and not args.find_large_files:
        # Regular cleanup
        print("Starting cleanup...")
        
        if not args.dry_run:
            # Clean Python cache
            count = cleanup_pycache(root_dir)
            print(f"  Removed {count} __pycache__ directories and .pyc files")
            
            # Clean temp files
            count = cleanup_temp_files(root_dir)
            print(f"  Removed {count} temporary files")
            
            # Clean old cache
            cache_dir = Path.home() / ".alice" / "cache"
            count = cleanup_old_cache(cache_dir, args.cache_days)
            print(f"  Removed {count} cache files older than {args.cache_days} days")
        else:
            print("  DRY RUN - no files were actually removed")
        
        print("\nCleanup complete!")


if __name__ == "__main__":
    main()