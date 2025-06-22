#!/usr/bin/env python3
"""Fix indentation in performance_tracker.py - add 4 spaces to method bodies."""

from pathlib import Path

def fix_indentation():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_class = False
    in_method = False
    
    for i, line in enumerate(lines):
        # Check if we're entering the PerformanceTracker class
        if line.strip() == "class PerformanceTracker:":
            in_class = True
            fixed_lines.append(line)
            continue
        
        # If we're in the class
        if in_class:
            # Check if this is a method definition (starts with exactly 4 spaces and 'def ')
            if line.startswith("    def ") and not line.startswith("     "):
                in_method = True
                fixed_lines.append(line)
                continue
            
            # Check if we're at the start of a new method or end of class
            if in_method and line.strip() and not line.startswith("    "):
                # We've reached something that's not indented - end of class
                in_method = False
                in_class = False
            elif in_method and i + 1 < len(lines) and lines[i + 1].startswith("    def ") and not lines[i + 1].startswith("     "):
                # Next line is a new method definition
                in_method = False
            
            # If we're in a method and the line has exactly 4 spaces followed by content
            if in_method and line.startswith("    ") and len(line) > 4 and line[4] != ' ':
                # Add 4 more spaces to make it 8 spaces total
                fixed_lines.append("    " + line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    fix_indentation()