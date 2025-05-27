#!/usr/bin/env python3
"""Script to organize root directory files."""

import os
import shutil
from pathlib import Path

def main():
    """Organize root directory files into appropriate folders."""
    root = Path.cwd()
    
    # Create directories if needed
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    archive_dir = root / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    # Files to move to scripts/
    scripts_to_move = [
        "api_key_manager.py",
        "cleanup_empty_metadata.py",
        "cleanup_old_files.sh",
        "migrate_metadata.py",
        "organizer.py",
        "quality_organizer_integration.py",
        "quality_pipeline.py",
        "remove_duplicates.py",
        "remove_old_metadata.py",
        "setup_api_keys.sh",
        "alice.py",  # Entry point script
    ]
    
    # Test files to move to tests/
    test_files_to_move = [
        "test_4_variants.py",
        "test_brisque_claude.py",
        "test_claude_real.py",
        "test_enhanced_organizer.py",
        "test_metadata_system.py",
        "test_omegaconf.py",
        "test_pipeline_dict.py",
        "test_project_structure.py",
    ]
    
    # Example files already in examples/
    example_files_to_move = [
        "example_ai_interaction.py",
        "example_enhanced_usage.py",
    ]
    
    # Files to archive (old versions, summaries)
    files_to_archive = [
        "API_KEYS 2.md",
        "CLAUDE 2.md",
        "CLEANUP_SUMMARY.md",
        "REFACTORING_SUMMARY.md",
        "ROOT_FILES_CLEANUP.md",
        "requirements 2.txt",
    ]
    
    # Files to delete (generated files)
    files_to_delete = [
        "coverage.xml",
        ".coverage",
    ]
    
    # Directories to delete
    dirs_to_delete = [
        "htmlcov",
        "alicemultiverse.egg-info",
        ".pytest_cache",
        "__pycache__",
    ]
    
    print("Organizing root directory...")
    
    # Move scripts
    for script in scripts_to_move:
        src = root / script
        if src.exists():
            dst = scripts_dir / script
            print(f"Moving {script} to scripts/")
            shutil.move(str(src), str(dst))
    
    # Move test files
    for test_file in test_files_to_move:
        src = root / test_file
        if src.exists():
            dst = root / "tests" / test_file
            print(f"Moving {test_file} to tests/")
            shutil.move(str(src), str(dst))
    
    # Move example files
    for example_file in example_files_to_move:
        src = root / example_file
        if src.exists():
            dst = root / "examples" / example_file
            print(f"Moving {example_file} to examples/")
            shutil.move(str(src), str(dst))
    
    # Archive old files
    for archive_file in files_to_archive:
        src = root / archive_file
        if src.exists():
            dst = archive_dir / archive_file
            print(f"Archiving {archive_file}")
            shutil.move(str(src), str(dst))
    
    # Delete generated files
    for file_to_delete in files_to_delete:
        file_path = root / file_to_delete
        if file_path.exists():
            print(f"Deleting {file_to_delete}")
            file_path.unlink()
    
    # Delete generated directories
    for dir_to_delete in dirs_to_delete:
        dir_path = root / dir_to_delete
        if dir_path.exists():
            print(f"Deleting {dir_to_delete}/")
            shutil.rmtree(dir_path)
    
    # Also clean up any __pycache__ directories recursively
    for pycache in root.rglob("__pycache__"):
        print(f"Deleting {pycache.relative_to(root)}")
        shutil.rmtree(pycache)
    
    print("\nRoot directory cleaned up!")
    print("\nRemaining files in root (these should stay):")
    expected_root_files = {
        "README.md", "LICENSE", "pyproject.toml",
        "requirements.txt", "requirements-dev.txt", "requirements-docs.txt",
        "MANIFEST.in", "pytest.ini", "mkdocs.yml", "settings.yaml",
        ".gitignore", "CHANGELOG.md", "CONTRIBUTING.md",
        # Documentation files
        "API_KEYS.md", "CLAUDE.md", "INSTALLATION.md", "CONFIGURATION.md",
        "AliceMultiverse-Spec.md", "CLAUDE_DESKTOP_SETUP.md",
        "DOCUMENTATION_OVERVIEW.md", "FORMAT_SUPPORT.md",
        "pipeline_config_example.json",
    }
    
    for item in sorted(root.iterdir()):
        if item.is_file() and item.name not in expected_root_files:
            print(f"  - {item.name} (unexpected)")
        elif item.is_file():
            print(f"  - {item.name}")

if __name__ == "__main__":
    main()