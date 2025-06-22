#!/usr/bin/env python3
"""Fix the embedder.py file by removing TODO comments and uncommenting the code."""

import re
from pathlib import Path

def fix_embedder():
    """Fix the embedder.py file."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        content = f.read()
    
    # Pattern to match TODO comments with the code on the same line
    pattern = r'(\s*)# TODO: Review unreachable code - (.+)$'
    
    # Replace pattern - keep the indentation, remove the comment prefix
    def replace_func(match):
        indent = match.group(1)
        code = match.group(2)
        return f"{indent}{code}"
    
    # Apply the fix
    fixed_content = re.sub(pattern, replace_func, content, flags=re.MULTILINE)
    
    # Write the fixed content back
    with file_path.open('w') as f:
        f.write(fixed_content)
    
    print(f"Fixed {file_path}")
    
    # Count how many lines were fixed
    original_lines = content.count('\n')
    fixed_lines = fixed_content.count('\n')
    todo_lines = content.count('# TODO: Review unreachable code')
    
    print(f"Original lines: {original_lines}")
    print(f"Fixed lines: {fixed_lines}")
    print(f"TODO comments removed: {todo_lines}")

if __name__ == "__main__":
    fix_embedder()