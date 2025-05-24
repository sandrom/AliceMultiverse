#!/usr/bin/env python3
"""Fix import statements after removing duplicate modules."""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Define import replacements
IMPORT_REPLACEMENTS = [
    # Keys module
    (r'from alicemultiverse\.keys\.', 'from alicemultiverse.core.keys.'),
    (r'import alicemultiverse\.keys\.', 'import alicemultiverse.core.keys.'),
    
    # Utils module - should use core
    (r'from alicemultiverse\.utils\.', 'from alicemultiverse.core.'),
    (r'import alicemultiverse\.utils\.', 'import alicemultiverse.core.'),
    
    # CLI module - should use interface.main_cli
    (r'from alicemultiverse\.cli import main\b', 'from alicemultiverse.interface.main_cli import main'),
    (r'from alicemultiverse\.cli import', 'from alicemultiverse.interface.cli_handler import'),
    
    # File ops - should use alice_utils package
    (r'from alicemultiverse\.core\.file_ops', 'from alice_utils.file_ops'),
    (r'from alicemultiverse\.utils\.file_ops', 'from alice_utils.file_ops'),
]

def fix_imports_in_file(filepath: Path) -> bool:
    """Fix imports in a single file. Returns True if changes were made."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    original_content = content
    
    # Apply all replacements
    for pattern, replacement in IMPORT_REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    
    # Check if changes were made
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    
    return False

def find_python_files(root_dir: Path, exclude_dirs: List[str]) -> List[Path]:
    """Find all Python files in the project, excluding certain directories."""
    python_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove excluded directories from search
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        # Add Python files
        for filename in filenames:
            if filename.endswith('.py'):
                python_files.append(Path(dirpath) / filename)
    
    return python_files

def main():
    """Main function to fix all imports."""
    root_dir = Path(__file__).parent.parent
    exclude_dirs = ['.venv', '__pycache__', 'build', 'dist', '.git', 'venv']
    
    print("🔍 Finding Python files...")
    python_files = find_python_files(root_dir, exclude_dirs)
    print(f"Found {len(python_files)} Python files")
    
    print("\n🔧 Fixing imports...")
    fixed_files = []
    
    for filepath in python_files:
        if fix_imports_in_file(filepath):
            fixed_files.append(filepath)
            print(f"✅ Fixed: {filepath.relative_to(root_dir)}")
    
    print(f"\n📊 Summary:")
    print(f"  Total files scanned: {len(python_files)}")
    print(f"  Files with fixed imports: {len(fixed_files)}")
    
    if fixed_files:
        print("\n📝 Files that were modified:")
        for filepath in fixed_files:
            print(f"  - {filepath.relative_to(root_dir)}")
    
    print("\n✨ Import fixing complete!")
    print("\n⚠️  Remember to:")
    print("  1. Remove duplicate directories manually")
    print("  2. Run tests to verify imports work correctly")
    print("  3. Update CLAUDE.md to remove old script references")

if __name__ == "__main__":
    main()