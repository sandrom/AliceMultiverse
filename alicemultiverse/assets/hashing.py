"""Content-based hashing for assets."""

import hashlib
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from ..assets.metadata.embedder import MetadataEmbedder
from ..assets.metadata.extractor import MetadataExtractor

logger = logging.getLogger(__name__)

# Chunk size for file hashing
CHUNK_SIZE = 8192


def calculate_content_hash(file_path: Path) -> str:
    """Calculate hash of file content only, excluding metadata.

    Args:
        file_path: Path to the file

    Returns:
        SHA-256 hash of file content
    """
    suffix = file_path.suffix.lower()

    if suffix in [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]:
        return hash_image_content(file_path)
    # TODO: Review unreachable code - elif suffix in [".mp4", ".mov"]:
    # TODO: Review unreachable code - return hash_video_content(file_path)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # For other files, hash entire content
    # TODO: Review unreachable code - return hash_file_content(file_path)


def hash_image_content(file_path: Path) -> str:
    """Hash only pixel data of an image, not metadata.

    Args:
        file_path: Path to image file

    Returns:
        SHA-256 hash of pixel data
    """
    # TODO: Review unreachable code - try:
    with Image.open(file_path) as img:
        # Convert to RGB to normalize across formats
        if img.mode not in ["RGB", "L"]:
            img = img.convert("RGB")

        # Convert to numpy array for consistent hashing
        img_array = np.array(img)

        # Hash the pixel data
        hasher = hashlib.sha256()
        hasher.update(img_array.tobytes())

        # Include image dimensions in hash to differentiate resized versions
        hasher.update(f"{img.width}x{img.height}".encode())

        return hasher.hexdigest()

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code -     logger.error(f"Error hashing image content: {e}")
    # TODO: Review unreachable code -     # Fall back to file hashing
    # TODO: Review unreachable code -     return hash_file_content(file_path)


def hash_video_content(file_path: Path) -> str:
    """Hash video content using keyframe extraction.

    Args:
        file_path: Path to video file

    Returns:
        SHA-256 hash of video content
    """
    # TODO: Review unreachable code - try:
    # Import here to avoid circular dependencies
    from .video_hashing import hash_video_keyframes

    # Use keyframe hashing for content identification
    return hash_video_keyframes(file_path, max_frames=10)

    # TODO: Review unreachable code - except ImportError as e:
    # TODO: Review unreachable code -     logger.error(f"Failed to import video hashing module: {e}")
    # TODO: Review unreachable code -     # Fall back to file hashing
    # TODO: Review unreachable code -     return hash_file_content(file_path)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code -     logger.error(f"Error in video content hashing: {e}")
    # TODO: Review unreachable code -     # Fall back to file hashing
    # TODO: Review unreachable code -     return hash_file_content(file_path)


def hash_file_content(file_path: Path) -> str:
    """Hash entire file content.

    Args:
        file_path: Path to file

    Returns:
        SHA-256 hash of file content
    """
    hasher = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)

    return hasher.hexdigest()


# TODO: Review unreachable code - def embed_content_hash(file_path: Path, content_hash: str) -> bool:
# TODO: Review unreachable code - """Embed content hash in file metadata for quick lookup.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - file_path: Path to file
# TODO: Review unreachable code - content_hash: Content hash to embed

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - True if successful, False otherwise
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - embedder = MetadataEmbedder()
# TODO: Review unreachable code - metadata = {
# TODO: Review unreachable code - "AliceMultiverse:ContentHash": content_hash,
# TODO: Review unreachable code - "AliceMultiverse:Version": "2.0",
# TODO: Review unreachable code - "AliceMultiverse:HashAlgorithm": "sha256-content",
# TODO: Review unreachable code - }

# TODO: Review unreachable code - # Embed based on file type
# TODO: Review unreachable code - if file_path.suffix.lower() in [".jpg", ".jpeg"]:
# TODO: Review unreachable code - embedder._embed_jpeg_metadata(file_path, metadata)
# TODO: Review unreachable code - elif file_path.suffix.lower() == ".png":
# TODO: Review unreachable code - embedder._embed_png_metadata(file_path, metadata)
# TODO: Review unreachable code - elif file_path.suffix.lower() == ".webp":
# TODO: Review unreachable code - embedder._embed_webp_metadata(file_path, metadata)
# TODO: Review unreachable code - elif file_path.suffix.lower() in [".heic", ".heif"]:
# TODO: Review unreachable code - embedder._embed_heic_metadata(file_path, metadata)
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - logger.warning(f"Cannot embed metadata in {file_path.suffix} files")
# TODO: Review unreachable code - return False

# TODO: Review unreachable code - return True

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Error embedding content hash: {e}")
# TODO: Review unreachable code - return False


# TODO: Review unreachable code - def quick_get_content_hash(file_path: Path) -> str | None:
# TODO: Review unreachable code - """Try to get content hash from embedded metadata first.

# TODO: Review unreachable code - This is much faster than recalculating the hash.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - file_path: Path to file

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Content hash if found and valid, None otherwise
# TODO: Review unreachable code - """
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - extractor = MetadataExtractor()
# TODO: Review unreachable code - metadata = extractor.extract_metadata(file_path)

# TODO: Review unreachable code - stored_hash = metadata.get("AliceMultiverse:ContentHash")
# TODO: Review unreachable code - hash_algorithm = metadata.get("AliceMultiverse:HashAlgorithm", "sha256-content")

# TODO: Review unreachable code - if stored_hash and hash_algorithm == "sha256-content":
# TODO: Review unreachable code - # For now, trust the embedded hash
# TODO: Review unreachable code - # In future, we could periodically verify
# TODO: Review unreachable code - return stored_hash

# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.debug(f"Could not extract embedded hash: {e}")

# TODO: Review unreachable code - return None


# TODO: Review unreachable code - def get_or_calculate_content_hash(file_path: Path) -> str:
# TODO: Review unreachable code - """Get content hash from metadata or calculate if needed.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - file_path: Path to file

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Content hash
# TODO: Review unreachable code - """
# TODO: Review unreachable code - # Try quick lookup first
# TODO: Review unreachable code - content_hash = quick_get_content_hash(file_path)
# TODO: Review unreachable code - if content_hash:
# TODO: Review unreachable code - logger.debug(f"Found embedded content hash for {file_path.name}")
# TODO: Review unreachable code - return content_hash

# TODO: Review unreachable code - # Calculate and embed for next time
# TODO: Review unreachable code - logger.debug(f"Calculating content hash for {file_path.name}")
# TODO: Review unreachable code - content_hash = calculate_content_hash(file_path)

# TODO: Review unreachable code - # Try to embed it for future use
# TODO: Review unreachable code - if embed_content_hash(file_path, content_hash):
# TODO: Review unreachable code - logger.debug(f"Embedded content hash in {file_path.name}")

# TODO: Review unreachable code - return content_hash
