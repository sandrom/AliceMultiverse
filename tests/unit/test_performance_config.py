"""Tests for performance configuration functionality."""

import pytest

from alicemultiverse.core.performance_config import (
    PerformanceConfig,
    get_performance_config,
)


class TestPerformanceConfig:
    """Test PerformanceConfig functionality."""
    
    def test_default_config(self):
        """Test default performance configuration."""
        config = PerformanceConfig()
        
        assert config.max_workers == 8
        assert config.batch_size == 100
        assert config.enable_batch_operations is True
        assert config.parallel_metadata_extraction is True
        assert config.max_memory_cache_mb == 500
        assert config.cache_ttl_seconds == 3600
    
    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "max_workers": 4,
            "batch_size": 50,
            "enable_batch_operations": False,
            "parallel_metadata_extraction": False,
            "max_memory_cache_mb": 200,
            "cache_ttl_seconds": 1800
        }
        
        config = PerformanceConfig.from_dict(data)
        
        assert config.max_workers == 4
        assert config.batch_size == 50
        assert config.enable_batch_operations is False
        assert config.parallel_metadata_extraction is False
        assert config.max_memory_cache_mb == 200
        assert config.cache_ttl_seconds == 1800
    
    def test_from_dict_partial(self):
        """Test creating config from partial dictionary."""
        data = {
            "max_workers": 2,
            "batch_size": 25
        }
        
        config = PerformanceConfig.from_dict(data)
        
        # Specified values
        assert config.max_workers == 2
        assert config.batch_size == 25
        
        # Default values
        assert config.enable_batch_operations is True
        assert config.parallel_metadata_extraction is True
        assert config.max_memory_cache_mb == 500
        assert config.cache_ttl_seconds == 3600
    
    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = PerformanceConfig(
            max_workers=6,
            batch_size=75,
            enable_batch_operations=False
        )
        
        data = config.to_dict()
        
        assert data["max_workers"] == 6
        assert data["batch_size"] == 75
        assert data["enable_batch_operations"] is False
        assert data["parallel_metadata_extraction"] is True
        assert data["max_memory_cache_mb"] == 500
        assert data["cache_ttl_seconds"] == 3600


class TestGetPerformanceConfig:
    """Test get_performance_config function."""
    
    def test_default_profile(self):
        """Test getting default profile."""
        config = get_performance_config()
        
        assert config.max_workers == 8
        assert config.batch_size == 100
        assert config.enable_batch_operations is True
    
    def test_fast_profile(self):
        """Test getting fast profile."""
        config = get_performance_config("fast")
        
        assert config.max_workers == 16
        assert config.batch_size == 200
        assert config.batch_insert_size == 1000
        assert config.understanding_batch_size == 50
        assert config.max_concurrent_api_calls == 10
    
    def test_memory_constrained_profile(self):
        """Test getting memory constrained profile."""
        config = get_performance_config("memory_constrained")
        
        assert config.max_workers == 4
        assert config.batch_size == 50
        assert config.max_memory_cache_mb == 100
        assert config.cache_ttl_seconds == 600
        assert config.search_cache_size == 100
    
    def test_large_collection_profile(self):
        """Test getting large collection profile."""
        config = get_performance_config("large_collection")
        
        assert config.max_workers == 12
        assert config.batch_size == 500
        assert config.batch_insert_size == 2000
        assert config.transaction_size == 5000
        assert config.enable_batch_operations is True
        assert config.parallel_metadata_extraction is True
        assert config.parallel_hash_computation is True
    
    def test_invalid_profile_returns_default(self):
        """Test that invalid profile returns default."""
        config = get_performance_config("invalid_profile")
        
        # Should return default config
        assert config.max_workers == 8
        assert config.batch_size == 100