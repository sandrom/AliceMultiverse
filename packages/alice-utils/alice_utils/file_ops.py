"""File operation utilities."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Union, Optional
import re

from .hashing import compute_file_hash


def hash_file_content(file_path: Union[str, Path]) -> str:
    """Compute SHA256 hash of file content."""
    return compute_file_hash(file_path)


def copy_with_metadata(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Copy file preserving metadata."""
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Ensure destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy file with metadata
    shutil.copy2(src_path, dst_path)
    
    # Preserve additional metadata if possible
    try:
        stat = src_path.stat()
        os.utime(dst_path, (stat.st_atime, stat.st_mtime))
    except Exception:
        pass  # Best effort


def atomic_write(file_path: Union[str, Path], content: Union[str, bytes], 
                mode: str = "w") -> None:
    """Write file atomically using a temporary file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file first
    with tempfile.NamedTemporaryFile(
        mode=mode,
        dir=file_path.parent,
        delete=False
    ) as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    # Atomic rename
    Path(tmp_path).replace(file_path)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if needed."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for filesystem safety."""
    # Remove/replace unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    safe_name = ''.join(char for char in safe_name if ord(char) >= 32)
    
    # Trim to max length preserving extension
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        max_name_length = max_length - len(ext)
        safe_name = name[:max_name_length] + ext
    
    return safe_name.strip()


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize and expand path."""
    path = Path(path)
    
    # Expand user home directory
    if str(path).startswith("~"):
        path = path.expanduser()
    
    # Resolve to absolute path
    path = path.resolve()
    
    return path