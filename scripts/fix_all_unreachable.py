#!/usr/bin/env python3
"""Fix all UNREACHABLE comments in the codebase."""

import os
import re
from pathlib import Path

def fix_unreachable_in_file(filepath):
    """Remove UNREACHABLE comments from a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Count UNREACHABLE occurrences
    count = len(re.findall(r'^# TODO: Review unreachable code - ', content, re.MULTILINE))
    
    if count == 0:
        return 0
    
    # Remove UNREACHABLE comments
    fixed_content = re.sub(r'^# TODO: Review unreachable code - ', '', content, flags=re.MULTILINE)
    
    with open(filepath, 'w') as f:
        f.write(fixed_content)
    
    return count

def main():
    """Fix all Python files in alicemultiverse directory."""
    root_dir = Path('alicemultiverse')
    total_files = 0
    total_fixes = 0
    
    for py_file in root_dir.rglob('*.py'):
        fixes = fix_unreachable_in_file(py_file)
        if fixes > 0:
            total_files += 1
            total_fixes += fixes
            print(f"Fixed {fixes} UNREACHABLE comments in {py_file}")
    
    print(f"\nTotal: Fixed {total_fixes} UNREACHABLE comments in {total_files} files")

if __name__ == '__main__':
    main()