#!/usr/bin/env python3
"""Final comprehensive fix for all syntax errors."""

import subprocess
import re
from pathlib import Path

def fix_all_syntax_errors():
    """Fix all remaining syntax errors."""
    project_root = Path(__file__).parent.parent
    
    # Keep fixing until no more errors
    for i in range(100):  # Safety limit
        # Run mypy
        result = subprocess.run(
            ["python", "-m", "mypy", "alicemultiverse"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Check for syntax errors
        if "error:" not in result.stderr:
            print(f"All syntax errors fixed after {i} iterations!")
            break
            
        # Find the error
        for line in result.stderr.split('\n'):
            if 'error:' in line and 'syntax' in line:
                # Extract file path
                match = re.match(r'(alicemultiverse/[^:]+):(\d+):', line)
                if match:
                    file_path = project_root / match.group(1)
                    line_num = int(match.group(2))
                    
                    print(f"Fixing {file_path.name} at line {line_num}")
                    
                    # Read file
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    
                    # Common fix patterns
                    fixed = False
                    
                    # Fix commented UNREACHABLE except blocks
                    for j in range(len(lines)):
                        if '# TODO: Review unreachable code - ' in lines[j] and ('except' in lines[j] or 'finally' in lines[j]):
                            lines[j] = lines[j].replace('# TODO: Review unreachable code - ', '')
                            # Fix following lines too
                            k = j + 1
                            while k < len(lines) and lines[k].strip().startswith('# TODO: Review unreachable code - '):
                                lines[k] = lines[k].replace('# TODO: Review unreachable code - ', '')
                                k += 1
                            fixed = True
                            break
                    
                    if fixed:
                        with open(file_path, 'w') as f:
                            f.writelines(lines)
                        break
    else:
        print("Reached iteration limit, some errors may remain")

if __name__ == "__main__":
    fix_all_syntax_errors()