#!/usr/bin/env python3
"""Clean up unnecessary files from the AliceMultiverse project.

This script removes:
1. Python cache files (__pycache__ directories and .pyc files)
2. Empty directories (excluding .git)
3. Editor temporary files
4. Old documentation that has been integrated
"""

import shutil
import sys
from pathlib import Path

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(message: str):
    """Print a colored header."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{message}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(message: str):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠ {message}{RESET}")


def print_error(message: str):
    """Print an error message."""
    print(f"{RED}✗ {message}{RESET}")


def find_pycache_dirs(root_path: Path) -> list[Path]:
    """Find all __pycache__ directories."""
    return list(root_path.rglob("__pycache__"))


def find_pyc_files(root_path: Path) -> list[Path]:
    """Find all .pyc and .pyo files."""
    pyc_files = list(root_path.rglob("*.pyc"))
    pyo_files = list(root_path.rglob("*.pyo"))
    return pyc_files + pyo_files


def find_editor_temp_files(root_path: Path) -> list[Path]:
    """Find editor temporary files."""
    patterns = ["*~", "*.swp", "*.swo", ".DS_Store"]
    temp_files = []
    for pattern in patterns:
        temp_files.extend(root_path.rglob(pattern))
    return temp_files


def find_empty_dirs(root_path: Path) -> list[Path]:
    """Find empty directories (excluding .git and .venv)."""
    empty_dirs = []
    for path in root_path.rglob("*"):
        if path.is_dir() and not any(path.iterdir()):
            # Skip .git and .venv related directories
            if ".git" not in str(path) and ".venv" not in str(path):
                empty_dirs.append(path)
    return sorted(empty_dirs, reverse=True)  # Sort reverse to delete nested first


def get_obsolete_docs() -> list[tuple[Path, str]]:
    """Get list of obsolete documentation files with reasons."""
    root = Path(__file__).parent.parent
    obsolete_docs = [
        (root / "CHANGELOG_v2.1.0.md", "Content should be in main CHANGELOG.md"),
        (root / "FINAL_QUALITY_REPORT.md", "Temporary quality report"),
        (root / "QUALITY_IMPROVEMENTS_SUMMARY.md", "Temporary quality report"),
        (root / "PROJECT_INVENTORY.md", "Temporary inventory report"),
        (root / "FULL_CLEANUP_REPORT.md", "Temporary cleanup report"),
        (root / "README_UPDATES.md", "Temporary notes for README updates"),
        (root / "DUCKDB_CONSOLIDATION_REPORT.md", "Temporary consolidation report"),
    ]
    return [(path, reason) for path, reason in obsolete_docs if path.exists()]


def clean_pycache(root_path: Path, dry_run: bool = True) -> int:
    """Clean Python cache files."""
    print_header("Cleaning Python Cache Files")

    # Find all cache directories and files
    pycache_dirs = find_pycache_dirs(root_path)
    pyc_files = find_pyc_files(root_path)

    total_count = len(pycache_dirs) + len(pyc_files)

    if dry_run:
        print(f"Found {len(pycache_dirs)} __pycache__ directories")
        print(f"Found {len(pyc_files)} .pyc/.pyo files")
        print(f"\nTotal: {total_count} items to clean")
    else:
        # Remove __pycache__ directories
        for cache_dir in pycache_dirs:
            try:
                shutil.rmtree(cache_dir)
                print_success(f"Removed {cache_dir}")
            except Exception as e:
                print_error(f"Failed to remove {cache_dir}: {e}")

        # Remove .pyc files (in case any are outside __pycache__)
        for pyc_file in pyc_files:
            if pyc_file.exists():  # Might have been removed with __pycache__
                try:
                    pyc_file.unlink()
                    print_success(f"Removed {pyc_file}")
                except Exception as e:
                    print_error(f"Failed to remove {pyc_file}: {e}")

    return total_count


def clean_editor_temp_files(root_path: Path, dry_run: bool = True) -> int:
    """Clean editor temporary files."""
    print_header("Cleaning Editor Temporary Files")

    temp_files = find_editor_temp_files(root_path)

    if dry_run:
        print(f"Found {len(temp_files)} temporary files:")
        for file in temp_files:
            print(f"  - {file}")
    else:
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                print_success(f"Removed {temp_file}")
            except Exception as e:
                print_error(f"Failed to remove {temp_file}: {e}")

    return len(temp_files)


def clean_empty_dirs(root_path: Path, dry_run: bool = True) -> int:
    """Clean empty directories."""
    print_header("Cleaning Empty Directories")

    empty_dirs = find_empty_dirs(root_path)

    # Filter out important empty directories
    important_dirs = ["projects", "test_data", "docs/api", "output", "inbox", "organized"]
    filtered_dirs = []

    for dir_path in empty_dirs:
        # Check if it's an important directory
        is_important = any(important in str(dir_path) for important in important_dirs)
        if not is_important:
            filtered_dirs.append(dir_path)

    if dry_run:
        print(f"Found {len(filtered_dirs)} empty directories to remove:")
        for dir_path in filtered_dirs:
            print(f"  - {dir_path}")

        if len(empty_dirs) > len(filtered_dirs):
            print(f"\nPreserving {len(empty_dirs) - len(filtered_dirs)} important empty directories")
    else:
        for dir_path in filtered_dirs:
            try:
                dir_path.rmdir()
                print_success(f"Removed {dir_path}")
            except Exception as e:
                print_error(f"Failed to remove {dir_path}: {e}")

    return len(filtered_dirs)


def clean_obsolete_docs(dry_run: bool = True) -> int:
    """Clean obsolete documentation files."""
    print_header("Cleaning Obsolete Documentation")

    obsolete_docs = get_obsolete_docs()

    if dry_run:
        print(f"Found {len(obsolete_docs)} obsolete documentation files:")
        for doc_path, reason in obsolete_docs:
            print(f"  - {doc_path.name}: {reason}")
    else:
        for doc_path, reason in obsolete_docs:
            try:
                doc_path.unlink()
                print_success(f"Removed {doc_path.name} ({reason})")
            except Exception as e:
                print_error(f"Failed to remove {doc_path}: {e}")

    return len(obsolete_docs)


def main():
    """Main cleanup function."""
    root_path = Path(__file__).parent.parent

    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv

    if dry_run:
        print_warning("DRY RUN MODE - No files will be deleted")
    elif not force:
        print_warning("Preview mode - use --force to actually delete files")
        dry_run = True

    # Count total items to clean
    total_items = 0

    # Clean Python cache
    total_items += clean_pycache(root_path, dry_run)

    # Clean editor temp files
    total_items += clean_editor_temp_files(root_path, dry_run)

    # Clean empty directories
    total_items += clean_empty_dirs(root_path, dry_run)

    # Clean obsolete documentation
    total_items += clean_obsolete_docs(dry_run)

    # Summary
    print_header("Summary")
    if dry_run:
        print(f"Total items that would be cleaned: {total_items}")
        if not force:
            print("\nTo actually delete these files, run:")
            print(f"  {YELLOW}python {sys.argv[0]} --force{RESET}")
    else:
        print_success(f"Successfully cleaned {total_items} items")

    # Update .gitignore if needed
    gitignore_path = root_path / ".gitignore"
    patterns_to_add = [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "*.swp",
        "*.swo",
        "*~",
        ".DS_Store",
    ]

    if gitignore_path.exists():
        with open(gitignore_path) as f:
            gitignore_content = f.read()

        missing_patterns = []
        for pattern in patterns_to_add:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)

        if missing_patterns:
            print_header("Update .gitignore")
            print("The following patterns should be added to .gitignore:")
            for pattern in missing_patterns:
                print(f"  {pattern}")
            print("\nAdd them to prevent these files from being committed.")


if __name__ == "__main__":
    main()
