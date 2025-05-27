"""Alice Utils - Common utilities for AliceMultiverse."""

from .file_operations import (
    atomic_write,
    copy_with_metadata,
    ensure_directory,
    hash_file_content,
    normalize_path,
    safe_filename,
)
from .hashing import compute_content_hash, compute_file_hash, verify_hash
from .media import (
    detect_media_type,
    extract_image_metadata,
    generate_thumbnail,
    get_file_info,
    is_supported_format,
)

__all__ = [
    # File operations
    "hash_file_content",
    "copy_with_metadata",
    "atomic_write",
    "ensure_directory",
    "safe_filename",
    "normalize_path",
    # Media utilities
    "detect_media_type",
    "is_supported_format",
    "get_file_info",
    "extract_image_metadata",
    "generate_thumbnail",
    # Hashing
    "compute_content_hash",
    "compute_file_hash",
    "verify_hash",
]
