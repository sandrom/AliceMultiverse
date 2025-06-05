"""Storage module for AliceMultiverse.

This module provides storage abstractions that support the file-first,
metadata-embedded architecture of AliceMultiverse.
"""

from .unified_duckdb import DuckDBSearchCache, DuckDBSearch, UnifiedDuckDBStorage
from .file_scanner import FileScanner
from .location_registry import LocationStatus, StorageLocation, StorageRegistry, StorageRule, StorageType
from .metadata_extractor import MetadataExtractor

__all__ = [
    "DuckDBSearchCache",
    "DuckDBSearch",
    "UnifiedDuckDBStorage",
    "FileScanner", 
    "LocationStatus",
    "MetadataExtractor",
    "StorageLocation",
    "StorageRegistry",
    "StorageRule",
    "StorageType"
]