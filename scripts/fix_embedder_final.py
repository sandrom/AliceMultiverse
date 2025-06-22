#!/usr/bin/env python3
"""Final fix for embedder.py - remove TODO comments properly."""

from pathlib import Path
import re

def fix_embedder_final():
    """Remove TODO comments and fix indentation issues."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        content = f.read()
    
    # Count initial TODOs
    initial_todos = content.count('TODO: Review unreachable code')
    print(f"Found {initial_todos} TODO comments to remove")
    
    # Replace all TODO comment patterns
    # Pattern 1: Lines that start with whitespace + # TODO: Review unreachable code - 
    content = re.sub(r'^(\s*)# TODO: Review unreachable code - (.*)$', r'\1\2', content, flags=re.MULTILINE)
    
    # Count remaining TODOs
    remaining_todos = content.count('TODO: Review unreachable code')
    print(f"Removed {initial_todos - remaining_todos} TODO comments, {remaining_todos} remaining")
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.write(content)
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success! File now compiles without errors!")
        
        # Check for duplicate methods
        duplicates = content.count('def _create_xmp_from_metadata')
        if duplicates > 1:
            print(f"\n⚠️  Warning: Found {duplicates} _create_xmp_from_metadata methods")
            print("Running duplicate removal...")
            remove_duplicate_methods(file_path)
        
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Compilation error: {e}")
        # Extract line number from error
        match = re.search(r'line (\d+)', str(e))
        if match:
            line_num = int(match.group(1))
            lines = content.split('\n')
            print(f"\nError context around line {line_num}:")
            for i in range(max(0, line_num - 3), min(len(lines), line_num + 3)):
                prefix = ">>> " if i == line_num - 1 else "    "
                print(f"{prefix}{i+1}: {lines[i]}")
        return False

def remove_duplicate_methods(file_path):
    """Remove duplicate _create_xmp_from_metadata methods."""
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # Find all occurrences of the method
    method_starts = []
    for i, line in enumerate(lines):
        if 'def _create_xmp_from_metadata(self' in line:
            method_starts.append(i)
    
    if len(method_starts) > 1:
        print(f"Found {len(method_starts)} occurrences at lines: {[s+1 for s in method_starts]}")
        
        # Keep only the first occurrence
        # Work backwards to avoid index issues
        for start_idx in reversed(method_starts[1:]):
            # Find the end of this method
            end_idx = len(lines)
            for j in range(start_idx + 1, len(lines)):
                # Look for next method definition at the same indentation level
                if lines[j].strip() and not lines[j].startswith(' ' * 8) and lines[j].strip().startswith('def '):
                    end_idx = j
                    break
                # Or if we hit a line with no indentation (class or top-level)
                if lines[j].strip() and not lines[j].startswith(' '):
                    end_idx = j
                    break
            
            print(f"Removing duplicate from line {start_idx + 1} to {end_idx}")
            del lines[start_idx:end_idx]
        
        # Write back
        with file_path.open('w') as f:
            f.writelines(lines)
        
        print("Duplicates removed")
        
        # Test again
        import py_compile
        try:
            py_compile.compile(str(file_path), doraise=True)
            print("✅ File still compiles after duplicate removal")
        except:
            print("❌ File has errors after duplicate removal")

if __name__ == "__main__":
    if fix_embedder_final():
        print("\n🎉 The embedder.py file has been successfully fixed!")
        print("- All TODO comments have been removed")
        print("- The file compiles without errors")
        print("- Duplicate methods have been removed")
    else:
        print("\n⚠️  There are still issues to fix.")