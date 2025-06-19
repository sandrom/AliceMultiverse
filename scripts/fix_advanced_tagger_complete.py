#!/usr/bin/env python3
"""Completely fix advanced_tagger.py by removing UNREACHABLE and fixing indentation."""

import re

# Read the file
with open('alicemultiverse/understanding/advanced_tagger.py', 'r') as f:
    content = f.read()

# Remove all UNREACHABLE comments
content = re.sub(r'^\s*#\s*UNREACHABLE:\s*', '', content, flags=re.MULTILINE)

# Now fix the specific indentation issues
lines = content.split('\n')
fixed_lines = []

i = 0
while i < len(lines):
    line = lines[i]
    
    # Special handling for the known problem areas
    if i == 212 and line.strip().startswith('def __init__'):
        # This is inside ProjectTagVocabulary class
        fixed_lines.append('    def __init__(self, project_id: str, repository: Any):')
        i += 1
        # Fix the docstring and body
        while i < len(lines) and (lines[i].strip().startswith('"""') or lines[i].strip().startswith('Args:') or 
                                  'project_id:' in lines[i] or 'repository:' in lines[i] or 
                                  lines[i].strip() == '' or lines[i].strip().endswith('"""')):
            if lines[i].strip():
                fixed_lines.append('        ' + lines[i].strip())
            else:
                fixed_lines.append('')
            i += 1
        # Now handle the body
        while i < len(lines) and not lines[i].strip().startswith('def ') and lines[i].strip():
            fixed_lines.append('        ' + lines[i].strip())
            i += 1
    elif i == 224 and line.strip().startswith('def _load_project_tags'):
        # Still inside ProjectTagVocabulary
        fixed_lines.append('    def _load_project_tags(self):')
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('def '):
            if lines[i].strip():
                fixed_lines.append('        ' + lines[i].strip())
            else:
                fixed_lines.append('')
            i += 1
    elif i == 230 and line.strip().startswith('def add_custom_tag'):
        # Still inside ProjectTagVocabulary
        fixed_lines.append('    def add_custom_tag(self, category: str, tag: str):')
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('def ') and not lines[i].strip().startswith('class '):
            if lines[i].strip():
                fixed_lines.append('        ' + lines[i].strip())
            else:
                fixed_lines.append('')
            i += 1
    elif i > 234 and i < 283 and line.strip().startswith('def '):
        # Other methods in ProjectTagVocabulary
        fixed_lines.append('    ' + line.strip())
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('def ') and not lines[i].strip().startswith('class '):
            if lines[i].strip():
                # Check if it's inside a nested structure
                if 'for ' in lines[i] or 'if ' in lines[i]:
                    fixed_lines.append('        ' + lines[i].strip())
                    # Handle nested content
                    i += 1
                    while i < len(lines) and lines[i].startswith('    ') and not lines[i].strip().startswith('def '):
                        if lines[i].strip():
                            fixed_lines.append('            ' + lines[i].strip())
                        else:
                            fixed_lines.append('')
                        i += 1
                    continue
                else:
                    fixed_lines.append('        ' + lines[i].strip())
            else:
                fixed_lines.append('')
            i += 1
    elif i == 288 and line.strip().startswith('def __init__'):
        # This is inside AdvancedTagger class
        fixed_lines.append('    def __init__(self, repository: Any):')
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('def '):
            if lines[i].strip():
                fixed_lines.append('        ' + lines[i].strip())
            else:
                fixed_lines.append('')
            i += 1
    elif i == 297 and line.strip().startswith('def get_project_vocabulary'):
        # Inside AdvancedTagger
        fixed_lines.append('    def get_project_vocabulary(self, project_id: str) -> ProjectTagVocabulary:')
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('def '):
            if lines[i].strip():
                # Check for nested if
                if lines[i].strip().startswith('if '):
                    fixed_lines.append('        ' + lines[i].strip())
                    i += 1
                    # Handle content inside if
                    while i < len(lines) and not lines[i].strip().startswith('return') and not lines[i].strip().startswith('def '):
                        if lines[i].strip():
                            fixed_lines.append('            ' + lines[i].strip())
                        else:
                            fixed_lines.append('')
                        i += 1
                    if i < len(lines) and lines[i].strip().startswith('return'):
                        fixed_lines.append('        ' + lines[i].strip())
                        i += 1
                else:
                    fixed_lines.append('        ' + lines[i].strip())
                    i += 1
            else:
                fixed_lines.append('')
                i += 1
    elif i > 305 and line.strip().startswith('def ') and i < 450:
        # Other AdvancedTagger methods
        fixed_lines.append('    ' + line.strip())
        i += 1
    elif line.strip() and i > 305 and i < 450 and not line.startswith(' '):
        # Lines that should be indented in AdvancedTagger methods
        fixed_lines.append('        ' + line.strip())
        i += 1
    else:
        fixed_lines.append(line)
        i += 1

# Join back and fix any remaining issues
content = '\n'.join(fixed_lines)

# Fix the get_ancestors method properly
content = content.replace(
    """    def get_ancestors(self, category: str, tag: str) -> list[str]:
        \"\"\"Get all ancestors of a tag in the hierarchy.\"\"\"
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []

        ancestors = []
        current = tag
        hierarchy = self.hierarchies[category]

        while current and current in hierarchy:
        parent = hierarchy[current].parent
        if parent:
        ancestors.append(parent)
        current = parent
        else:
        break

        return ancestors""",
    """    def get_ancestors(self, category: str, tag: str) -> list[str]:
        \"\"\"Get all ancestors of a tag in the hierarchy.\"\"\"
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []

        ancestors = []
        current = tag
        hierarchy = self.hierarchies[category]

        while current and current in hierarchy:
            parent = hierarchy[current].parent
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break

        return ancestors"""
)

# Fix the get_descendants method
content = content.replace(
    """    def get_descendants(self, category: str, tag: str) -> list[str]:
        \"\"\"Get all descendants of a tag in the hierarchy.\"\"\"
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []

        descendants = []
        to_process = [tag]
        hierarchy = self.hierarchies[category]

        while to_process:
        current = to_process.pop(0)
        if current in hierarchy:
        children = hierarchy[current].children
        descendants.extend(children)
        to_process.extend(children)

        return descendants""",
    """    def get_descendants(self, category: str, tag: str) -> list[str]:
        \"\"\"Get all descendants of a tag in the hierarchy.\"\"\"
        if category not in self.hierarchies or tag not in self.hierarchies[category]:
            return []

        descendants = []
        to_process = [tag]
        hierarchy = self.hierarchies[category]

        while to_process:
            current = to_process.pop(0)
            if current in hierarchy:
                children = hierarchy[current].children
                descendants.extend(children)
                to_process.extend(children)

        return descendants"""
)

# Write the fixed content
with open('alicemultiverse/understanding/advanced_tagger.py', 'w') as f:
    f.write(content)

print("Fixed advanced_tagger.py completely")