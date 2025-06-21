#!/usr/bin/env python3
"""Fix indentation in cli_handlers.py after uncommenting."""

import re
from pathlib import Path

def fix_indentation(content: str) -> str:
    """Fix indentation in Python code."""
    lines = content.split('\n')
    fixed_lines = []
    
    in_function = False
    function_indent = 0
    
    for i, line in enumerate(lines):
        # Detect function definition
        if re.match(r'^def\s+\w+\(.*\):\s*$', line):
            in_function = True
            function_indent = 0
            fixed_lines.append(line)
            continue
        
        # Handle empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # If we're in a function
        if in_function:
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            
            # Docstring should be at function_indent + 4
            if stripped.startswith('"""'):
                if current_indent < 4:
                    line = '    ' + stripped
            # Other lines need proper indentation
            elif current_indent < 4 and stripped:
                # Determine proper indent based on context
                if any(stripped.startswith(kw) for kw in ['if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ', 'def ', 'class ', 'from ', 'import ', 'return']):
                    line = '    ' + stripped
                elif i > 0 and fixed_lines[i-1].rstrip().endswith(':'):
                    # Previous line ended with colon, increase indent
                    line = '        ' + stripped
                else:
                    # Check if this line is part of a continued statement
                    prev_line = fixed_lines[i-1].strip() if i > 0 else ''
                    if prev_line and not prev_line.endswith((':',  ',', '(', '[', '{')):
                        # Likely a continued line, maintain or increase indent
                        prev_indent = len(fixed_lines[i-1]) - len(fixed_lines[i-1].lstrip())
                        if prev_indent >= 4:
                            line = ' ' * prev_indent + stripped
                        else:
                            line = '    ' + stripped
                    else:
                        line = '    ' + stripped
                        
            # Check if we're exiting the function
            if line.strip() == 'return 0' or (line.strip().startswith('return ') and current_indent <= 4):
                in_function = False
                
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def main():
    file_path = Path('alicemultiverse/interface/cli_handlers.py')
    
    print(f"Fixing indentation in {file_path}")
    
    content = file_path.read_text()
    fixed_content = fix_indentation(content)
    
    file_path.write_text(fixed_content)
    print("Indentation fixed!")

if __name__ == '__main__':
    main()