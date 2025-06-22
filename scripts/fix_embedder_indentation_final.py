#!/usr/bin/env python3
"""Fix the remaining indentation issues in embedder.py."""

from pathlib import Path

def fix_indentation_issues():
    """Fix specific indentation issues in the file."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # Fix specific known indentation issues
    fixes_needed = [
        # Line 46: return obj.__dict__ needs indent
        (46, "        return obj.__dict__", "            return obj.__dict__"),
        # Line 47: return super().default(obj) needs dedent
        (47, "        return super().default(obj)", "        return super().default(obj)"),
        # Lines after elif statements
        (89, "            return self._embed_jpeg_metadata(image_path, metadata)", "                return self._embed_jpeg_metadata(image_path, metadata)"),
        (91, "            return self._embed_webp_metadata(image_path, metadata)", "                return self._embed_webp_metadata(image_path, metadata)"),
        (93, "            return self._embed_heic_metadata(image_path, metadata)", "                return self._embed_heic_metadata(image_path, metadata)"),
        (95, "            # Should not happen with our restricted format support", "                # Should not happen with our restricted format support"),
        (96, "            logger.error(f\"Unexpected format: {suffix}\")", "                logger.error(f\"Unexpected format: {suffix}\")"),
        (97, "            return False", "                return False"),
    ]
    
    # Apply fixes
    for line_num, old_content, new_content in fixes_needed:
        # Adjust for 0-based indexing
        idx = line_num - 1
        if idx < len(lines) and lines[idx].rstrip() == old_content:
            lines[idx] = new_content + '\n'
            print(f"Fixed line {line_num}: {old_content.strip()}")
        else:
            print(f"Warning: Line {line_num} doesn't match expected content")
            if idx < len(lines):
                print(f"  Expected: {old_content}")
                print(f"  Found: {lines[idx].rstrip()}")
    
    # Fix all lines that are missing indentation after method definitions
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # If this is a method definition
        if line.strip().startswith('def ') and line.strip().endswith(':'):
            # Check if next line is a docstring that's not indented
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip().startswith('"""') and not next_line.startswith(' '):
                    # Get the indentation of the def line
                    def_indent = len(line) - len(line.lstrip())
                    # Fix the docstring line
                    lines[i + 1] = ' ' * (def_indent + 4) + next_line.strip() + '\n'
                    print(f"Fixed docstring indentation at line {i + 2}")
        
        # Check for lines after colons that need indentation
        if line.strip().endswith(':') and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Skip if it's already indented or empty
            if next_line.strip() and not next_line[0].isspace():
                # Get the indentation of the current line
                current_indent = len(line) - len(line.lstrip())
                # Fix the next line
                lines[i + 1] = ' ' * (current_indent + 4) + next_line.strip() + '\n'
                print(f"Fixed indentation after colon at line {i + 2}")
        
        i += 1
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(lines)
    
    print("\nWrote fixed content to file")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success! File now compiles without errors!")
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Still has compilation error: {e}")
        return False

if __name__ == "__main__":
    fix_indentation_issues()