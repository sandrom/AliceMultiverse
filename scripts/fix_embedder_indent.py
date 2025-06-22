#!/usr/bin/env python3
"""Fix indentation issues in the embedder.py file."""

import re
from pathlib import Path

def fix_indentation():
    """Fix indentation issues in embedder.py."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_method = False
    base_indent = ""
    
    for i, line in enumerate(lines):
        # Check if we're starting a method definition
        if line.strip().startswith('def '):
            in_method = True
            # Extract the base indentation
            base_indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(line)
            continue
        
        # If we're in a method and the line has no indentation but content
        if in_method and line.strip() and not line[0].isspace():
            # This line should be indented
            # Check what it contains to determine proper indentation
            stripped = line.strip()
            
            if stripped.startswith('"""'):
                # Docstring - should be at method indent + 4
                fixed_lines.append(base_indent + "    " + stripped + "\n")
            elif stripped.startswith(('try:', 'except', 'if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'return', 'metadata', 'alice_data', 'img', 'pnginfo', 'exif_dict', 'info', 'save_kwargs', 'xmp_template', 'metadata_json', 'description', 'xmp_data', 'analysis', 'desc', 'prompt', 'comment', 'our_key', 'logger')):
                # Statement - should be at method indent + 4
                fixed_lines.append(base_indent + "    " + stripped + "\n")
            elif stripped.startswith('#'):
                # Comment - should be at method indent + 4
                fixed_lines.append(base_indent + "    " + stripped + "\n")
            elif stripped == '}':
                # Dictionary closing - check context
                fixed_lines.append(base_indent + "        " + stripped + "\n")
            else:
                # Other content - likely continuation, indent more
                fixed_lines.append(base_indent + "        " + stripped + "\n")
        elif in_method and line.strip() == "":
            # Empty line
            fixed_lines.append(line)
        elif not in_method or (in_method and line[0].isspace()):
            # Already properly indented or not in a method
            fixed_lines.append(line)
        else:
            # Edge case
            fixed_lines.append(line)
            
        # Check if we're ending a method (next non-empty line starts with def or class)
        if in_method and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and (next_line.startswith('def ') or next_line.startswith('class ')):
                in_method = False
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    fix_indentation()