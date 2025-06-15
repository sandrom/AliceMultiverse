#!/usr/bin/env python3
"""Clean up deprecated code and files from the AliceMultiverse project."""

import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent


def cleanup_deprecated_quality_code():
    """Remove deprecated quality assessment code."""
    files_to_remove = [
        # Old quality module in asset-processor
        "services/asset-processor/src/asset_processor/quality.py",
    ]

    for file_path in files_to_remove:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            logger.info(f"Removing deprecated file: {file_path}")
            full_path.unlink()
        else:
            logger.debug(f"File already removed: {file_path}")


def cleanup_old_test_outputs():
    """Clean up test output directories."""
    dirs_to_clean = [
        "test_output",
        "output",  # if empty
        "generated",  # if empty
    ]

    for dir_name in dirs_to_clean:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists():
            # Check if directory is empty or only contains test files
            if dir_name == "test_output":
                logger.info(f"Removing test output directory: {dir_name}")
                shutil.rmtree(dir_path)
            elif not any(dir_path.iterdir()):
                logger.info(f"Removing empty directory: {dir_name}")
                dir_path.rmdir()
            else:
                # Check specific subdirs
                if dir_name == "output":
                    # Keep real output, but could clean test data
                    logger.info(f"Keeping {dir_name} - contains real data")
                elif dir_name == "generated":
                    # Check if it only has .gitkeep
                    files = list(dir_path.iterdir())
                    if len(files) == 1 and files[0].name == ".gitkeep":
                        logger.info(f"Keeping {dir_name} with .gitkeep")
                    elif len(files) == 0:
                        logger.info(f"Removing empty directory: {dir_name}")
                        dir_path.rmdir()


def cleanup_cache_dirs():
    """Clean up cache directories."""
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/.ruff_cache",
    ]

    for pattern in cache_patterns:
        for path in BASE_DIR.glob(pattern):
            if path.is_dir():
                logger.info(f"Removing cache directory: {path.relative_to(BASE_DIR)}")
                shutil.rmtree(path)
            elif path.is_file():
                logger.info(f"Removing cache file: {path.relative_to(BASE_DIR)}")
                path.unlink()


def cleanup_mock_paths():
    """Clean up MagicMock paths."""
    mock_dir = BASE_DIR / "MagicMock/mock.paths.cache_dir"
    if mock_dir.exists():
        logger.info("Cleaning up MagicMock cache directories...")
        for subdir in mock_dir.iterdir():
            if subdir.is_dir() and subdir.name.isdigit():
                logger.info(f"  Removing: {subdir.name}")
                shutil.rmtree(subdir)


def cleanup_old_experiments():
    """Archive old experiment files."""
    # For now, just report what might be archived
    potential_archives = [
        "docs/research/multi-agent-how.md",  # If multi-agent is not in current roadmap
    ]

    for file_path in potential_archives:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            logger.info(f"Consider archiving: {file_path}")


def update_asset_processor_service():
    """Update asset-processor to remove quality references."""
    main_file = BASE_DIR / "services/asset-processor/src/asset_processor/main.py"
    if main_file.exists():
        content = main_file.read_text()
        if "quality" in content.lower():
            logger.info("Asset-processor main.py contains quality references - needs updating")
            # Could automatically update, but safer to do manually


def check_for_deprecated_imports():
    """Check for imports of deprecated modules."""
    deprecated_imports = [
        # These are examples of deprecated imports to check for
        # "from alicemultiverse.quality",
        # "import quality",
        # "from .quality import",
        # "from alicemultiverse.pipeline.stages import QualityStage",
    ]

    logger.info("\nChecking for deprecated imports...")
    found_issues = False

    for py_file in BASE_DIR.rglob("*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue

        try:
            content = py_file.read_text()
            for deprecated in deprecated_imports:
                if deprecated in content:
                    logger.warning(f"Found deprecated import in {py_file.relative_to(BASE_DIR)}: {deprecated}")
                    found_issues = True
        except Exception:
            pass

    if not found_issues:
        logger.info("No deprecated imports found!")


def main():
    """Run all cleanup tasks."""
    logger.info("Starting AliceMultiverse cleanup...")
    logger.info("=" * 60)

    # Clean up deprecated code
    logger.info("\n1. Cleaning up deprecated quality code...")
    cleanup_deprecated_quality_code()

    # Clean up test outputs
    logger.info("\n2. Cleaning up test output directories...")
    cleanup_old_test_outputs()

    # Clean up cache directories
    logger.info("\n3. Cleaning up cache directories...")
    cleanup_cache_dirs()

    # Clean up mock paths
    logger.info("\n4. Cleaning up MagicMock paths...")
    cleanup_mock_paths()

    # Check for things that need manual attention
    logger.info("\n5. Checking for deprecated imports...")
    check_for_deprecated_imports()

    # Report on potential archives
    logger.info("\n6. Checking for old experiments...")
    cleanup_old_experiments()

    # Check asset-processor
    logger.info("\n7. Checking asset-processor service...")
    update_asset_processor_service()

    logger.info("\n" + "=" * 60)
    logger.info("Cleanup complete! Review the output above for any manual tasks.")


if __name__ == "__main__":
    main()
