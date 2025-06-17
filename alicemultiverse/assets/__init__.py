"""Assets module for AliceMultiverse.

This module consolidates all media asset handling functionality:
- Metadata extraction and embedding
- Deduplication and similarity detection
- Hashing and fingerprinting
- Discovery and organization
"""

# Re-export commonly used classes for backward compatibility
from .deduplication.duplicate_finder import DuplicateFinder
from .deduplication.perceptual_hasher import PerceptualHasher
from .deduplication.similarity_index import SimilarityIndex
from .hashing import calculate_content_hash as get_content_hash
from .hashing import hash_file_content as get_file_hash
from .metadata.embedder import MetadataEmbedder
from .metadata.extractor import MetadataExtractor
from .metadata.models import AssetMetadata, AssetRole

__all__ = [
    "get_content_hash",
    "get_file_hash",
    "MetadataEmbedder",
    "MetadataExtractor",
    "AssetMetadata",
    "AssetRole",
    "DuplicateFinder",
    "PerceptualHasher",
    "SimilarityIndex",
]
