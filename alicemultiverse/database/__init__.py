"""Database module for AliceMultiverse - Simple file-based cache for personal use."""

import logging

from .file_cache import FileCache

logger = logging.getLogger(__name__)
logger.info("Using file-based cache")

__all__ = ["FileCache"]