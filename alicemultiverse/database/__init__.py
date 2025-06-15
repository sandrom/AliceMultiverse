"""Database module for AliceMultiverse - Cache support with Redis or file backend."""

import logging
import os

logger = logging.getLogger(__name__)

# Check if Redis is available and requested
USE_REDIS_CACHE = os.getenv("USE_REDIS_CACHE", "false").lower() == "true"

try:
    if USE_REDIS_CACHE:
        from .cache import RedisCache
        logger.info("Using Redis for caching")
    else:
        raise ImportError("File-based cache requested")

except (ImportError, Exception) as e:
    # Fall back to file-based cache
    if USE_REDIS_CACHE:
        logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to file-based cache.")
    else:
        logger.info("Using file-based cache")

    from .file_cache import FileCache as RedisCache  # Alias for compatibility

__all__ = ["RedisCache"]
