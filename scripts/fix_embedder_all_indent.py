#!/usr/bin/env python3
"""Fix all remaining indentation issues in embedder.py."""

import re
from pathlib import Path

def fix_indentation():
    """Fix all indentation issues in embedder.py."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        content = f.read()
    
    # Fix all lines that should be indented inside methods
    lines = content.split('\n')
    fixed_lines = []
    
    in_method = False
    method_indent = ""
    in_docstring = False
    
    for i, line in enumerate(lines):
        # Check if we're starting a method definition
        if re.match(r'^(\s*)def\s+\w+\(', line):
            in_method = True
            method_indent = re.match(r'^(\s*)', line).group(1)
            in_docstring = False
            fixed_lines.append(line)
            continue
            
        # Check if we're at class level or module level
        if line.strip() and not line[0].isspace() and not line.startswith('#'):
            in_method = False
            fixed_lines.append(line)
            continue
            
        # Handle empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # If we're in a method
        if in_method:
            stripped = line.strip()
            
            # Handle docstrings
            if stripped.startswith('"""'):
                if not in_docstring:
                    in_docstring = True
                    fixed_lines.append(f"{method_indent}    {stripped}")
                elif stripped == '"""':
                    in_docstring = False
                    fixed_lines.append(f"{method_indent}    {stripped}")
                else:
                    in_docstring = False
                    fixed_lines.append(f"{method_indent}    {stripped}")
            elif in_docstring:
                fixed_lines.append(f"{method_indent}    {stripped}")
            # Fix lines that are missing indentation
            elif line and not line[0].isspace():
                # These lines should be indented
                if stripped.startswith(('try:', 'except', 'if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'return', '#')):
                    fixed_lines.append(f"{method_indent}    {stripped}")
                elif any(stripped.startswith(x + ' ') or stripped.startswith(x + '.') or stripped == x for x in 
                        ['metadata', 'alice_data', 'img', 'pnginfo', 'exif_dict', 'info', 'save_kwargs', 
                         'analysis', 'desc', 'prompt', 'comment', 'our_key', 'logger', 'exif_bytes', 
                         'alice_key', 'tmp_path', 'suffix', 'image_path']):
                    fixed_lines.append(f"{method_indent}    {stripped}")
                else:
                    # Nested content needs more indentation
                    fixed_lines.append(f"{method_indent}        {stripped}")
            else:
                # Already has indentation, keep it
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    fix_indentation()