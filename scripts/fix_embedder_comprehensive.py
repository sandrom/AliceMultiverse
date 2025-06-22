#!/usr/bin/env python3
"""Comprehensive fix for embedder.py indentation issues."""

import re
from pathlib import Path

def fix_embedder_indentation():
    """Fix all indentation issues in embedder.py."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    indent_stack = []  # Track current indentation levels
    
    for i, line in enumerate(lines):
        original_line = line
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(original_line)
            continue
            
        # Skip comment-only lines
        if stripped.startswith('#'):
            fixed_lines.append(original_line)
            continue
        
        # Calculate expected indentation based on previous line
        if i > 0:
            prev_line = lines[i-1].strip()
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            
            # If previous line ends with colon, increase indent
            if prev_line.endswith(':'):
                expected_indent = prev_indent + 4
            # elif/else should match the if indent
            elif stripped.startswith(('elif ', 'else:')):
                # Find the matching if/elif indent
                for j in range(i-1, -1, -1):
                    check_line = lines[j].strip()
                    if check_line.startswith(('if ', 'elif ')):
                        expected_indent = len(lines[j]) - len(lines[j].lstrip())
                        break
                else:
                    expected_indent = prev_indent
            # except should match try indent
            elif stripped.startswith('except '):
                # Find the matching try
                for j in range(i-1, -1, -1):
                    check_line = lines[j].strip()
                    if check_line.startswith('try:'):
                        expected_indent = len(lines[j]) - len(lines[j].lstrip())
                        break
                else:
                    expected_indent = prev_indent
            # finally should match try indent
            elif stripped.startswith('finally:'):
                # Find the matching try
                for j in range(i-1, -1, -1):
                    check_line = lines[j].strip()
                    if check_line.startswith('try:'):
                        expected_indent = len(lines[j]) - len(lines[j].lstrip())
                        break
                else:
                    expected_indent = prev_indent
            else:
                # For regular lines, check if we need to dedent
                current_indent = len(line) - len(line.lstrip())
                if current_indent == 0 and not line.startswith(('class ', 'def ', 'import ', 'from ')):
                    # This line should probably be indented
                    # Use the previous non-empty line's indent
                    expected_indent = prev_indent
                else:
                    expected_indent = current_indent
        else:
            expected_indent = 0
        
        # Apply the expected indentation
        current_indent = len(line) - len(line.lstrip())
        if current_indent == 0 and expected_indent > 0:
            # Line has no indentation but should have some
            fixed_line = ' ' * expected_indent + stripped + '\n'
            fixed_lines.append(fixed_line)
            print(f"Fixed line {i+1}: {stripped[:50]}...")
        else:
            # Keep the line as is
            fixed_lines.append(original_line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print(f"\nFixed indentation in {file_path}")
    
    # Try to compile to check for remaining issues
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("File compiles successfully!")
    except py_compile.PyCompileError as e:
        print(f"Compilation error: {e}")

if __name__ == "__main__":
    fix_embedder_indentation()