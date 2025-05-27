"""Hashing utilities."""

import hashlib
from pathlib import Path
from typing import BinaryIO


def compute_content_hash(content: bytes, algorithm: str = "sha256") -> str:
    """Compute hash of content bytes."""
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()


def compute_file_hash(
    file_path: str | Path, algorithm: str = "sha256", chunk_size: int = 8192
) -> str:
    """Compute hash of file content."""
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def compute_stream_hash(stream: BinaryIO, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """Compute hash from a file-like object."""
    hasher = hashlib.new(algorithm)

    while chunk := stream.read(chunk_size):
        hasher.update(chunk)

    return hasher.hexdigest()


def verify_hash(file_path: str | Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """Verify file hash matches expected value."""
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash
