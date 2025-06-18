"""
File Operation Utilities

Safe file operations with error handling, dry-run support, and duplicate detection.
Provides copy/move operations with automatic directory creation and hash-based
file comparison for deduplication.
"""

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from ..core.constants import HASH_CHUNK_SIZE
from ..core.exceptions import FileOperationError

logger = logging.getLogger(__name__)


class FileHandler:
    """Handle file operations with proper error handling and logging."""

    def __init__(self, dry_run: bool = False):
        """Initialize file handler.

        Args:
            dry_run: If True, simulate operations without making changes
        """
        self.dry_run = dry_run

    def copy_file(self, source: Path, destination: Path) -> bool:
        """Copy a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if successful, False otherwise

        Raises:
            FileOperationError: If copy fails
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would copy {source} to {destination}")
            return True

        try:
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Copy file with metadata
            shutil.copy2(source, destination)
            logger.debug(f"Copied {source.name} to {destination}")
            return True

        except Exception as e:
            raise FileOperationError(f"Failed to copy {source}: {e}")

    def move_file(self, source: Path, destination: Path) -> bool:
        """Move a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if successful, False otherwise

        Raises:
            FileOperationError: If move fails
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would move {source} to {destination}")
            return True

        try:
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(source), str(destination))
            logger.debug(f"Moved {source.name} to {destination}")
            return True

        except Exception as e:
            raise FileOperationError(f"Failed to move {source}: {e}")

    def get_file_hash(self, file_path: Path, quick: bool = True) -> str:
        """Calculate hash of file for duplicate detection.

        Args:
            file_path: Path to the file
            quick: If True, use quick hash (size + first/last 1KB)

        Returns:
            Hash string

        Raises:
            FileOperationError: If file cannot be read
        """
        try:
            if quick:
                return self._quick_hash(file_path)
            else:
                return self._full_hash(file_path)
        except Exception as e:
            raise FileOperationError(f"Failed to hash {file_path}: {e}")

    def files_are_identical(self, file1: Path, file2: Path) -> bool:
        """Check if two files are identical.

        Args:
            file1: First file path
            file2: Second file path

        Returns:
            True if files are identical, False otherwise
        """
        try:
            # Quick check: file sizes
            if file1.stat().st_size != file2.stat().st_size:
                return False

            # Compare hashes
            hash1 = self.get_file_hash(file1, quick=False)
            hash2 = self.get_file_hash(file2, quick=False)
            return hash1 == hash2

        except Exception as e:
            logger.warning(f"Failed to compare files: {e}")
            return False

    def _quick_hash(self, file_path: Path) -> str:
        """Calculate quick hash using size and samples."""
        stat = file_path.stat()
        size = stat.st_size

        with open(file_path, "rb") as f:
            first_kb = f.read(1024)
            if size > 2048:
                f.seek(-1024, 2)  # 1KB from end
                last_kb = f.read(1024)
            else:
                last_kb = b""

        content = f"{size}{first_kb}{last_kb}".encode()
        return hashlib.md5(content, usedforsecurity=False).hexdigest()[:16]

    def _full_hash(self, file_path: Path) -> str:
        """Calculate full MD5 hash of file."""
        md5_hash = hashlib.md5(usedforsecurity=False)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()[:16]

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate full hash of file (for duplicate detection).

        Args:
            file_path: Path to the file

        Returns:
            Full hash string

        Raises:
            FileOperationError: If file cannot be read
        """
        return self.get_file_hash(file_path, quick=False)


def find_duplicate(source_path: Path, dest_dir: Path, file_handler: FileHandler) -> Path | None:
    """Find duplicate file in destination directory.

    Args:
        source_path: Source file to check
        dest_dir: Directory to search for duplicates
        file_handler: FileHandler instance

    Returns:
        Path to duplicate file if found, None otherwise
    """
    if not dest_dir.exists():
        return None

    source_hash = file_handler.get_file_hash(source_path)

    for existing_file in dest_dir.iterdir():
        if existing_file.is_file():
            if file_handler.get_file_hash(existing_file) == source_hash:
                return existing_file

    return None


async def download_file(url: str, destination: Path, session: Optional['aiohttp.ClientSession'] = None) -> None:
    """Download a file from URL to destination.

    Args:
        url: URL to download from
        destination: Path to save file
        session: Optional aiohttp session to reuse

    Raises:
        FileOperationError: If download fails or aiohttp not available
    """
    if not AIOHTTP_AVAILABLE:
        raise FileOperationError("aiohttp is required for downloading files. Install with: pip install aiohttp")

    if session is None:
        async with aiohttp.ClientSession() as session:
            await _download_with_session(url, destination, session)
    else:
        await _download_with_session(url, destination, session)


async def _download_with_session(url: str, destination: Path, session: 'aiohttp.ClientSession') -> None:
    """Download file using provided session."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()

            # Ensure directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Download in chunks
            with open(destination, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)

        logger.info(f"Downloaded {url} to {destination}")

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        if destination.exists():
            destination.unlink()  # Clean up partial download
        raise FileOperationError(f"Download failed: {e}")


async def save_text_file(path: Path, content: str, encoding: str = 'utf-8') -> None:
    """Save text content to a file.

    Args:
        path: Path to save file
        content: Text content to save
        encoding: Text encoding (default: utf-8)

    Raises:
        FileOperationError: If save fails
    """
    try:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)

        logger.info(f"Saved text file to {path}")

    except Exception as e:
        logger.error(f"Failed to save text file {path}: {e}")
        raise FileOperationError(f"Save failed: {e}")
