"""Performance configuration for AliceMultiverse."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations."""
    
    # Parallel processing settings
    max_workers: int = 8  # Maximum parallel workers
    batch_size: int = 100  # Files per batch
    
    # Database optimization
    enable_batch_operations: bool = True
    batch_insert_size: int = 500  # Records per batch insert
    transaction_size: int = 1000  # Operations per transaction
    
    # Memory management
    max_memory_cache_mb: int = 500  # Maximum cache size in MB
    cache_ttl_seconds: int = 3600  # Cache time-to-live
    
    # File processing
    parallel_metadata_extraction: bool = True
    parallel_hash_computation: bool = True
    async_file_operations: bool = True
    
    # Understanding system
    understanding_batch_size: int = 20  # Images per API batch
    max_concurrent_api_calls: int = 5  # Concurrent API requests
    
    # Search optimization
    search_result_cache: bool = True
    search_cache_size: int = 1000  # Number of cached queries
    
    # Monitoring
    enable_performance_monitoring: bool = True
    log_performance_metrics: bool = True
    metrics_interval_seconds: int = 60
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'PerformanceConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'max_workers': self.max_workers,
            'batch_size': self.batch_size,
            'enable_batch_operations': self.enable_batch_operations,
            'batch_insert_size': self.batch_insert_size,
            'transaction_size': self.transaction_size,
            'max_memory_cache_mb': self.max_memory_cache_mb,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'parallel_metadata_extraction': self.parallel_metadata_extraction,
            'parallel_hash_computation': self.parallel_hash_computation,
            'async_file_operations': self.async_file_operations,
            'understanding_batch_size': self.understanding_batch_size,
            'max_concurrent_api_calls': self.max_concurrent_api_calls,
            'search_result_cache': self.search_result_cache,
            'search_cache_size': self.search_cache_size,
            'enable_performance_monitoring': self.enable_performance_monitoring,
            'log_performance_metrics': self.log_performance_metrics,
            'metrics_interval_seconds': self.metrics_interval_seconds
        }


def get_performance_config(profile: str = "default") -> PerformanceConfig:
    """Get performance configuration for a specific profile.
    
    Args:
        profile: Configuration profile name
        
    Returns:
        PerformanceConfig instance
    """
    profiles = {
        "default": PerformanceConfig(),
        
        "fast": PerformanceConfig(
            max_workers=16,
            batch_size=200,
            batch_insert_size=1000,
            understanding_batch_size=50,
            max_concurrent_api_calls=10
        ),
        
        "memory_constrained": PerformanceConfig(
            max_workers=4,
            batch_size=50,
            max_memory_cache_mb=100,
            cache_ttl_seconds=600,
            search_cache_size=100
        ),
        
        "large_collection": PerformanceConfig(
            max_workers=12,
            batch_size=500,
            batch_insert_size=2000,
            transaction_size=5000,
            enable_batch_operations=True,
            parallel_metadata_extraction=True,
            parallel_hash_computation=True
        )
    }
    
    return profiles.get(profile, profiles["default"])