"""Storage module for AliceMultiverse.

This module provides storage abstractions that support the file-first,
metadata-embedded architecture of AliceMultiverse.
"""

from .file_cache import FileCache
from .file_scanner import FileScanner
from .location_registry import (
    LocationStatus,
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)
from .metadata_extractor import MetadataExtractor
from .unified_duckdb import DuckDBSearch, DuckDBSearchCache, UnifiedDuckDBStorage

__all__ = [
    "DuckDBSearch",
    "DuckDBSearchCache",
    "FileCache",
    "FileScanner",
    "LocationStatus",
    "MetadataExtractor",
    "StorageLocation",
    "StorageRegistry",
    "StorageRule",
    "StorageType",
    "UnifiedDuckDBStorage"
]
