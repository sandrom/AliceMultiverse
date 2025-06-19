#!/usr/bin/env python3
"""Fix indentation issues in memory_optimization.py."""

from pathlib import Path

def fix_memory_optimization():
    """Fix the memory_optimization.py file."""
    file_path = Path("alicemultiverse/core/memory_optimization.py")
    
    # Read the file
    content = file_path.read_text()
    lines = content.split('\n')
    
    # Fix specific issues
    fixed_lines = []
    i = 0
    in_class = False
    in_function = False
    class_indent = 0
    function_indent = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        
        # Track class and function context
        if stripped.startswith('class '):
            in_class = True
            class_indent = len(line) - len(stripped)
            in_function = False
            fixed_lines.append(line)
        elif stripped.startswith('def ') and in_class:
            in_function = True
            function_indent = class_indent + 4
            # Ensure proper indentation for method definitions
            fixed_lines.append(' ' * function_indent + stripped)
        elif in_function and stripped and not line.startswith(' '):
            # Fix unindented lines inside functions
            if stripped.startswith(('import', 'from')):
                fixed_lines.append(' ' * (function_indent + 4) + stripped)
            elif stripped.startswith(('if ', 'elif ', 'else:', 'return ', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ')):
                fixed_lines.append(' ' * (function_indent + 4) + stripped)
            else:
                # Variable assignments and other statements
                fixed_lines.append(' ' * (function_indent + 4) + stripped)
        else:
            # Keep the line as is
            fixed_lines.append(line)
            
        i += 1
    
    # Write back
    file_path.write_text('\n'.join(fixed_lines))
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    fix_memory_optimization()