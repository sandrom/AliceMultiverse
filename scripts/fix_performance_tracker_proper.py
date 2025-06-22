#!/usr/bin/env python3
"""Fix performance_tracker.py by uncommenting TODO: Review unreachable code lines with proper indentation."""

import re
from pathlib import Path

def fix_performance_tracker():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if line contains the TODO comment
        if "# TODO: Review unreachable code -" in line:
            # Extract the indentation and code
            match = re.match(r'^(\s*)# TODO: Review unreachable code - (.*)$', line)
            if match:
                base_indent = match.group(1)
                code = match.group(2)
                
                # For multi-line docstrings or method definitions, we need to collect all related lines
                if code.strip().startswith('"""'):
                    # This is the start of a docstring
                    fixed_lines.append(base_indent + '    ' + code + '\n')
                    i += 1
                    
                    # Process subsequent docstring lines
                    while i < len(lines) and "# TODO: Review unreachable code -" in lines[i]:
                        match = re.match(r'^(\s*)# TODO: Review unreachable code - (.*)$', lines[i])
                        if match:
                            code = match.group(2)
                            if code.strip() == '"""':
                                # End of docstring
                                fixed_lines.append(base_indent + '    ' + code + '\n')
                                i += 1
                                break
                            else:
                                # Docstring content
                                fixed_lines.append(base_indent + '    ' + code + '\n')
                                i += 1
                        else:
                            break
                    continue
                    
                elif code.strip().startswith('def '):
                    # This is a method definition - use base_indent as is
                    fixed_lines.append(base_indent + code + '\n')
                else:
                    # This is method body code - add 4 spaces to base_indent
                    fixed_lines.append(base_indent + '    ' + code + '\n')
            else:
                # If no match, keep the original line
                fixed_lines.append(line)
        else:
            # Not a TODO line, keep as is
            fixed_lines.append(line)
        
        i += 1
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path} with proper indentation")
    print(f"Total lines processed: {len(lines)}")

if __name__ == "__main__":
    fix_performance_tracker()