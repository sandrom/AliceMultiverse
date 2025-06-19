#!/usr/bin/env python3
"""Fix indentation in advanced_tagger.py properly."""

import re

# Read the file
with open('alicemultiverse/understanding/advanced_tagger.py', 'r') as f:
    lines = f.readlines()

# Fix indentation
fixed_lines = []
class_level = 0
inside_class = False
inside_method = False
method_level = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Track class definitions
    if stripped.startswith('class ') and stripped.endswith(':'):
        inside_class = True
        inside_method = False
        class_level = 0  # Classes should be at top level
        fixed_lines.append(line)
        continue
    
    # Track method definitions inside classes
    if inside_class and stripped.startswith('def ') and stripped.endswith(':'):
        inside_method = True
        method_level = 4  # Methods inside classes should be indented 4 spaces
        fixed_lines.append(' ' * method_level + stripped + '\n')
        continue
    
    # Handle lines inside methods
    if inside_method and stripped:
        # Check if this line should end the method (another def or class)
        if stripped.startswith('def ') or stripped.startswith('class '):
            # Check original indentation
            orig_indent = len(line) - len(line.lstrip())
            if orig_indent <= method_level:
                inside_method = False
                # This is a new method at class level
                if stripped.startswith('def '):
                    fixed_lines.append(' ' * method_level + stripped + '\n')
                    inside_method = True
                else:
                    # New class
                    inside_class = True
                    inside_method = False
                    fixed_lines.append(stripped + '\n')
                continue
        
        # Regular line inside method - indent 8 spaces (4 for class + 4 for method)
        if not line.startswith(' ' * 8) and stripped:
            fixed_lines.append(' ' * 8 + stripped + '\n')
        else:
            fixed_lines.append(line)
    elif inside_class and not inside_method and stripped:
        # Line directly inside class but not in method
        if not line.startswith(' ' * 4) and stripped:
            fixed_lines.append(' ' * 4 + stripped + '\n')
        else:
            fixed_lines.append(line)
    else:
        # Keep empty lines and top-level code as is
        fixed_lines.append(line)

# Write the fixed content
with open('alicemultiverse/understanding/advanced_tagger.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed indentation in advanced_tagger.py")