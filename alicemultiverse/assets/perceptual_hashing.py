"""Perceptual hashing for similarity search.

This module implements perceptual hashing algorithms that generate
similar hashes for visually similar images, enabling "find similar" features.
"""

import logging
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def calculate_perceptual_hash(
    file_path: Path,
    hash_size: int = 8,
    highfreq_factor: int = 4
) -> str | None:
    """Calculate perceptual hash (pHash) for an image.

    This uses the DCT (Discrete Cosine Transform) method to create
    a hash that's robust to scaling, aspect ratio changes, and
    minor color/brightness variations.

    Args:
        file_path: Path to image file
        hash_size: Size of the hash (8 = 64 bit hash)
        highfreq_factor: Factor for high frequency extraction

    Returns:
        Hex string of perceptual hash or None if failed
    """
    try:
        # Open and prepare image
        with Image.open(file_path) as img:
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')

            # Resize to remove high frequencies
            img_size = hash_size * highfreq_factor
            img = img.resize((img_size, img_size), Image.Resampling.LANCZOS)

            # Convert to numpy array
            pixels = np.array(img, dtype=np.float32)

            # Apply DCT (Discrete Cosine Transform)
            dct = _dct2d(pixels)

            # Extract top-left corner (low frequencies)
            dct_low = dct[:hash_size, :hash_size]

            # Calculate median
            median = np.median(dct_low)

            # Generate hash by comparing to median
            hash_bits = dct_low > median

            # Convert to hex string
            return _bits_to_hex(hash_bits.flatten())

    except Exception as e:
        logger.error(f"Failed to calculate perceptual hash for {file_path}: {e}")
        return None


def calculate_difference_hash(file_path: Path, hash_size: int = 8) -> str | None:
    """Calculate difference hash (dHash) for an image.

    This is simpler and faster than pHash but still effective
    for finding similar images.

    Args:
        file_path: Path to image file
        hash_size: Size of the hash

    Returns:
        Hex string of difference hash or None if failed
    """
    try:
        with Image.open(file_path) as img:
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')

            # Resize to (hash_size+1) x hash_size
            img = img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)

            # Convert to numpy array
            pixels = np.array(img, dtype=np.float32)

            # Calculate differences between adjacent pixels
            diff = pixels[:, 1:] > pixels[:, :-1]

            # Convert to hex string
            return _bits_to_hex(diff.flatten())

    except Exception as e:
        logger.error(f"Failed to calculate difference hash for {file_path}: {e}")
        return None


def calculate_average_hash(file_path: Path, hash_size: int = 8) -> str | None:
    """Calculate average hash (aHash) for an image.

    This is the simplest and fastest perceptual hash.

    Args:
        file_path: Path to image file
        hash_size: Size of the hash

    Returns:
        Hex string of average hash or None if failed
    """
    try:
        with Image.open(file_path) as img:
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')

            # Resize to hash_size x hash_size
            img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

            # Convert to numpy array
            pixels = np.array(img, dtype=np.float32)

            # Calculate average
            avg = pixels.mean()

            # Generate hash by comparing to average
            hash_bits = pixels > avg

            # Convert to hex string
            return _bits_to_hex(hash_bits.flatten())

    except Exception as e:
        logger.error(f"Failed to calculate average hash for {file_path}: {e}")
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate Hamming distance between two hashes.

    Args:
        hash1: First hash (hex string)
        hash2: Second hash (hex string)

    Returns:
        Hamming distance (number of differing bits)
    """
    if len(hash1) != len(hash2):
        raise ValueError("Hashes must be same length")

    # TODO: Review unreachable code - # Convert hex to binary
    # TODO: Review unreachable code - bits1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
    # TODO: Review unreachable code - bits2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)

    # TODO: Review unreachable code - # Count differing bits
    # TODO: Review unreachable code - return sum(b1 != b2 for b1, b2 in zip(bits1, bits2, strict=False))


def find_similar_hashes(
    target_hash: str,
    hash_list: list[tuple[str, str]],
    threshold: int = 10
) -> list[tuple[str, int]]:
    """Find hashes similar to target within threshold.

    Args:
        target_hash: Target hash to compare against
        hash_list: List of (identifier, hash) tuples
        threshold: Maximum Hamming distance for similarity

    Returns:
        List of (identifier, distance) tuples sorted by distance
    """
    similar = []

    for identifier, hash_value in hash_list:
        try:
            distance = hamming_distance(target_hash, hash_value)
            if distance <= threshold:
                similar.append((identifier, distance))
        except ValueError:
            # Skip if hashes are different lengths
            continue

    # Sort by distance (most similar first)
    similar.sort(key=lambda x: x[1])

    return similar


# TODO: Review unreachable code - def _dct2d(matrix: np.ndarray) -> np.ndarray:
# TODO: Review unreachable code - """2D Discrete Cosine Transform.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - matrix: 2D numpy array

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - DCT coefficients
# TODO: Review unreachable code - """
# TODO: Review unreachable code - # This is a simplified DCT implementation
# TODO: Review unreachable code - # For production, consider using scipy.fftpack.dct
# TODO: Review unreachable code - n = matrix.shape[0]
# TODO: Review unreachable code - dct_matrix = np.zeros_like(matrix)

# TODO: Review unreachable code - for i in range(n):
# TODO: Review unreachable code - for j in range(n):
# TODO: Review unreachable code - sum_val = 0.0
# TODO: Review unreachable code - for x in range(n):
# TODO: Review unreachable code - for y in range(n):
# TODO: Review unreachable code - sum_val += matrix[x, y] * np.cos((2*x+1)*i*np.pi/(2*n)) * np.cos((2*y+1)*j*np.pi/(2*n))

# TODO: Review unreachable code - # Normalization
# TODO: Review unreachable code - ci = 1.0 if i == 0 else np.sqrt(2)
# TODO: Review unreachable code - cj = 1.0 if j == 0 else np.sqrt(2)
# TODO: Review unreachable code - dct_matrix[i, j] = ci * cj * sum_val * 2 / n

# TODO: Review unreachable code - return dct_matrix


# TODO: Review unreachable code - def _bits_to_hex(bits: np.ndarray) -> str:
# TODO: Review unreachable code - """Convert bit array to hex string.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - bits: Boolean array

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Hex string representation
# TODO: Review unreachable code - """
# TODO: Review unreachable code - # Convert boolean array to binary string
# TODO: Review unreachable code - bit_string = ''.join('1' if b else '0' for b in bits)

# TODO: Review unreachable code - # Convert binary to hex
# TODO: Review unreachable code - hex_value = hex(int(bit_string, 2))[2:]

# TODO: Review unreachable code - # Pad with zeros if needed
# TODO: Review unreachable code - expected_length = len(bits) // 4
# TODO: Review unreachable code - return hex_value.zfill(expected_length)
