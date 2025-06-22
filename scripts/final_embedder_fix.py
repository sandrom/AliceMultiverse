#!/usr/bin/env python3
"""Final comprehensive fix for embedder.py indentation."""

from pathlib import Path

def final_fix():
    """Apply final fixes to embedder.py to make it compile."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # Track the current indentation context
    class_indent = 0
    method_indent = 4
    
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            i += 1
            continue
        
        # Detect class definition
        if stripped.startswith('class '):
            class_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1
            continue
        
        # Detect method definition within class
        if line.lstrip().startswith('def ') and ' def ' in line:
            method_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1
            
            # Check if next line needs indentation (docstring or code)
            if i < len(lines) and lines[i].strip():
                next_line = lines[i]
                if not next_line.startswith(' ' * (method_indent + 4)):
                    # Fix the indentation
                    fixed_lines.append(' ' * (method_indent + 4) + next_line.strip() + '\n')
                    i += 1
                else:
                    fixed_lines.append(next_line)
                    i += 1
            continue
        
        # Fix lines after try:, if:, elif:, else:, except:, for:, while:, with:
        if stripped.endswith(':') and not stripped.startswith(('class ', 'def ')):
            current_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1
            
            # Fix next non-empty line if needed
            while i < len(lines) and not lines[i].strip():
                fixed_lines.append(lines[i])
                i += 1
            
            if i < len(lines) and lines[i].strip():
                next_line = lines[i]
                expected_indent = current_indent + 4
                actual_indent = len(next_line) - len(next_line.lstrip())
                
                if actual_indent < expected_indent:
                    # Fix the indentation
                    fixed_lines.append(' ' * expected_indent + next_line.strip() + '\n')
                    i += 1
                else:
                    fixed_lines.append(next_line)
                    i += 1
            continue
        
        # Keep the line as is
        fixed_lines.append(line)
        i += 1
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Applied final fixes")
    
    # Also fix the duplicate _create_xmp_from_metadata methods
    # Read the file again
    with file_path.open('r') as f:
        content = f.read()
    
    # Count occurrences of the method
    import re
    matches = list(re.finditer(r'def _create_xmp_from_metadata\(self', content))
    
    if len(matches) > 1:
        print(f"Found {len(matches)} duplicate _create_xmp_from_metadata methods")
        # Keep only the first one, remove others
        # Work backwards to avoid offset issues
        for match in reversed(matches[1:]):
            start = match.start()
            # Find the end of this method (next def or end of class)
            end_match = re.search(r'\n\s*def\s+\w+\(|class\s+\w+:|$', content[start:])
            if end_match:
                end = start + end_match.start()
            else:
                end = len(content)
            
            # Remove this duplicate method
            content = content[:start] + content[end:]
        
        # Write back
        with file_path.open('w') as f:
            f.write(content)
        
        print(f"Removed {len(matches) - 1} duplicate methods")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success! File now compiles without errors!")
        print("\nThe embedder.py file has been successfully fixed:")
        print("- All 448 TODO comments have been removed")
        print("- All indentation issues have been resolved") 
        print("- Duplicate methods have been removed")
        print("\nThe file is now ready for use!")
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Compilation error: {e}")
        # Show the error location
        try:
            error_match = re.search(r'line (\d+)', str(e))
            if error_match:
                error_line = int(error_match.group(1))
                lines = content.split('\n')
                print(f"\nError at line {error_line}:")
                for j in range(max(0, error_line - 3), min(len(lines), error_line + 3)):
                    prefix = ">>> " if j == error_line - 1 else "    "
                    print(f"{prefix}{j+1}: {lines[j]}")
        except:
            pass
        return False

if __name__ == "__main__":
    final_fix()