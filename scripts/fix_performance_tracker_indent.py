#!/usr/bin/env python3
"""Fix performance_tracker.py by uncommenting TODO: Review unreachable code lines with proper indentation."""

import re
from pathlib import Path

def fix_performance_tracker():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    # Read the original file again
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Restore from backup or re-read the file with TODO comments
    lines = content.split('\n')
    
    fixed_lines = []
    
    for line in lines:
        # Check if line contains the TODO comment
        if "# TODO: Review unreachable code -" in line and len(line) > 0:
            # Extract the actual code after the TODO comment
            # The pattern should preserve the original indentation
            match = re.match(r'^(\s*)# TODO: Review unreachable code - (.*)$', line)
            if match:
                indent = match.group(1)
                code = match.group(2)
                # Check if this is part of a method definition that needs additional indentation
                # The code after the TODO comment should maintain its relative indentation
                if code.strip() and not code.startswith('def '):
                    # This is method body code, it needs the base indent plus method indent
                    fixed_line = indent + '    ' + code
                else:
                    # This is a method definition or empty line, use original indent
                    fixed_line = indent + code
                fixed_lines.append(fixed_line)
            else:
                # If no match, keep the original line
                fixed_lines.append(line[:-1] if line.endswith('\n') else line)
        else:
            fixed_lines.append(line[:-1] if line.endswith('\n') else line)
    
    # Join lines and write back
    fixed_content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed {file_path} with proper indentation")

if __name__ == "__main__":
    fix_performance_tracker()