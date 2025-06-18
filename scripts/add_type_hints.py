#!/usr/bin/env python3
"""Add type hints to improve mypy compliance."""

import ast
import os
from pathlib import Path
from typing import List, Set


def find_classes_and_methods(file_path: Path) -> dict:
    """Find all classes and their methods in a file."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                attributes = set()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                        # Look for self attributes
                        for n in ast.walk(item):
                            if isinstance(n, ast.Attribute) and \
                               isinstance(n.value, ast.Name) and \
                               n.value.id == 'self':
                                attributes.add(n.attr)
                
                classes[node.name] = {
                    'methods': methods,
                    'attributes': attributes,
                    'lineno': node.lineno
                }
        
        return classes
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {}


def add_protocol_imports(content: str) -> str:
    """Add Protocol import if not present."""
    lines = content.split('\n')
    
    # Check if Protocol is already imported
    for line in lines:
        if 'from typing import' in line and 'Protocol' in line:
            return content
    
    # Find where to add the import
    import_added = False
    for i, line in enumerate(lines):
        if line.startswith('from typing import'):
            # Add Protocol to existing typing import
            if 'Protocol' not in line:
                lines[i] = line.rstrip() + ', Protocol'
            import_added = True
            break
    
    if not import_added:
        # Add new typing import after other imports
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                continue
            elif i > 0 and lines[i-1].startswith(('import ', 'from ')):
                lines.insert(i, 'from typing import Protocol')
                break
    
    return '\n'.join(lines)


def create_mixin_protocol(mixin_name: str, expected_attrs: Set[str]) -> str:
    """Create a Protocol class for mixin expectations."""
    attrs_str = '\n    '.join(f'{attr}: Any' for attr in sorted(expected_attrs))
    return f"""

class {mixin_name}Protocol(Protocol):
    \"\"\"Protocol defining expected attributes for {mixin_name}.\"\"\"
    {attrs_str}
"""


def process_mixin_file(file_path: Path) -> bool:
    """Process a file containing mixins to add type hints."""
    try:
        content = file_path.read_text()
        classes = find_classes_and_methods(file_path)
        
        modified = False
        protocols_to_add = []
        
        for class_name, class_info in classes.items():
            if 'Mixin' in class_name:
                # Find attributes used but not defined
                undefined_attrs = set()
                for attr in class_info['attributes']:
                    # Check if attribute is defined in __init__ or as class variable
                    if attr not in ['__class__', '__dict__', '__module__']:
                        # Simple heuristic: if it's used in methods but not in __init__
                        if '__init__' not in class_info['methods'] or \
                           attr in ['stats', 'config', 'organizer', 'search_db', 
                                   'metadata_cache', 'selection_service', 'project_service',
                                   'understanding_provider', 'search_handler']:
                            undefined_attrs.add(attr)
                
                if undefined_attrs:
                    protocol_name = f"{class_name}Protocol"
                    protocol_code = create_mixin_protocol(class_name, undefined_attrs)
                    protocols_to_add.append(protocol_code)
                    
                    # Update class definition to inherit from Protocol
                    old_class_def = f"class {class_name}:"
                    new_class_def = f"class {class_name}({protocol_name}):"
                    if old_class_def in content:
                        content = content.replace(old_class_def, new_class_def)
                        modified = True
        
        if protocols_to_add:
            # Add Protocol import
            content = add_protocol_imports(content)
            
            # Add Any import if needed
            if 'from typing import' in content and 'Any' not in content:
                content = content.replace('from typing import', 'from typing import Any,')
            
            # Find where to insert protocols (after imports)
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith(('import ', 'from ')):
                    insert_pos = i + 1
                elif insert_pos > 0 and line and not line.startswith(('import ', 'from ')):
                    break
            
            # Insert protocols
            for protocol in protocols_to_add:
                lines.insert(insert_pos, protocol)
                insert_pos += 1
            
            content = '\n'.join(lines)
            modified = True
        
        if modified:
            file_path.write_text(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Add type hints to mixin classes."""
    project_root = Path(__file__).parent.parent
    alicemultiverse_dir = project_root / "alicemultiverse"
    
    fixed_count = 0
    
    # Find all Python files with mixins
    for py_file in alicemultiverse_dir.rglob("*.py"):
        try:
            content = py_file.read_text()
            if 'class ' in content and 'Mixin' in content:
                if process_mixin_file(py_file):
                    print(f"Added type hints to: {py_file.relative_to(project_root)}")
                    fixed_count += 1
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    print(f"\nTotal files updated: {fixed_count}")


if __name__ == "__main__":
    main()