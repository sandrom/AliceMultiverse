#!/usr/bin/env python3
"""Fix all method indentation in embedder.py."""

from pathlib import Path
import re

def fix_all_method_indentation():
    """Fix indentation for all methods in the file."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    in_class = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check for class definition
        if stripped.startswith('class ') and ':' in stripped:
            in_class = True
            fixed_lines.append(line)
            i += 1
            continue
        
        # Check for method definition inside a class
        if in_class and re.match(r'^(\s*)def\s+\w+.*:$', line):
            # This is a method definition
            indent_match = re.match(r'^(\s*)def', line)
            base_indent = len(indent_match.group(1)) if indent_match else 0
            
            # Method definitions in classes should have 4 spaces
            if base_indent == 0:
                line = '    ' + line.lstrip()
            
            fixed_lines.append(line)
            i += 1
            
            # Now fix all lines that belong to this method
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                # Check if we've reached the next method or class
                if next_stripped and (
                    (next_stripped.startswith('def ') and not next_line.startswith(' ' * 8)) or
                    (next_stripped.startswith('class ') and ':' in next_stripped)
                ):
                    break
                
                # Fix indentation for method body
                if next_stripped:
                    # Docstrings should be indented 8 spaces
                    if next_stripped.startswith('"""') or next_stripped.startswith("'''"):
                        fixed_lines.append(' ' * 8 + next_stripped + '\n')
                    # Regular code should be indented 8 spaces minimum
                    elif not next_line.startswith(' ' * 8) and i < len(lines) - 1:
                        # Ensure at least 8 spaces of indentation
                        current_indent = len(next_line) - len(next_line.lstrip())
                        if current_indent < 8:
                            fixed_lines.append(' ' * 8 + next_stripped + '\n')
                        else:
                            fixed_lines.append(next_line)
                    else:
                        fixed_lines.append(next_line)
                else:
                    # Empty line
                    fixed_lines.append(next_line)
                
                i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed method indentation")
    
    # Test with black
    import subprocess
    try:
        result = subprocess.run(['black', str(file_path)], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Black formatting successful!")
        else:
            print(f"❌ Black failed: {result.stderr}")
    except Exception as e:
        print(f"Error running black: {e}")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("✅ File compiles successfully!")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Compilation error: {e}")
        return False

if __name__ == "__main__":
    if fix_all_method_indentation():
        print("\n🎉 Successfully fixed embedder.py!")
    else:
        print("\n⚠️  Some issues remain")