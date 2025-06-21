#!/usr/bin/env python3
"""Fix indentation in cli_parser.py after uncommenting."""

import re
from pathlib import Path

def fix_indentation():
    file_path = Path("alicemultiverse/interface/cli_parser.py")
    
    content = file_path.read_text()
    lines = content.split('\n')
    fixed_lines = []
    
    in_function = False
    
    for i, line in enumerate(lines):
        # Detect function definition
        if re.match(r'^def\s+\w+\(.*\).*:$', line):
            in_function = True
            fixed_lines.append(line)
            continue
        
        # If we're in a function and the line has no indentation but isn't empty
        if in_function and line and not line[0].isspace():
            # This line should be indented - it's likely a docstring or code
            if line.startswith('"""'):
                line = '    ' + line
            elif not line.startswith('def '):
                line = '    ' + line
            
        # Check if we're exiting the function
        if line.strip() == '' and i + 1 < len(lines) and lines[i + 1].startswith('def '):
            in_function = False
            
        fixed_lines.append(line)
    
    fixed_content = '\n'.join(fixed_lines)
    file_path.write_text(fixed_content)
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    fix_indentation()