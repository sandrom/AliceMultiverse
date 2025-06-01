"""Storage module for AliceMultiverse.

This module provides storage abstractions that support the file-first,
metadata-embedded architecture of AliceMultiverse.
"""

from .duckdb_cache import DuckDBSearchCache
from .file_scanner import FileScanner
from .metadata_extractor import MetadataExtractor

__all__ = [
    "DuckDBSearchCache",
    "FileScanner", 
    "MetadataExtractor"
]