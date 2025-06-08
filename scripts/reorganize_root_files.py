#!/usr/bin/env python3
"""Reorganize root directory markdown files into appropriate documentation folders.

This script moves documentation files from the root directory to better organized
locations within the docs/ folder structure.
"""

import shutil
import sys
from pathlib import Path
from typing import List, Tuple

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


def get_file_moves() -> List[Tuple[str, str, str]]:
    """Get list of files to move with (source, destination, description)."""
    return [
        # Developer documentation
        ("CONFIGURATION_GUIDE.md", "docs/developer/configuration-guide.md", 
         "Configuration guide for developers"),
        ("PROVIDER_REFACTORING_EXAMPLE.md", "docs/developer/provider-refactoring-example.md",
         "Provider refactoring example"),
        ("instructions.md", "docs/developer/development-instructions.md",
         "Development instructions"),
        
        # Philosophy/creative docs
        ("multi-agent-team.md", "docs/philosophy/multi-agent-team.md",
         "Multi-agent team creative document"),
        
        # Archive cleanup/status reports
        ("CLEANUP_COMPLETE.md", "docs/archive/cleanup-complete-jan-2025.md",
         "Cleanup completion report"),
        ("CLEANUP_SUMMARY_2025.md", "docs/archive/cleanup-summary-jan-2025.md",
         "Detailed cleanup summary"),
        ("CLEANUP_SUMMARY.md", "docs/archive/cleanup-summary-jan-2025-brief.md",
         "Brief cleanup summary"),
        ("PROJECT_STATUS_JAN_2025.md", "docs/archive/project-status-jan-2025.md",
         "Project status January 2025"),
        ("PROJECT_STATUS.md", "docs/archive/project-status-jan-2025-brief.md",
         "Brief project status"),
        
        # Templates
        ("PULL_REQUEST_TEMPLATE.md", ".github/PULL_REQUEST_TEMPLATE.md",
         "GitHub pull request template"),
    ]


def get_files_to_consolidate() -> List[Tuple[str, str, str]]:
    """Get list of files to consolidate with (source, target, description)."""
    return [
        ("API_KEYS.md", "docs/getting-started/configuration.md",
         "API keys setup information"),
        ("QUICKSTART.md", "docs/getting-started/quickstart.md",
         "Quick start guide"),
        ("QUICK_REFERENCE.md", "docs/QUICK_REFERENCE_2025.md",
         "Quick reference guide"),
    ]


def create_directories(root_path: Path, dry_run: bool = True):
    """Create necessary directories."""
    directories = [
        root_path / "docs" / "archive",
        root_path / "docs" / "developer", 
        root_path / "docs" / "philosophy",
        root_path / ".github",
    ]
    
    for directory in directories:
        if not directory.exists():
            if dry_run:
                print_warning(f"Would create directory: {directory}")
            else:
                directory.mkdir(parents=True, exist_ok=True)
                print_success(f"Created directory: {directory}")


def move_files(root_path: Path, dry_run: bool = True) -> int:
    """Move files to their new locations."""
    print_header("Moving Files")
    
    moves = get_file_moves()
    moved_count = 0
    
    for source_name, dest_name, description in moves:
        source = root_path / source_name
        dest = root_path / dest_name
        
        if source.exists():
            if dry_run:
                print(f"Would move: {source_name}")
                print(f"       to: {dest_name}")
                print(f"  ({description})\n")
            else:
                try:
                    # Create parent directory if needed
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move the file
                    shutil.move(str(source), str(dest))
                    print_success(f"Moved {source_name} → {dest_name}")
                    print(f"  ({description})")
                    moved_count += 1
                except Exception as e:
                    print_error(f"Failed to move {source_name}: {e}")
        else:
            print_warning(f"File not found: {source_name}")
    
    return moved_count


def consolidate_files(root_path: Path, dry_run: bool = True) -> int:
    """Show files that need manual consolidation."""
    print_header("Files to Consolidate (Manual Action Required)")
    
    consolidations = get_files_to_consolidate()
    consolidate_count = 0
    
    for source_name, target_name, description in consolidations:
        source = root_path / source_name
        target = root_path / target_name
        
        if source.exists():
            print(f"File: {source_name}")
            print(f"  Consolidate into: {target_name}")
            print(f"  Description: {description}")
            
            if target.exists():
                print(f"  {YELLOW}Target exists - manual merge required{RESET}")
            else:
                print(f"  {RED}Target doesn't exist - review needed{RESET}")
            
            print()
            consolidate_count += 1
        else:
            print_warning(f"File not found: {source_name}")
    
    if consolidate_count > 0:
        print(f"\n{YELLOW}Action required: Manually review and consolidate {consolidate_count} files{RESET}")
    
    return consolidate_count


def show_final_state(root_path: Path):
    """Show what the final root directory will look like."""
    print_header("Final Root Directory State")
    
    essential_files = [
        "README.md",
        "CHANGELOG.md", 
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "ROADMAP.md",
    ]
    
    print("Essential files that will remain in root:")
    for file in essential_files:
        if (root_path / file).exists():
            print_success(f"  {file}")
        else:
            print_warning(f"  {file} (not found)")
    
    print(f"\n{GREEN}Root directory will be reduced from 18+ to 6 markdown files{RESET}")


def main():
    """Main function."""
    root_path = Path(__file__).parent.parent
    
    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv
    
    if dry_run:
        print_warning("DRY RUN MODE - No files will be moved")
    elif not force:
        print_warning("Preview mode - use --force to actually move files")
        dry_run = True
    
    # Create necessary directories
    create_directories(root_path, dry_run)
    
    # Move files
    moved_count = move_files(root_path, dry_run)
    
    # Show consolidation candidates
    consolidate_count = consolidate_files(root_path, dry_run)
    
    # Show final state
    show_final_state(root_path)
    
    # Summary
    print_header("Summary")
    if dry_run:
        print(f"Would move {moved_count} files")
        print(f"Would consolidate {consolidate_count} files (manual action)")
        if not force:
            print(f"\nTo actually move these files, run:")
            print(f"  {YELLOW}python {sys.argv[0]} --force{RESET}")
    else:
        print_success(f"Successfully moved {moved_count} files")
        if consolidate_count > 0:
            print_warning(f"Please manually consolidate {consolidate_count} files")


if __name__ == "__main__":
    main()