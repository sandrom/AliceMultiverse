#!/usr/bin/env python3
"""Fix indentation issues in Python files caused by UNREACHABLE comment removal."""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_indentation_after_definition(content: str) -> str:
    """Fix missing indentation after function/class definitions with docstrings."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if this is a function or class definition
        if re.match(r'^(def |class |async def )', line.lstrip()) and line.rstrip().endswith(':'):
            # Look ahead for docstring
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Check if next line is at the same indentation level (wrong) and starts with quotes
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())
                
                if next_indent == current_indent and next_line.lstrip().startswith(('"""', "'''")):
                    # Fix: indent the docstring and everything until the closing quotes
                    i += 1
                    indent_str = ' ' * (current_indent + 4)
                    
                    # Handle single-line docstring
                    if next_line.lstrip().count('"""') >= 2 or next_line.lstrip().count("'''") >= 2:
                        fixed_lines.append(indent_str + next_line.lstrip())
                    else:
                        # Multi-line docstring
                        quote_type = '"""' if '"""' in next_line else "'''"
                        fixed_lines.append(indent_str + next_line.lstrip())
                        i += 1
                        
                        # Continue until we find the closing quotes
                        while i < len(lines):
                            line = lines[i]
                            if quote_type in line:
                                fixed_lines.append(indent_str + line.lstrip())
                                break
                            else:
                                fixed_lines.append(indent_str + line.lstrip())
                            i += 1
        
        i += 1
    
    return '\n'.join(fixed_lines)


def fix_indentation_after_conditionals(content: str) -> str:
    """Fix missing indentation after if/try/except/else/elif/finally/with/for/while."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if this line ends with a colon (control structure)
        if line.rstrip().endswith(':') and any(line.lstrip().startswith(keyword) for keyword in 
                                                ['if ', 'elif ', 'else:', 'try:', 'except', 'finally:', 
                                                 'with ', 'for ', 'while ', 'match ', 'case ']):
            # Check if next line has wrong indentation
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line is not indented more than current line, fix it
                if next_line.strip() and next_indent <= current_indent:
                    i += 1
                    indent_str = ' ' * (current_indent + 4)
                    fixed_lines.append(indent_str + next_line.lstrip())
                    continue
        
        i += 1
    
    return '\n'.join(fixed_lines)


def fix_multiline_strings(content: str) -> str:
    """Fix unterminated triple-quoted strings."""
    # Pattern to find triple quotes that might be missing their closing pair
    lines = content.split('\n')
    in_triple_quote = False
    quote_type = None
    fixed_lines = []
    
    for i, line in enumerate(lines):
        if not in_triple_quote:
            # Check if we're starting a triple quote
            if '"""' in line:
                count = line.count('"""')
                if count % 2 == 1:  # Odd number means unclosed
                    in_triple_quote = True
                    quote_type = '"""'
            elif "'''" in line:
                count = line.count("'''")
                if count % 2 == 1:  # Odd number means unclosed
                    in_triple_quote = True
                    quote_type = "'''"
        else:
            # We're in a triple quote, check if it ends
            if quote_type in line:
                in_triple_quote = False
                quote_type = None
        
        fixed_lines.append(line)
    
    # If we ended while still in a triple quote, add the closing quotes
    if in_triple_quote and quote_type:
        fixed_lines.append(quote_type)
    
    return '\n'.join(fixed_lines)


def fix_file(filepath: Path) -> Tuple[bool, str]:
    """Fix indentation issues in a Python file.
    
    Returns:
        (success, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fixes in order
        fixed_content = fix_indentation_after_definition(content)
        fixed_content = fix_indentation_after_conditionals(fixed_content)
        fixed_content = fix_multiline_strings(fixed_content)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        return True, ""
    except Exception as e:
        return False, str(e)


def main():
    """Fix indentation issues in all Python files with problems."""
    # List of files with issues (from the previous scan)
    files_with_issues = [
        "alicemultiverse/assets/hashing.py",
        "alicemultiverse/assets/perceptual_hashing.py",
        "alicemultiverse/assets/video_hashing.py",
        "alicemultiverse/cli/main.py",
        "alicemultiverse/cli_entry.py",
        "alicemultiverse/comparison/populate.py",
        "alicemultiverse/comparison/web_server.py",
        "alicemultiverse/core/config_loader.py",
        "alicemultiverse/core/config_validation.py",
        "alicemultiverse/core/error_recovery.py",
        "alicemultiverse/core/file_operations.py",
        "alicemultiverse/core/first_run.py",
        "alicemultiverse/core/keys/cli.py",
        "alicemultiverse/core/memory_optimization.py",
        "alicemultiverse/core/metrics.py",
        "alicemultiverse/core/startup_validation.py",
        "alicemultiverse/core/structured_logging.py",
        "alicemultiverse/core/unified_cache.py",
        "alicemultiverse/core/validation.py",
        "alicemultiverse/events/file_events.py",
        "alicemultiverse/events/workflow_events.py",
        "alicemultiverse/interface/alice_api.py",
        "alicemultiverse/interface/analytics_mcp.py",
        "alicemultiverse/interface/broll_suggestions_mcp.py",
        "alicemultiverse/interface/cli_handlers.py",
        "alicemultiverse/interface/cli_parser.py",
        "alicemultiverse/interface/creative_models.py",
        "alicemultiverse/interface/image_presentation_mcp.py",
        "alicemultiverse/interface/main_cli.py",
        "alicemultiverse/interface/multi_version_export_mcp.py",
        "alicemultiverse/interface/simple_cli.py",
        "alicemultiverse/interface/timeline_nlp_mcp.py",
        "alicemultiverse/interface/timeline_preview_mcp.py",
        "alicemultiverse/interface/validation/request_validators.py",
        "alicemultiverse/interface/variation_mcp.py",
        "alicemultiverse/interface/video_providers_mcp.py",
        "alicemultiverse/mcp/base.py",
        "alicemultiverse/mcp/server.py",
        "alicemultiverse/mcp/utils/formatters.py",
        "alicemultiverse/memory/style_memory_mcp.py",
        "alicemultiverse/monitoring/dashboard.py",
        "alicemultiverse/monitoring/tracker.py",
        "alicemultiverse/organizer/organization_helpers.py",
        "alicemultiverse/prompts/hooks.py",
        "alicemultiverse/prompts/project_storage.py",
        "alicemultiverse/selections/models.py",
        "alicemultiverse/storage/unified_duckdb.py",
        "alicemultiverse/understanding/custom_instructions.py",
        "alicemultiverse/understanding/providers.py",
        "alicemultiverse/workflows/base.py",
        "alicemultiverse/workflows/composition/flow_analyzer.py",
        "alicemultiverse/workflows/multi_version_export.py",
        "alicemultiverse/workflows/templates/image_enhancement.py",
        "alicemultiverse/workflows/templates/music_video.py",
        "alicemultiverse/workflows/templates/social_media.py",
        "alicemultiverse/workflows/templates/style_transfer.py",
        "alicemultiverse/workflows/templates/template_mcp.py",
        "alicemultiverse/workflows/templates/video_pipeline.py",
        "alicemultiverse/workflows/transitions/color_flow.py",
        "alicemultiverse/workflows/transitions/match_cuts.py",
        "alicemultiverse/workflows/transitions/morphing.py",
        "alicemultiverse/workflows/variations/variation_tracker.py",
        "alicemultiverse/workflows/video_export.py",
        "tests/integration/test_elevenlabs_integration.py",
        "tests/unit/test_providers.py"
    ]
    
    root_dir = Path(__file__).parent.parent
    
    print(f"Fixing indentation in {len(files_with_issues)} files...")
    print()
    
    success_count = 0
    failed = []
    
    for relative_path in files_with_issues:
        filepath = root_dir / relative_path
        if not filepath.exists():
            print(f"  ❌ {relative_path} - File not found")
            continue
            
        success, error = fix_file(filepath)
        if success:
            print(f"  ✓ {relative_path}")
            success_count += 1
        else:
            print(f"  ❌ {relative_path} - {error}")
            failed.append((relative_path, error))
    
    print()
    print(f"Successfully fixed: {success_count}/{len(files_with_issues)} files")
    
    if failed:
        print("\nFailed to fix:")
        for path, error in failed:
            print(f"  {path}: {error}")
    
    return 0 if success_count == len(files_with_issues) else 1


if __name__ == "__main__":
    sys.exit(main())