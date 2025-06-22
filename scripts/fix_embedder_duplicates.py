#\!/usr/bin/env python3
"""Remove duplicate _create_xmp_from_metadata methods and fix indentation."""

from pathlib import Path
import re

def remove_duplicates_and_fix():
    """Remove duplicate methods and fix indentation issues."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # Find all occurrences of _create_xmp_from_metadata
    method_starts = []
    for i, line in enumerate(lines):
        if 'def _create_xmp_from_metadata(self' in line:
            method_starts.append(i)
    
    print(f"Found {len(method_starts)} occurrences of _create_xmp_from_metadata at lines: {[s+1 for s in method_starts]}")
    
    if len(method_starts) > 1:
        # Keep only the first occurrence, remove others
        # Work backwards to avoid index issues
        for start_idx in reversed(method_starts[1:]):
            # Find the end of this method (next def or end of file)
            end_idx = len(lines)
            for j in range(start_idx + 1, len(lines)):
                if lines[j].strip().startswith('def ') and lines[j][0] not in ' \t':
                    end_idx = j
                    break
            
            # Remove lines from start_idx to end_idx
            print(f"Removing duplicate method from line {start_idx + 1} to {end_idx}")
            del lines[start_idx:end_idx]
    
    # Fix the indentation of the remaining _create_xmp_from_metadata method
    # Find it again after deletions
    for i, line in enumerate(lines):
        if 'def _create_xmp_from_metadata(self' in line:
            # Make sure it's properly indented (4 spaces for a method in a class)
            lines[i] = '    def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:\n'
            
            # Fix the docstring and body indentation
            j = i + 1
            while j < len(lines):
                if lines[j].strip() and not lines[j].strip().startswith('"""'):
                    # Check if we've reached the next method or end of class
                    if lines[j].strip().startswith('def ') or (lines[j][0] not in ' \t' and lines[j].strip()):
                        break
                
                # Fix indentation for docstrings and method body
                if lines[j].strip().startswith('"""'):
                    lines[j] = '        ' + lines[j].strip() + '\n'
                elif lines[j].strip() and j < i + 20:  # Only fix the first part of the method
                    # This is part of the method body
                    stripped = lines[j].strip()
                    if not stripped.startswith('def ') and not stripped.startswith('class '):
                        lines[j] = '        ' + stripped + '\n'
                
                j += 1
            break
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(lines)
    
    print("\nFixed content written to file")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success! File now compiles without errors!")
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Compilation error: {e}")
        # Show the error location
        try:
            error_match = re.search(r'line (\d+)', str(e))
            if error_match:
                error_line = int(error_match.group(1))
                print(f"\nError at line {error_line}:")
                for j in range(max(0, error_line - 3), min(len(lines), error_line + 3)):
                    prefix = ">>> " if j == error_line - 1 else "    "
                    print(f"{prefix}{j+1}: {lines[j].rstrip()}")
        except:
            pass
        return False

if __name__ == "__main__":
    remove_duplicates_and_fix()