"""Database module - DEPRECATED: Use storage module instead."""

import logging

from ..storage.file_cache import FileCache

logger = logging.getLogger(__name__)
logger.warning("database module is deprecated - use storage module instead")

# Keep for backward compatibility
__all__ = ["FileCache"]