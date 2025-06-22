#!/usr/bin/env python3
"""Fix performance_tracker.py by uncommenting TODO: Review unreachable code lines."""

import re
from pathlib import Path

def fix_performance_tracker():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line in lines:
        # Check if line contains the TODO comment
        if "# TODO: Review unreachable code -" in line:
            # Extract the actual code after the TODO comment
            match = re.match(r'^(\s*)# TODO: Review unreachable code - (.*)$', line)
            if match:
                indent = match.group(1)
                code = match.group(2)
                # Reconstruct the line with proper indentation
                fixed_line = indent + code + '\n'
                fixed_lines.append(fixed_line)
            else:
                # If no match, keep the original line
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path}")
    print(f"Total lines processed: {len(lines)}")

if __name__ == "__main__":
    fix_performance_tracker()