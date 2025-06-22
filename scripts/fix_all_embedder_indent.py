#!/usr/bin/env python3
"""Comprehensive fix for all indentation issues in embedder.py."""

import re
from pathlib import Path

def fix_all_indentation():
    """Fix all indentation issues in embedder.py comprehensively."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        content = f.read()
    
    # Split into lines
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a method definition
        method_match = re.match(r'^(\s*)def\s+(\w+)\(', line)
        if method_match:
            indent = method_match.group(1)
            method_name = method_match.group(2)
            fixed_lines.append(line)
            i += 1
            
            # Process the method body
            while i < len(lines):
                next_line = lines[i]
                
                # Check if we've reached the next method or end of class
                if next_line.strip() and re.match(r'^(\s*)def\s+\w+\(', next_line):
                    break
                if next_line.strip() and not next_line[0].isspace() and not next_line.startswith('#'):
                    break
                    
                # Fix lines that should be indented but aren't
                if next_line.strip() and not next_line[0].isspace():
                    # This line needs indentation
                    stripped = next_line.strip()
                    # Add proper indentation (method indent + 4 spaces)
                    fixed_lines.append(f"{indent}    {stripped}")
                else:
                    # Keep the line as is
                    fixed_lines.append(next_line)
                
                i += 1
            
            # Don't increment i here as we want to process the next method/line
            continue
        
        # Not a method definition, keep as is
        fixed_lines.append(line)
        i += 1
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"Fixed all indentation in {file_path}")

if __name__ == "__main__":
    fix_all_indentation()