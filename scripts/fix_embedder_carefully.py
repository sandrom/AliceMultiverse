#!/usr/bin/env python3
"""Carefully remove TODO comments from embedder.py preserving exact indentation."""

import re
from pathlib import Path

def remove_todo_comments():
    """Remove TODO comments while preserving exact indentation."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        content = f.read()
    
    # Pattern to match TODO comment lines
    # Captures the leading whitespace and the code after the comment
    pattern = r'^(\s*)# TODO: Review unreachable code - (.*)$'
    
    # Replace each TODO comment with just the code part, preserving indentation
    fixed_content = re.sub(pattern, r'\1\2', content, flags=re.MULTILINE)
    
    # Count how many replacements were made
    original_lines = content.count('\n')
    fixed_lines = fixed_content.count('\n')
    todo_count = content.count('# TODO: Review unreachable code')
    
    print(f"Original lines: {original_lines}")
    print(f"TODO comments found: {todo_count}")
    print(f"Lines after fix: {fixed_lines}")
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.write(fixed_content)
    
    print(f"\nRemoved {todo_count} TODO comments from {file_path}")
    
    # Test if it compiles
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("✓ File compiles successfully!")
    except py_compile.PyCompileError as e:
        print(f"✗ Compilation error: {e}")
        # Show the error location
        try:
            error_match = re.search(r'line (\d+)', str(e))
            if error_match:
                error_line = int(error_match.group(1))
                lines = fixed_content.split('\n')
                print(f"\nError at line {error_line}:")
                for i in range(max(0, error_line - 3), min(len(lines), error_line + 3)):
                    prefix = ">>> " if i == error_line - 1 else "    "
                    print(f"{prefix}{i+1}: {lines[i]}")
        except:
            pass

if __name__ == "__main__":
    remove_todo_comments()