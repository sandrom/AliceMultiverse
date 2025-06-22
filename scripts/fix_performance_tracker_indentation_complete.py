#!/usr/bin/env python3
"""Fix all indentation issues in performance_tracker.py."""

from pathlib import Path
import re

def fix_all_indentation():
    file_path = Path("alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split into lines for processing
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Keep class and function definitions as they are
        if line.strip().startswith('class ') or (line.strip().startswith('def ') and line.startswith('    def ')):
            fixed_lines.append(line)
            i += 1
            continue
        
        # Handle method content that needs proper indentation
        if line.startswith('    ') and len(line) > 4 and line[4] != ' ':
            # This line starts with exactly 4 spaces - it's method content that needs 8 spaces
            if any(line.strip().startswith(keyword) for keyword in ['"""', "'''", 'Args:', 'Returns:', 'if ', 'else:', 'elif ', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ', 'return ', 'pass', 'raise ', 'yield ', 'break', 'continue']):
                # This is definitely method content
                fixed_lines.append('    ' + line)
            elif line.strip() and not line.strip().startswith('#'):
                # Regular statement or assignment
                fixed_lines.append('    ' + line)
            else:
                # Comments and other lines
                fixed_lines.append(line)
        else:
            # Keep the line as is
            fixed_lines.append(line)
        
        i += 1
    
    # Join back and write
    fixed_content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed all indentation issues in {file_path}")
    
    # Now try to compile to check for syntax errors
    try:
        import ast
        with open(file_path, 'r') as f:
            ast.parse(f.read())
        print("✓ Syntax is now valid!")
        return True
    except SyntaxError as e:
        print(f"✗ Still has syntax error: {e}")
        return False

if __name__ == "__main__":
    fix_all_indentation()