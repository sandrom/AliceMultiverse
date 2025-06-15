"""File-based caching support for search and embeddings.

A simple file-based cache that mimics the RedisCache interface.
Stores cache data as JSON files in a local directory.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class FileCache:
    """File-based cache manager for AliceMultiverse.
    
    Provides the same interface as RedisCache but uses local files.
    Perfect for personal use and development environments.
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        prefix: str = "alice",
        ttl: int = 3600,
        **kwargs  # Accept and ignore Redis-specific parameters
    ):
        """Initialize file cache.
        
        Args:
            cache_dir: Directory for cache files. Defaults to ~/.alice/cache
            prefix: Key prefix for all cache keys
            ttl: Default TTL in seconds
            **kwargs: Ignored Redis-specific parameters for compatibility
        """
        self.prefix = prefix
        self.ttl = ttl
        self._lock = Lock()

        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".alice" / "cache"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"File cache initialized at {self.cache_dir}")

    @property
    def is_available(self) -> bool:
        """Check if cache is available (always True for file cache)."""
        return True

    def _make_key(self, namespace: str, key: str) -> str:
        """Create a namespaced key.
        
        Args:
            namespace: Cache namespace (e.g., "search", "embedding")
            key: Specific key
            
        Returns:
            Full cache key
        """
        return f"{self.prefix}:{namespace}:{key}"

    def _get_cache_path(self, full_key: str) -> Path:
        """Get file path for a cache key."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.md5(full_key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def _is_expired(self, cache_data: dict) -> bool:
        """Check if cache entry is expired."""
        if "expires_at" not in cache_data:
            return False
        return time.time() > cache_data["expires_at"]

    def get(self, namespace: str, key: str) -> Any | None:
        """Get value from cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        full_key = self._make_key(namespace, key)
        cache_path = self._get_cache_path(full_key)

        try:
            if not cache_path.exists():
                return None

            with self._lock:
                with open(cache_path) as f:
                    cache_data = json.load(f)

            if self._is_expired(cache_data):
                # Clean up expired entry
                cache_path.unlink(missing_ok=True)
                return None

            return cache_data.get("value")

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int | None = None
    ) -> bool:
        """Set value in cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not specified)
            
        Returns:
            True if successful
        """
        full_key = self._make_key(namespace, key)
        cache_path = self._get_cache_path(full_key)

        try:
            cache_data = {
                "key": full_key,
                "value": value,
                "created_at": time.time(),
                "expires_at": time.time() + (ttl or self.ttl)
            }

            with self._lock:
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            True if deleted
        """
        full_key = self._make_key(namespace, key)
        cache_path = self._get_cache_path(full_key)

        try:
            cache_path.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace.
        
        Args:
            namespace: Cache namespace to clear
            
        Returns:
            Number of keys deleted
        """
        count = 0

        try:
            # Since we hash keys, we need to check each file
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file) as f:
                        data = json.load(f)

                    if data.get("key", "").startswith(f"{self.prefix}:{namespace}:"):
                        cache_file.unlink()
                        count += 1

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Clear namespace error: {e}")

        return count

    def _hash_dict(self, data: dict) -> str:
        """Create hash from dictionary for cache keys.
        
        Args:
            data: Dictionary to hash
            
        Returns:
            Hash string
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()

    # Specialized methods for search results

    def get_search_results(self, query_hash: str) -> dict | None:
        """Get cached search results.
        
        Args:
            query_hash: Hash of search query
            
        Returns:
            Cached results or None
        """
        return self.get("search", query_hash)

    def set_search_results(
        self,
        query_hash: str,
        results: dict,
        ttl: int | None = None
    ) -> bool:
        """Cache search results.
        
        Args:
            query_hash: Hash of search query
            results: Search results to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        return self.set("search", query_hash, results, ttl)

    # Specialized methods for embeddings

    def get_embedding(self, content_hash: str) -> list[float] | None:
        """Get cached embedding.
        
        Args:
            content_hash: Hash of content
            
        Returns:
            Embedding vector or None
        """
        return self.get("embedding", content_hash)

    def set_embedding(
        self,
        content_hash: str,
        embedding: list[float],
        ttl: int | None = None
    ) -> bool:
        """Cache embedding.
        
        Args:
            content_hash: Hash of content
            embedding: Embedding vector
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        return self.set("embedding", content_hash, embedding, ttl)

    def get_embeddings_batch(
        self,
        content_hashes: list[str]
    ) -> dict[str, list[float]]:
        """Get multiple embeddings.
        
        Args:
            content_hashes: List of content hashes
            
        Returns:
            Dictionary of hash -> embedding
        """
        results = {}
        for hash_val in content_hashes:
            embedding = self.get_embedding(hash_val)
            if embedding:
                results[hash_val] = embedding
        return results

    def set_embeddings_batch(
        self,
        embeddings: dict[str, list[float]],
        ttl: int | None = None
    ) -> int:
        """Set multiple embeddings.
        
        Args:
            embeddings: Dictionary of hash -> embedding
            ttl: Time to live in seconds
            
        Returns:
            Number of embeddings cached
        """
        count = 0
        for hash_val, embedding in embeddings.items():
            if self.set_embedding(hash_val, embedding, ttl):
                count += 1
        return count

    # Cleanup methods

    def cleanup_expired(self) -> int:
        """Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        count = 0

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file) as f:
                        data = json.load(f)

                    if self._is_expired(data):
                        cache_file.unlink()
                        count += 1

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

        return count


# Alias for compatibility
RedisCache = FileCache
