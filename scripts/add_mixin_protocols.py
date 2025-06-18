#!/usr/bin/env python3
"""Add Protocol type hints to mixin classes."""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Map mixin names to required attributes
MIXIN_ATTRIBUTES = {
    "StatisticsMixin": ["stats"],
    "ProcessFileMixin": ["metadata_cache", "config", "stats"],
    "FileOperationsMixin": ["config", "stats"],
    "OrganizationLogicMixin": ["config", "stats"],
    "MediaAnalysisMixin": ["config"],
    "SearchOperationsMixin": ["search_handler", "organizer"],
    "WatchModeMixin": ["config", "organizer"],
    "SelectionOperationsMixin": ["selection_service", "project_service"],
    "AnalysisMixin": ["search_db"],
    "PromptGenerationMixin": ["understanding_provider"],
    "KlingIntegrationMixin": ["understanding_provider"],
    "ExportMixin": ["search_db"],
}

# Protocol imports for each attribute
ATTRIBUTE_PROTOCOLS = {
    "stats": "HasStats",
    "config": "HasConfig", 
    "metadata_cache": "HasMetadataCache",
    "search_handler": "HasSearchHandler",
    "organizer": "HasOrganizer",
    "selection_service": "HasSelectionService",
    "project_service": "HasProjectService",
    "understanding_provider": "HasUnderstandingProvider",
    "search_db": "HasSearchDB",
}


def add_protocol_to_mixin(file_path: Path, mixin_name: str, attributes: List[str]) -> bool:
    """Add protocol type hints to a mixin class."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Check if TYPE_CHECKING is imported
        if "TYPE_CHECKING" not in content:
            # Add TYPE_CHECKING import
            if "from typing import" in content:
                content = re.sub(
                    r'(from typing import .*)',
                    r'\1, TYPE_CHECKING',
                    content,
                    count=1
                )
            else:
                # Add typing import after other imports
                import_pos = content.find('\n\n')
                if import_pos > 0:
                    content = content[:import_pos] + "\nfrom typing import TYPE_CHECKING" + content[import_pos:]
        
        # Add protocol imports if needed
        protocols_needed = set(ATTRIBUTE_PROTOCOLS[attr] for attr in attributes if attr in ATTRIBUTE_PROTOCOLS)
        if protocols_needed and "from ...core.protocols import" not in content:
            # Find where to add the import
            type_checking_match = re.search(r'if TYPE_CHECKING:.*?\n\n', content, re.DOTALL)
            if not type_checking_match:
                # Add TYPE_CHECKING block
                import_section_end = content.rfind('\n\n', 0, content.find(f'class {mixin_name}'))
                if import_section_end > 0:
                    protocols_import = f"\n\nif TYPE_CHECKING:\n    from ...core.protocols import {', '.join(sorted(protocols_needed))}"
                    content = content[:import_section_end] + protocols_import + content[import_section_end:]
            else:
                # Add to existing TYPE_CHECKING block
                insert_pos = type_checking_match.end() - 2
                protocols_import = f"    from ...core.protocols import {', '.join(sorted(protocols_needed))}\n"
                content = content[:insert_pos] + protocols_import + content[insert_pos:]
        
        # Add type annotations to the class
        class_match = re.search(rf'class {mixin_name}.*?:\n(    """.*?""")?', content, re.DOTALL)
        if class_match:
            # Check if attributes are already annotated
            class_body_start = class_match.end()
            next_method = content.find('\n    def ', class_body_start)
            if next_method == -1:
                next_method = len(content)
            
            existing_annotations = content[class_body_start:next_method]
            
            # Add TYPE_CHECKING block with annotations
            if "if TYPE_CHECKING:" not in existing_annotations:
                annotations = "\n\n    if TYPE_CHECKING:\n        # Type hints for mypy\n"
                for attr in attributes:
                    if attr == "stats":
                        annotations += f"        {attr}: Statistics\n"
                    elif attr == "config":
                        annotations += f"        {attr}: Config\n"
                    else:
                        annotations += f"        {attr}: Any\n"
                
                content = content[:class_match.end()] + annotations + content[class_match.end():]
                
                # Also need to add imports for Statistics and Config if used
                if "stats" in attributes and "from ...core.types import" in content:
                    if "Statistics" not in content:
                        content = re.sub(
                            r'(from \.\.\.core\.types import .*)',
                            lambda m: m.group(1) + ', Statistics' if ', Statistics' not in m.group(1) else m.group(1),
                            content,
                            count=1
                        )
                
                if "config" in attributes and "from ...core.config import Config" not in content:
                    # Add Config import
                    import_pos = content.find("from ...core.")
                    if import_pos > 0:
                        line_end = content.find('\n', import_pos)
                        content = content[:line_end+1] + "from ...core.config import Config\n" + content[line_end+1:]
        
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Add Protocol type hints to all mixin classes."""
    project_root = Path(__file__).parent.parent
    alicemultiverse_dir = project_root / "alicemultiverse"
    
    fixed_count = 0
    
    # Process each mixin
    for mixin_name, attributes in MIXIN_ATTRIBUTES.items():
        # Find files containing the mixin
        for py_file in alicemultiverse_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                if f"class {mixin_name}" in content:
                    if add_protocol_to_mixin(py_file, mixin_name, attributes):
                        print(f"✅ Updated {mixin_name} in {py_file.relative_to(project_root)}")
                        fixed_count += 1
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
    
    print(f"\n📝 Updated {fixed_count} mixin classes with Protocol type hints")
    
    # Run mypy to check improvements
    print("\n🔍 Checking mypy errors...")
    import subprocess
    result = subprocess.run(
        ["mypy", "alicemultiverse", "--ignore-missing-imports", "--show-error-codes"],
        capture_output=True,
        text=True
    )
    
    error_count = result.stderr.count("error:")
    print(f"\nCurrent mypy errors: {error_count}")
    
    # Show mixin-related errors
    mixin_errors = [line for line in result.stderr.split('\n') if 'has no attribute' in line and 'Mixin' in line]
    if mixin_errors:
        print(f"\nRemaining mixin errors: {len(mixin_errors)}")
        for error in mixin_errors[:5]:
            print(f"  - {error}")


if __name__ == "__main__":
    main()