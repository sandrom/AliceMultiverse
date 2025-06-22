#!/usr/bin/env python3
"""Fix all indentation issues in embedder.py comprehensively."""

from pathlib import Path

def fix_embedder_indentation():
    """Fix all indentation issues systematically."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_class = False
    in_method = False
    in_docstring = False
    docstring_quote = None
    expected_indent = 0
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        stripped = line.strip()
        
        # Check for docstring start/end
        if '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                in_docstring = True
                docstring_quote = '"""' if '"""' in stripped else "'''"
                # If it's a one-line docstring
                if stripped.count(docstring_quote) >= 2:
                    in_docstring = False
            else:
                if docstring_quote in stripped:
                    in_docstring = False
        
        # Handle class definitions
        if stripped.startswith('class ') and ':' in stripped:
            in_class = True
            in_method = False
            expected_indent = 0
            fixed_lines.append(line.lstrip())  # Classes at root level
            continue
            
        # Handle method definitions
        if stripped.startswith('def ') and ':' in stripped:
            if in_class:
                in_method = True
                expected_indent = 4  # Methods in classes are indented 4 spaces
                fixed_lines.append(' ' * 4 + stripped + '\n')
            else:
                # Top-level function
                expected_indent = 0
                fixed_lines.append(stripped + '\n')
            continue
        
        # Handle lines inside methods
        if in_method:
            # If we hit another method or class, we're done with this method
            if (stripped.startswith('def ') or stripped.startswith('class ')) and not in_docstring:
                in_method = True  # New method
                expected_indent = 4
                fixed_lines.append(' ' * 4 + stripped + '\n')
                continue
            
            # Docstrings in methods should be indented 8 spaces
            if in_docstring or stripped.startswith('"""') or stripped.startswith("'''"):
                fixed_lines.append(' ' * 8 + stripped + '\n')
                continue
            
            # Handle control structures
            if any(stripped.startswith(kw) for kw in ['if ', 'elif ', 'else:', 'try:', 'except', 'finally:', 'for ', 'while ', 'with ']):
                # These should be at method body level (8 spaces)
                fixed_lines.append(' ' * 8 + stripped + '\n')
                continue
            
            # Handle return statements and other code
            if stripped.startswith('return ') or stripped.startswith('raise ') or stripped.startswith('pass') or stripped.startswith('continue') or stripped.startswith('break'):
                # Check previous non-empty line to determine indent
                prev_line = None
                for j in range(i-1, -1, -1):
                    if lines[j].strip():
                        prev_line = lines[j]
                        break
                
                if prev_line and any(prev_line.strip().endswith(kw) for kw in [':', 'else:', 'try:', 'finally:']):
                    # Should be indented one level more than the control structure
                    fixed_lines.append(' ' * 12 + stripped + '\n')
                else:
                    # Regular method body
                    fixed_lines.append(' ' * 8 + stripped + '\n')
                continue
            
            # Regular code lines in method body
            fixed_lines.append(' ' * 8 + stripped + '\n')
            continue
        
        # If we're in a class but not in a method (e.g., class variables)
        if in_class and not in_method:
            fixed_lines.append(' ' * 4 + stripped + '\n')
            continue
        
        # Default: keep as is or fix obvious issues
        if line[0] not in ' \t' or not in_class:
            # Top-level code
            fixed_lines.append(stripped + '\n')
        else:
            # Keep existing indentation
            fixed_lines.append(line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation")
    
    # Now use black to format properly
    import subprocess
    try:
        result = subprocess.run(['black', str(file_path)], capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully formatted with black")
        else:
            print(f"Black formatting failed: {result.stderr}")
    except Exception as e:
        print(f"Error running black: {e}")
    
    # Check for duplicate methods
    with file_path.open('r') as f:
        content = f.read()
    
    duplicates = content.count('def _create_xmp_from_metadata')
    if duplicates > 1:
        print(f"\nWarning: Found {duplicates} _create_xmp_from_metadata methods")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success! File now compiles without errors!")
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Compilation error: {e}")
        return False

if __name__ == "__main__":
    if fix_embedder_indentation():
        print("\nThe embedder.py file has been successfully fixed!")
    else:
        print("\nThere are still issues to fix.")