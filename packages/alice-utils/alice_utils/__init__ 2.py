"""Alice Utils - Common utilities for AliceMultiverse."""

from .file_operations import (
    hash_file_content,
    copy_with_metadata,
    atomic_write,
    ensure_directory,
    safe_filename,
    normalize_path
)

from .media import (
    detect_media_type,
    is_supported_format,
    get_file_info,
    extract_image_metadata,
    generate_thumbnail
)

from .hashing import (
    compute_content_hash,
    compute_file_hash,
    verify_hash
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
    "verify_hash"
]