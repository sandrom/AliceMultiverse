#!/usr/bin/env python3
"""Fix nested indentation in performance_tracker.py."""

from pathlib import Path

def fix_nested_indentation():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Count the current indentation level
        stripped = line.lstrip()
        if not stripped:  # Empty line
            fixed_lines.append(line)
            continue
            
        current_indent = len(line) - len(stripped)
        
        # Check if this line needs additional indentation
        # Lines with 8 spaces that contain control flow keywords need their bodies indented
        if current_indent == 8 and any(stripped.startswith(kw) for kw in ['if ', 'else:', 'elif ', 'for ', 'while ', 'try:', 'except ', 'finally:', 'with ']):
            fixed_lines.append(line)
            continue
        
        # Lines with exactly 8 spaces that are not control flow statements need 4 more spaces
        if current_indent == 8 and not any(stripped.startswith(kw) for kw in ['if ', 'else:', 'elif ', 'for ', 'while ', 'try:', 'except ', 'finally:', 'with ', 'def ', 'class ', 'return ', '"""', '#']):
            # This is a statement inside a control structure, add 4 more spaces
            fixed_lines.append("    " + line)
        else:
            fixed_lines.append(line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed nested indentation in {file_path}")

if __name__ == "__main__":
    fix_nested_indentation()