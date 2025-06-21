#!/usr/bin/env python3
"""Fix indentation in Python files after uncommenting."""
import sys
import re

def fix_indentation(file_path):
    """Fix indentation in a Python file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    current_indent = 0
    in_multiline = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue
            
        # Handle multiline strings
        if '"""' in line or "'''" in line:
            in_multiline = not in_multiline
            if in_multiline or line.count('"""') == 2 or line.count("'''") == 2:
                fixed_lines.append(' ' * current_indent + stripped + '\n')
                continue
        
        if in_multiline:
            fixed_lines.append(' ' * current_indent + stripped + '\n')
            continue
        
        # Decrease indent for these keywords
        if stripped.startswith(('elif', 'else:', 'except', 'finally:', 'case')):
            if current_indent >= 4:
                current_indent -= 4
        
        # Handle decorators
        if stripped.startswith('@'):
            fixed_lines.append(stripped + '\n')
            continue
            
        # Handle class and function definitions
        if stripped.startswith(('class ', 'def ', 'async def ')):
            # Find the appropriate indent level based on previous lines
            for j in range(i-1, -1, -1):
                prev = lines[j].strip()
                if prev and not prev.startswith(('@', '#')):
                    if prev.startswith(('class ', 'def ', 'async def ')):
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        break
                    elif j == 0 or (prev and not prev.endswith(':')):
                        current_indent = 0
                        break
            
            fixed_lines.append(' ' * current_indent + stripped + '\n')
            if stripped.endswith(':'):
                current_indent += 4
            continue
        
        # Add the line with current indentation
        fixed_lines.append(' ' * current_indent + stripped + '\n')
        
        # Increase indent after these patterns
        if stripped.endswith(':') and not stripped.startswith('#'):
            current_indent += 4
        
        # Decrease indent after return, break, continue, pass, raise
        if stripped.startswith(('return', 'break', 'continue', 'pass', 'raise')):
            if current_indent >= 4:
                current_indent -= 4
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_indentation(sys.argv[1])
    else:
        print("Usage: python fix_indent_generic.py <file_path>")