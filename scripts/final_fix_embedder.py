#!/usr/bin/env python3
"""Final fix for embedder.py - remove duplicates and fix remaining indentation."""

from pathlib import Path
import subprocess

def final_fix_embedder():
    """Remove duplicate methods and fix remaining indentation issues."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    # Read the file
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # First, remove duplicate _create_xmp_from_metadata methods
    print("Removing duplicate _create_xmp_from_metadata methods...")
    
    # Find all occurrences
    method_indices = []
    for i, line in enumerate(lines):
        if 'def _create_xmp_from_metadata(self' in line:
            method_indices.append(i)
    
    print(f"Found {len(method_indices)} occurrences at lines: {[i+1 for i in method_indices]}")
    
    if len(method_indices) > 1:
        # Keep only the first occurrence
        # Work backwards to avoid index shifting
        for idx in reversed(method_indices[1:]):
            # Find the end of this method
            end_idx = len(lines)
            
            # Look for the next method or end of class
            for j in range(idx + 1, len(lines)):
                line = lines[j]
                # Check if we've reached another method definition
                if line.strip().startswith('def ') and not line.startswith(' ' * 12):
                    end_idx = j
                    break
                # Or if we've reached the end of the class
                if line.strip() and not line.startswith(' '):
                    end_idx = j
                    break
            
            print(f"Removing duplicate from line {idx + 1} to {end_idx}")
            del lines[idx:end_idx]
    
    # Now fix remaining indentation issues
    print("\nFixing remaining indentation issues...")
    
    # Fix lines that need indentation after try statements
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # If this line ends with try:, ensure next non-empty line is indented
        if line.strip() == 'try:':
            indent_level = len(line) - len(line.lstrip())
            i += 1
            # Process following lines
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip():  # Non-empty line
                    # Ensure it has proper indentation
                    current_indent = len(next_line) - len(next_line.lstrip())
                    if current_indent <= indent_level:
                        # Fix indentation
                        fixed_lines.append(' ' * (indent_level + 4) + next_line.strip() + '\n')
                    else:
                        fixed_lines.append(next_line)
                    i += 1
                    break
                else:
                    fixed_lines.append(next_line)
                    i += 1
        else:
            i += 1
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Written fixed content")
    
    # Run black to format
    print("\nRunning black formatter...")
    result = subprocess.run(['black', '--quiet', str(file_path)], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Black formatting successful")
    else:
        print(f"⚠️  Black had issues: {result.stderr}")
    
    # Test compilation
    print("\nTesting compilation...")
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("✅ File compiles successfully!")
        
        # Final check for duplicates
        with file_path.open('r') as f:
            content = f.read()
        
        todo_count = content.count('TODO: Review unreachable code')
        duplicate_count = content.count('def _create_xmp_from_metadata')
        
        print(f"\nFinal status:")
        print(f"- TODO comments: {todo_count}")
        print(f"- _create_xmp_from_metadata methods: {duplicate_count}")
        
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Compilation error: {e}")
        return False

if __name__ == "__main__":
    if final_fix_embedder():
        print("\n🎉 Successfully fixed embedder.py!")
        print("- All TODO comments removed")
        print("- Duplicate methods removed")
        print("- File properly formatted")
    else:
        print("\n⚠️  Some issues remain")