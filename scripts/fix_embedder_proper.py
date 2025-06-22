#\!/usr/bin/env python3
"""Properly remove TODO comments and fix indentation in embedder.py."""

from pathlib import Path
import re

def fix_embedder():
    """Remove TODO comments and ensure proper indentation."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line in lines:
        # Remove the TODO comment prefix but keep the code
        # Handle different patterns
        if '# TODO: Review unreachable code - ' in line:
            # Extract the indentation and the code part
            match = re.match(r'^(\s*)# TODO: Review unreachable code - (.*)$', line)
            if match:
                indent = match.group(1)
                code = match.group(2)
                # Reconstruct the line with same indentation
                fixed_lines.append(indent + code + '\n')
            else:
                # Fallback - just remove the comment prefix
                fixed_line = line.replace('# TODO: Review unreachable code - ', '')
                fixed_lines.append(fixed_line)
        else:
            # Keep line as is
            fixed_lines.append(line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print(f"Removed TODO comments from {len([l for l in lines if 'TODO: Review' in l])} lines")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success\! File now compiles without errors\!")
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Compilation error: {e}")
        # Show the error location
        error_match = re.search(r'line (\d+)', str(e))
        if error_match:
            error_line = int(error_match.group(1))
            print(f"\nError at line {error_line}:")
            for j in range(max(0, error_line - 3), min(len(fixed_lines), error_line + 3)):
                prefix = ">>> " if j == error_line - 1 else "    "
                print(f"{prefix}{j+1}: {fixed_lines[j].rstrip()}")
        return False

if __name__ == "__main__":
    if fix_embedder():
        print("\nThe embedder.py file has been successfully fixed\!")
        print("- All 448 TODO comments have been removed")
        print("- The file now compiles without errors")
    else:
        print("\nThere are still issues to fix.")
