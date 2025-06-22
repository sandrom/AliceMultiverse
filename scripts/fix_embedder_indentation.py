#!/usr/bin/env python3
"""Fix all indentation issues in embedder.py."""

import re
from pathlib import Path

def fix_all_indentation():
    """Fix all indentation issues in embedder.py."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_method = False
    method_indent = ""
    
    for i, line in enumerate(lines):
        # Detect method definitions
        if re.match(r'^(\s*)def\s+\w+\(', line):
            in_method = True
            method_indent = re.match(r'^(\s*)', line).group(1)
            fixed_lines.append(line)
            continue
        
        # Detect class definitions or module-level code
        if line.strip() and not line[0].isspace() and not line.startswith('#'):
            in_method = False
            fixed_lines.append(line)
            continue
        
        # If we're in a method and the line has content but no indentation
        if in_method and line.strip() and not line[0].isspace():
            # This line needs indentation
            content = line.strip()
            
            # Determine the proper indentation level
            if content.startswith(('"""', "'''")):
                # Docstring
                fixed_lines.append(f"{method_indent}    {content}\n")
            elif content.startswith(('try:', 'except', 'if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'return', 'pass', '#')):
                # First-level statement in method
                fixed_lines.append(f"{method_indent}    {content}\n")
            elif any(content.startswith(x) for x in ['metadata', 'alice_data', 'img', 'pnginfo', 'exif_dict', 'info', 'save_kwargs', 'analysis', 'desc', 'prompt', 'comment', 'our_key', 'logger', 'exif_bytes', 'alice_key', 'tmp_path']):
                # Variable assignment or method call
                fixed_lines.append(f"{method_indent}    {content}\n")
            else:
                # Nested content - add extra indentation
                fixed_lines.append(f"{method_indent}        {content}\n")
        else:
            # Keep the line as is
            fixed_lines.append(line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    fix_all_indentation()