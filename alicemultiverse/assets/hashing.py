"""Content-based hashing for assets."""

import hashlib
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from ..metadata.embedder import MetadataEmbedder
from ..metadata.extractor import MetadataExtractor

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
    elif suffix in [".mp4", ".mov"]:
        return hash_video_content(file_path)
    else:
        # For other files, hash entire content
        return hash_file_content(file_path)


def hash_image_content(file_path: Path) -> str:
    """Hash only pixel data of an image, not metadata.

    Args:
        file_path: Path to image file

    Returns:
        SHA-256 hash of pixel data
    """
    try:
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

    except Exception as e:
        logger.error(f"Error hashing image content: {e}")
        # Fall back to file hashing
        return hash_file_content(file_path)


def hash_video_content(file_path: Path) -> str:
    """Hash video content using keyframe extraction.

    Args:
        file_path: Path to video file

    Returns:
        SHA-256 hash of video content
    """
    try:
        # Import here to avoid circular dependencies
        from .video_hashing import hash_video_keyframes

        # Use keyframe hashing for content identification
        return hash_video_keyframes(file_path, max_frames=10)

    except ImportError as e:
        logger.error(f"Failed to import video hashing module: {e}")
        # Fall back to file hashing
        return hash_file_content(file_path)
    except Exception as e:
        logger.error(f"Error in video content hashing: {e}")
        # Fall back to file hashing
        return hash_file_content(file_path)


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


def embed_content_hash(file_path: Path, content_hash: str) -> bool:
    """Embed content hash in file metadata for quick lookup.

    Args:
        file_path: Path to file
        content_hash: Content hash to embed

    Returns:
        True if successful, False otherwise
    """
    try:
        embedder = MetadataEmbedder()
        metadata = {
            "AliceMultiverse:ContentHash": content_hash,
            "AliceMultiverse:Version": "2.0",
            "AliceMultiverse:HashAlgorithm": "sha256-content",
        }

        # Embed based on file type
        if file_path.suffix.lower() in [".jpg", ".jpeg"]:
            embedder._embed_jpeg_metadata(file_path, metadata)
        elif file_path.suffix.lower() == ".png":
            embedder._embed_png_metadata(file_path, metadata)
        elif file_path.suffix.lower() == ".webp":
            embedder._embed_webp_metadata(file_path, metadata)
        elif file_path.suffix.lower() in [".heic", ".heif"]:
            embedder._embed_heic_metadata(file_path, metadata)
        else:
            logger.warning(f"Cannot embed metadata in {file_path.suffix} files")
            return False

        return True

    except Exception as e:
        logger.error(f"Error embedding content hash: {e}")
        return False


def quick_get_content_hash(file_path: Path) -> str | None:
    """Try to get content hash from embedded metadata first.

    This is much faster than recalculating the hash.

    Args:
        file_path: Path to file

    Returns:
        Content hash if found and valid, None otherwise
    """
    try:
        extractor = MetadataExtractor()
        metadata = extractor.extract_metadata(file_path)

        stored_hash = metadata.get("AliceMultiverse:ContentHash")
        hash_algorithm = metadata.get("AliceMultiverse:HashAlgorithm", "sha256-content")

        if stored_hash and hash_algorithm == "sha256-content":
            # For now, trust the embedded hash
            # In future, we could periodically verify
            return stored_hash

    except Exception as e:
        logger.debug(f"Could not extract embedded hash: {e}")

    return None


def get_or_calculate_content_hash(file_path: Path) -> str:
    """Get content hash from metadata or calculate if needed.

    Args:
        file_path: Path to file

    Returns:
        Content hash
    """
    # Try quick lookup first
    content_hash = quick_get_content_hash(file_path)
    if content_hash:
        logger.debug(f"Found embedded content hash for {file_path.name}")
        return content_hash

    # Calculate and embed for next time
    logger.debug(f"Calculating content hash for {file_path.name}")
    content_hash = calculate_content_hash(file_path)

    # Try to embed it for future use
    if embed_content_hash(file_path, content_hash):
        logger.debug(f"Embedded content hash in {file_path.name}")

    return content_hash
