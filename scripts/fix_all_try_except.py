#!/usr/bin/env python3
"""Fix all try-except syntax errors in the codebase."""

import re
import subprocess
from pathlib import Path

def fix_file(file_path: Path) -> bool:
    """Fix try-except blocks in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find commented UNREACHABLE except blocks
    pattern = r'(\s+)# TODO: Review unreachable code - (except .+?:)\n(\s+)# UNREACHABLE: (.+)'
    
    def replace_except(match):
        indent = match.group(1)
        except_line = match.group(2)
        body_indent = match.group(3)
        body = match.group(4)
        
        # Reconstruct the except block with proper indentation
        return f"{indent}{except_line}\n{body_indent}{body}"
    
    # Replace all occurrences
    new_content = re.sub(pattern, replace_except, content)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

def find_and_fix_all():
    """Find and fix all files with syntax errors."""
    project_root = Path(__file__).parent.parent
    fixed_files = []
    
    while True:
        # Run mypy to find syntax errors
        result = subprocess.run(
            ["python", "-m", "mypy", "alicemultiverse"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Find syntax errors
        error_file = None
        for line in result.stderr.split('\n'):
            if 'error:' in line and ('expected' in line or 'syntax' in line):
                parts = line.split(':')
                if len(parts) >= 2:
                    error_file = project_root / parts[0]
                    break
        
        if not error_file:
            break
            
        print(f"Fixing {error_file.relative_to(project_root)}")
        if fix_file(error_file):
            fixed_files.append(error_file)
        else:
            # Manual fix needed
            print(f"Could not automatically fix {error_file}")
            break
    
    return fixed_files

if __name__ == "__main__":
    print("Fixing all try-except syntax errors...")
    fixed = find_and_fix_all()
    print(f"\nFixed {len(fixed)} files:")
    for f in fixed:
        print(f"  - {f.name}")