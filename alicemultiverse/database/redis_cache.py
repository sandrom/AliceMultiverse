"""Redis caching support for search and embeddings."""

import hashlib
import json
import logging
import pickle
from typing import Any, Optional

import redis
from redis.sentinel import Sentinel

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager for AliceMultiverse."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        sentinel_hosts: Optional[list[tuple[str, int]]] = None,
        sentinel_service: Optional[str] = None,
        prefix: str = "alice",
        ttl: int = 3600,
    ):
        """Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            sentinel_hosts: List of (host, port) tuples for Sentinel
            sentinel_service: Sentinel service name
            prefix: Key prefix for all cache keys
            ttl: Default TTL in seconds
        """
        self.prefix = prefix
        self.ttl = ttl
        self._client = None
        
        try:
            if sentinel_hosts and sentinel_service:
                # Use Sentinel for high availability
                self._sentinel = Sentinel(sentinel_hosts)
                self._client = self._sentinel.master_for(
                    sentinel_service,
                    socket_connect_timeout=5,
                    password=password,
                    db=db
                )
            else:
                # Direct connection
                self._client = redis.StrictRedis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30
                )
            
            # Test connection
            self._client.ping()
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.warning(f"Redis cache connection failed: {e}. Cache disabled.")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create a namespaced key.
        
        Args:
            namespace: Cache namespace (e.g., "search", "embedding")
            key: Specific key
            
        Returns:
            Full Redis key
        """
        return f"{self.prefix}:{namespace}:{key}"
    
    def _hash_dict(self, data: dict) -> str:
        """Create hash from dictionary.
        
        Args:
            data: Dictionary to hash
            
        Returns:
            MD5 hash string
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.is_available:
            return None
        
        try:
            redis_key = self._make_key(namespace, key)
            data = self._client.get(redis_key)
            
            if data:
                return pickle.loads(data)
            
            return None
            
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
            
        Returns:
            True if successful
        """
        if not self.is_available:
            return False
        
        try:
            redis_key = self._make_key(namespace, key)
            data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            
            ttl = ttl or self.ttl
            self._client.setex(redis_key, ttl, data)
            
            return True
            
        except Exception as e:
            logger.debug(f"Cache set error: {e}")
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key
            
        Returns:
            True if deleted
        """
        if not self.is_available:
            return False
        
        try:
            redis_key = self._make_key(namespace, key)
            return bool(self._client.delete(redis_key))
            
        except Exception as e:
            logger.debug(f"Cache delete error: {e}")
            return False
    
    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace.
        
        Args:
            namespace: Cache namespace
            
        Returns:
            Number of keys deleted
        """
        if not self.is_available:
            return 0
        
        try:
            pattern = self._make_key(namespace, "*")
            keys = self._client.keys(pattern)
            
            if keys:
                return self._client.delete(*keys)
            
            return 0
            
        except Exception as e:
            logger.debug(f"Cache clear error: {e}")
            return 0
    
    # Search-specific methods
    
    def cache_search_results(
        self,
        query_params: dict,
        results: list,
        total_count: int,
        ttl: int = 300
    ) -> bool:
        """Cache search results.
        
        Args:
            query_params: Search query parameters
            results: Search results
            total_count: Total count
            ttl: TTL in seconds (default 5 minutes)
            
        Returns:
            True if cached
        """
        key = self._hash_dict(query_params)
        value = {
            "results": results,
            "total_count": total_count,
            "cached_at": json.dumps({"timestamp": "now"})  # Simplified
        }
        
        return self.set("search", key, value, ttl)
    
    def get_search_results(self, query_params: dict) -> Optional[dict]:
        """Get cached search results.
        
        Args:
            query_params: Search query parameters
            
        Returns:
            Cached results or None
        """
        key = self._hash_dict(query_params)
        return self.get("search", key)
    
    # Embedding-specific methods
    
    def cache_embedding(
        self,
        content_hash: str,
        embedding: list[float],
        model: str = "default"
    ) -> bool:
        """Cache an embedding vector.
        
        Args:
            content_hash: Asset content hash
            embedding: Embedding vector
            model: Model name
            
        Returns:
            True if cached
        """
        key = f"{content_hash}:{model}"
        return self.set("embedding", key, embedding, ttl=86400)  # 24 hours
    
    def get_embedding(
        self,
        content_hash: str,
        model: str = "default"
    ) -> Optional[list[float]]:
        """Get cached embedding.
        
        Args:
            content_hash: Asset content hash
            model: Model name
            
        Returns:
            Embedding vector or None
        """
        key = f"{content_hash}:{model}"
        return self.get("embedding", key)
    
    def cache_embeddings_batch(
        self,
        embeddings: dict[str, list[float]],
        model: str = "default"
    ) -> int:
        """Cache multiple embeddings.
        
        Args:
            embeddings: Dict of content_hash -> embedding
            model: Model name
            
        Returns:
            Number of embeddings cached
        """
        if not self.is_available:
            return 0
        
        count = 0
        pipeline = self._client.pipeline()
        
        try:
            for content_hash, embedding in embeddings.items():
                key = self._make_key("embedding", f"{content_hash}:{model}")
                data = pickle.dumps(embedding, protocol=pickle.HIGHEST_PROTOCOL)
                pipeline.setex(key, 86400, data)  # 24 hours
            
            results = pipeline.execute()
            count = sum(1 for r in results if r)
            
        except Exception as e:
            logger.debug(f"Batch cache error: {e}")
        
        return count
    
    # Stats and monitoring
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Cache stats dictionary
        """
        if not self.is_available:
            return {"available": False}
        
        try:
            info = self._client.info()
            
            return {
                "available": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands": info.get("total_commands_processed"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                )
            }
            
        except Exception as e:
            logger.debug(f"Stats error: {e}")
            return {"available": False, "error": str(e)}