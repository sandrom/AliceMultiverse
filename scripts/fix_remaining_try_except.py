#!/usr/bin/env python3
"""Fix all remaining try-except syntax errors in the codebase."""

import subprocess
import re
from pathlib import Path

def fix_try_except_in_file(file_path: Path) -> bool:
    """Fix try-except blocks in a file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed = False
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a commented UNREACHABLE except line
        if '# TODO: Review unreachable code - ' in line and 'except' in line:
            # Remove the UNREACHABLE comment
            lines[i] = line.replace('# TODO: Review unreachable code - ', '')
            fixed = True
            
            # Process following lines that are part of the except block
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('# TODO: Review unreachable code - '):
                lines[j] = lines[j].replace('# TODO: Review unreachable code - ', '')
                j += 1
        
        i += 1
    
    if fixed:
        with open(file_path, 'w') as f:
            f.writelines(lines)
    
    return fixed

def main():
    """Fix all files with try-except syntax errors."""
    project_root = Path(__file__).parent.parent
    
    while True:
        # Run mypy to find syntax errors
        result = subprocess.run(
            ["python", "-m", "mypy", "alicemultiverse"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Look for syntax errors
        error_found = False
        for line in result.stderr.split('\n'):
            if 'error:' in line and ('expected' in line or 'syntax' in line):
                match = re.match(r'(alicemultiverse/[^:]+):\d+:', line)
                if match:
                    file_path = project_root / match.group(1)
                    print(f"Fixing {file_path.name}...")
                    if fix_try_except_in_file(file_path):
                        error_found = True
                        break
        
        if not error_found:
            print("No more syntax errors found!")
            break
    
    # Final check
    result = subprocess.run(
        ["python", "-m", "mypy", "alicemultiverse", "--count"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    print(f"\nFinal mypy error count: {result.stdout.strip()}")

if __name__ == "__main__":
    main()