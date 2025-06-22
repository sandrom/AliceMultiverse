#!/usr/bin/env python3
"""Final comprehensive fix for embedder.py indentation issues."""

import re
from pathlib import Path

def fix_embedder_indentation():
    """Fix all indentation issues in embedder.py."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.rstrip('\n')
        
        # Check for lines that should be indented but aren't
        if (stripped and 
            not stripped[0].isspace() and 
            i > 0 and
            lines[i-1].strip().endswith(':')):
            # Previous line ends with colon, this line should be indented
            # Get the indentation of the previous line
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            # Add 4 more spaces
            fixed_lines.append(' ' * (prev_indent + 4) + stripped + '\n')
        else:
            fixed_lines.append(line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    fix_embedder_indentation()