#\!/usr/bin/env python3
"""Final cleanup of embedder.py - remove remaining TODO comments and duplicate methods."""

from pathlib import Path
import re

def final_cleanup():
    """Remove remaining TODO comments and duplicate methods."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # Remove lines that are just TODO comments
    cleaned_lines = []
    for line in lines:
        if '# TODO: Review unreachable code -' in line:
            # This is a TODO line - skip it
            continue
        cleaned_lines.append(line)
    
    # Now find and remove duplicate _create_xmp_from_metadata methods
    # First, identify all occurrences
    method_starts = []
    for i, line in enumerate(cleaned_lines):
        if 'def _create_xmp_from_metadata(self' in line:
            method_starts.append(i)
    
    print(f"Found {len(method_starts)} instances of _create_xmp_from_metadata")
    
    if len(method_starts) > 1:
        # Keep only the first occurrence
        # Work backwards to avoid index issues
        for start_idx in reversed(method_starts[1:]):
            # Find the end of this method
            end_idx = len(cleaned_lines)
            for j in range(start_idx + 1, len(cleaned_lines)):
                # Look for next method or class definition at the same indentation level
                if cleaned_lines[j].strip() and not cleaned_lines[j].startswith(' '):
                    end_idx = j
                    break
                if re.match(r'^    def ', cleaned_lines[j]):
                    end_idx = j
                    break
            
            # Remove lines
            print(f"Removing duplicate method from line {start_idx + 1} to {end_idx}")
            del cleaned_lines[start_idx:end_idx]
    
    # Write the cleaned content
    with file_path.open('w') as f:
        f.writelines(cleaned_lines)
    
    print(f"\nCleaned file written. Removed {len(lines) - len(cleaned_lines)} lines")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success\! File now compiles without errors\!")
        
        # Final stats
        with file_path.open('r') as f:
            content = f.read()
        
        print(f"\nFinal statistics:")
        print(f"- Total lines: {content.count(chr(10))}")
        print(f"- TODO comments: {content.count('TODO: Review unreachable code')}")
        print(f"- _create_xmp_from_metadata methods: {content.count('def _create_xmp_from_metadata')}")
        
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Compilation error: {e}")
        return False

if __name__ == "__main__":
    if final_cleanup():
        print("\n✅ The embedder.py file has been successfully fixed\!")
        print("- All TODO comments have been removed")
        print("- All duplicate methods have been removed")
        print("- The file compiles without errors")
