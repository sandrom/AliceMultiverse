#!/usr/bin/env python3
"""Fix method body indentation in embedder.py."""

import re
from pathlib import Path

def fix_method_indentation():
    """Fix all method body indentation issues."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_method = False
    method_indent = 0
    
    for i, line in enumerate(lines):
        # Check if this is a method definition
        if re.match(r'^(\s+)def\s+\w+\s*\(', line):
            in_method = True
            method_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue
        
        # If we're in a method and find a line that should be indented but isn't
        if in_method and line.strip() and not line[0].isspace():
            # Check if this line starts a new method or class
            if line.strip().startswith(('def ', 'class ')) or (i > 0 and not lines[i-1].strip()):
                # End of current method
                in_method = False
                fixed_lines.append(line)
            else:
                # This line needs indentation
                fixed_lines.append(' ' * (method_indent + 4) + line.strip() + '\n')
        else:
            fixed_lines.append(line)
            
            # Check if method ends
            if in_method and line.strip() == '' and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() and not next_line[0].isspace():
                    in_method = False
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed method body indentation")
    
    # Test compilation
    import py_compile
    error_count = 0
    max_iterations = 10
    
    while error_count < max_iterations:
        try:
            py_compile.compile(str(file_path), doraise=True)
            print("✓ File now compiles successfully!")
            return True
        except py_compile.PyCompileError as e:
            error_count += 1
            print(f"Iteration {error_count}: {e}")
            
            # Try to fix the specific error
            error_match = re.search(r'line (\d+)', str(e))
            if error_match:
                error_line = int(error_match.group(1)) - 1  # 0-indexed
                
                # Re-read the file
                with file_path.open('r') as f:
                    lines = f.readlines()
                
                # Fix the specific line if it needs indentation
                if error_line < len(lines):
                    line = lines[error_line]
                    if line.strip() and not line[0].isspace() and error_line > 0:
                        # Check previous line for context
                        prev_line = lines[error_line - 1]
                        if prev_line.strip().endswith(':'):
                            # Add indentation
                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                            lines[error_line] = ' ' * (prev_indent + 4) + line.strip() + '\n'
                            
                            # Write back
                            with file_path.open('w') as f:
                                f.writelines(lines)
                            continue
            
            # If we can't fix it, break
            break
    
    return False

if __name__ == "__main__":
    success = fix_method_indentation()
    if not success:
        print("\n⚠️  Could not fix all issues automatically.")