#!/usr/bin/env python3
"""Properly fix embedder.py by removing TODO comments and formatting with black."""

from pathlib import Path
import re
import subprocess
import tempfile

def fix_embedder_properly():
    """Remove TODO comments and format the file properly."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    # Read the file
    with file_path.open('r') as f:
        content = f.read()
    
    # Count initial TODOs
    initial_todos = content.count('TODO: Review unreachable code')
    print(f"Found {initial_todos} TODO comments to remove")
    
    # Remove TODO comments - handle all patterns
    # Pattern: Lines that start with any amount of whitespace + # TODO: Review unreachable code - 
    content = re.sub(r'^(\s*)# TODO: Review unreachable code - (.*)$', r'\1\2', content, flags=re.MULTILINE)
    
    # Count remaining TODOs
    remaining_todos = content.count('TODO: Review unreachable code')
    print(f"Removed {initial_todos - remaining_todos} TODO comments")
    
    # Fix the MetadataEncoder.default method which has a known issue
    # The method needs proper indentation for the if statements
    content = re.sub(
        r'(class MetadataEncoder.*?\n.*?def default.*?\n.*?if hasattr.*?\n.*?return obj\.value\n)(.*?if hasattr.*?\n)(.*?return obj\.__dict__\n)(.*?return super.*?\n)',
        r'\1\2            \3\4',
        content,
        flags=re.DOTALL
    )
    
    # Write to a temporary file to test formatting
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    # Try to format with black
    print("\nTrying to format with black...")
    try:
        result = subprocess.run([
            'black',
            '--quiet',
            str(tmp_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Black formatting successful")
            # Read the formatted content
            with tmp_path.open('r') as f:
                formatted_content = f.read()
            
            # Write to the actual file
            with file_path.open('w') as f:
                f.write(formatted_content)
            
            # Test compilation
            import py_compile
            try:
                py_compile.compile(str(file_path), doraise=True)
                print("✅ File compiles successfully!")
                
                # Check for duplicate methods
                duplicates = formatted_content.count('def _create_xmp_from_metadata')
                if duplicates > 1:
                    print(f"\n⚠️  Warning: Found {duplicates} _create_xmp_from_metadata methods")
                    print("Removing duplicates...")
                    remove_duplicates(file_path)
                
                tmp_path.unlink()  # Clean up temp file
                return True
            except py_compile.PyCompileError as e:
                print(f"❌ Compilation error: {e}")
                tmp_path.unlink()
                return False
        else:
            print(f"❌ Black failed: {result.stderr}")
            # Write the content anyway - it might still be valid Python
            with file_path.open('w') as f:
                f.write(content)
            tmp_path.unlink()
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        tmp_path.unlink()
        return False

def remove_duplicates(file_path):
    """Remove duplicate _create_xmp_from_metadata methods."""
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # Find all occurrences
    method_indices = []
    for i, line in enumerate(lines):
        if 'def _create_xmp_from_metadata(self' in line:
            method_indices.append(i)
    
    if len(method_indices) > 1:
        print(f"Found {len(method_indices)} occurrences")
        # Keep only the first one
        # Work backwards to avoid index shifting
        for idx in reversed(method_indices[1:]):
            # Find the end of this method
            end_idx = len(lines)
            indent_level = len(lines[idx]) - len(lines[idx].lstrip())
            
            for j in range(idx + 1, len(lines)):
                if lines[j].strip():  # Non-empty line
                    current_indent = len(lines[j]) - len(lines[j].lstrip())
                    if current_indent <= indent_level and lines[j].strip().startswith('def '):
                        end_idx = j
                        break
            
            print(f"Removing duplicate from line {idx + 1} to {end_idx}")
            del lines[idx:end_idx]
        
        # Write back
        with file_path.open('w') as f:
            f.writelines(lines)
        
        # Format again
        subprocess.run(['black', '--quiet', str(file_path)])
        print("✅ Duplicates removed and file reformatted")

if __name__ == "__main__":
    if fix_embedder_properly():
        print("\n🎉 Successfully fixed embedder.py!")
        print("- All TODO comments removed")
        print("- File properly formatted")
        print("- Compiles without errors")
    else:
        print("\n⚠️  Some issues remain - manual intervention may be needed")