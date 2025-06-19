#!/usr/bin/env python3
"""Fix indentation issues in advanced_tagger.py"""

import re

def fix_indentation(content):
    """Fix indentation in Python file content."""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a class or function definition
        if re.match(r'^(class|def)\s+\w+.*:$', line.strip()) and line.strip():
            # This is an unindented class/function definition
            fixed_lines.append(line)
            i += 1
            
            # Check and fix the next lines that should be indented
            while i < len(lines):
                next_line = lines[i]
                
                # If it's an empty line, keep it
                if not next_line.strip():
                    fixed_lines.append(next_line)
                    i += 1
                    continue
                
                # If it's another class/def at the same level, we're done with this block
                if re.match(r'^(class|def)\s+\w+.*:$', next_line.strip()):
                    break
                
                # If the line is not indented but should be, indent it
                if not next_line.startswith(' ') and not next_line.startswith('\t'):
                    fixed_lines.append('    ' + next_line)
                else:
                    fixed_lines.append(next_line)
                
                i += 1
        else:
            # Check if this line should be indented based on context
            if i > 0 and line.strip() and not line.startswith(' '):
                # Look back to see if we're inside a class or function
                indent_level = 0
                for j in range(i - 1, -1, -1):
                    prev_line = lines[j].rstrip()
                    if prev_line.endswith(':'):
                        # Found a block start
                        indent_level = len(prev_line) - len(prev_line.lstrip()) + 4
                        break
                    elif prev_line and not prev_line.strip().startswith('#'):
                        # Found a regular line, use its indentation
                        curr_indent = len(prev_line) - len(prev_line.lstrip())
                        if curr_indent > 0:
                            indent_level = curr_indent
                            break
                
                if indent_level > 0:
                    fixed_lines.append(' ' * indent_level + line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

# Read the file
with open('alicemultiverse/understanding/advanced_tagger.py', 'r') as f:
    content = f.read()

# Fix indentation
fixed_content = fix_indentation(content)

# Write back
with open('alicemultiverse/understanding/advanced_tagger.py', 'w') as f:
    f.write(fixed_content)

print("Fixed indentation in advanced_tagger.py")