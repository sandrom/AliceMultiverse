#!/usr/bin/env python3
"""Fix all try-except syntax errors in the codebase."""

import ast
import re
from pathlib import Path


def find_try_blocks_to_fix(content: str) -> list[tuple[int, int]]:
    """Find try blocks that need fixing."""
    lines = content.split('\n')
    blocks_to_fix = []
    
    for i, line in enumerate(lines):
        # Look for TODO: Review unreachable code - try:
        if '# TODO: Review unreachable code - try:' in line:
            # Find the matching except block
            indent_level = len(line) - len(line.lstrip())
            
            # Look for the except block
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    # Check if it's an except at the same level
                    if (lines[j].lstrip().startswith('except') and 
                        len(lines[j]) - len(lines[j].lstrip()) == indent_level):
                        blocks_to_fix.append((i, j))
                        break
                    # If we hit something else at the same or lower indent, the except might be missing
                    elif len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                        break
    
    return blocks_to_fix


def fix_file(file_path: Path) -> bool:
    """Fix try-except blocks in a file."""
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        
        # First, find all commented try blocks
        blocks_to_fix = find_try_blocks_to_fix(content)
        
        if not blocks_to_fix:
            # Check for uncommented try blocks with commented except
            for i, line in enumerate(lines):
                if line.strip() == 'try:':
                    # Look ahead for a commented except
                    for j in range(i + 1, min(i + 50, len(lines))):
                        if '# TODO: Review unreachable code - except' in lines[j]:
                            # Comment out the try block
                            indent = len(line) - len(line.lstrip())
                            lines[i] = ' ' * indent + '# TODO: Review unreachable code - try:'
                            print(f"Fixed try block at line {i+1} in {file_path}")
                            break
        
        # Write back
        new_content = '\n'.join(lines)
        if new_content != content:
            file_path.write_text(new_content)
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return False


def main():
    """Fix all Python files with try-except issues."""
    # Get all Python files with syntax errors
    files_to_check = [
        "alicemultiverse/interface/natural/base.py",
        "alicemultiverse/interface/timeline_preview_mcp.py", 
        "alicemultiverse/interface/video_creation_mcp.py",
        "alicemultiverse/interface/image_presentation.py",
        "alicemultiverse/interface/structured/base.py",
        "alicemultiverse/interface/broll_suggestions_mcp.py",
        "alicemultiverse/interface/image_presentation_mcp.py",
        "alicemultiverse/core/config_dataclass.py",
        "alicemultiverse/core/metrics.py",
        "alicemultiverse/core/first_run.py",
        "alicemultiverse/core/graceful_degradation.py",
        "alicemultiverse/core/logging_middleware.py",
        "alicemultiverse/core/ai_errors.py",
        "alicemultiverse/core/utils.py",
        "alicemultiverse/core/keys/cli.py",
        "alicemultiverse/core/file_operations.py",
        "alicemultiverse/selections/service.py",
        "alicemultiverse/providers/provider.py",
        "alicemultiverse/organizer/components/process_file.py",
        "alicemultiverse/organizer/organizer_runner.py",
        "alicemultiverse/organizer/resilient_organizer.py"
    ]
    
    fixed_count = 0
    for file_str in files_to_check:
        file_path = Path(file_str)
        if file_path.exists():
            if fix_file(file_path):
                fixed_count += 1
                print(f"Fixed {file_path}")
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()