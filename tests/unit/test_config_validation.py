"""Tests for configuration validation system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from alicemultiverse.core.config_validation import (
    ValidationResult,
    SystemResources,
    ConfigValidator,
    SmartConfigBuilder
)
from alicemultiverse.core.exceptions_extended import ConfigurationValidationError


class TestValidationResult:
    """Test ValidationResult class."""
    
    def test_initialization(self):
        """Test validation result initialization."""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.errors == {}
        assert result.warnings == {}
        assert result.recommendations == []
    
    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult(is_valid=True)
        
        result.add_error("test.field", "Test error")
        
        assert result.is_valid is False
        assert result.errors["test.field"] == "Test error"
    
    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult(is_valid=True)
        
        result.add_warning("test.field", "Test warning")
        
        assert result.is_valid is True  # Warnings don't invalidate
        assert result.warnings["test.field"] == "Test warning"
    
    def test_add_recommendation(self):
        """Test adding recommendations."""
        result = ValidationResult(is_valid=True)
        
        result.add_recommendation("Test recommendation")
        
        assert "Test recommendation" in result.recommendations
    
    def test_raise_if_invalid(self):
        """Test raising on invalid configuration."""
        result = ValidationResult(is_valid=True)
        result.add_error("field", "error")
        
        with pytest.raises(ConfigurationValidationError) as exc_info:
            result.raise_if_invalid()
        
        assert exc_info.value.errors == {"field": "error"}


class TestSystemResources:
    """Test SystemResources class."""
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_detect(self, mock_disk, mock_memory, mock_cpu):
        """Test system resource detection."""
        mock_cpu.return_value = 8
        mock_memory.return_value = Mock(total=16 * 1024 * 1024 * 1024)  # 16GB
        mock_disk.return_value = Mock(free=100 * 1024 * 1024 * 1024)  # 100GB
        
        resources = SystemResources.detect()
        
        assert resources.cpu_count == 8
        assert resources.memory_mb == 16384
        assert resources.available_disk_mb == 102400
        assert resources.has_gpu is False


class TestConfigValidator:
    """Test ConfigValidator class."""
    
    @patch('alicemultiverse.core.config_validation.SystemResources.detect')
    def test_initialization(self, mock_detect):
        """Test validator initialization."""
        mock_detect.return_value = SystemResources(
            cpu_count=4,
            memory_mb=8192,
            available_disk_mb=50000
        )
        
        validator = ConfigValidator()
        
        assert validator.system_resources.cpu_count == 4
        assert validator.system_resources.memory_mb == 8192
    
    def test_validate_paths_valid(self, tmp_path):
        """Test valid path validation."""
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        # Create test directories
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        organized = tmp_path / "organized"
        
        paths = {
            "inbox": str(inbox),
            "organized": str(organized)
        }
        
        validator._validate_paths(paths, result)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert organized.exists()  # Should be created
    
    def test_validate_paths_missing_inbox(self):
        """Test missing inbox path."""
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        paths = {
            "inbox": "/nonexistent/path",
            "organized": "/tmp/organized"
        }
        
        validator._validate_paths(paths, result)
        
        assert not result.is_valid
        assert "paths.inbox" in result.errors
    
    def test_validate_paths_no_permissions(self, tmp_path):
        """Test path permission validation."""
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        # Create read-only directory
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        organized = tmp_path / "organized"
        organized.mkdir()
        organized.chmod(0o444)  # Read-only
        
        paths = {
            "inbox": str(inbox),
            "organized": str(organized)
        }
        
        validator._validate_paths(paths, result)
        
        # Restore permissions for cleanup
        organized.chmod(0o755)
        
        assert not result.is_valid
        assert "paths.organized" in result.errors
    
    @patch('alicemultiverse.core.config_validation.SystemResources.detect')
    def test_validate_performance(self, mock_detect):
        """Test performance validation."""
        mock_detect.return_value = SystemResources(
            cpu_count=4,
            memory_mb=8192,
            available_disk_mb=50000
        )
        
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        # Test excessive workers
        performance = {
            "max_workers": 20,  # Too many for 4 CPUs
            "batch_size": 1000,  # Large batch
            "profile": "invalid_profile"
        }
        
        validator._validate_performance(performance, result)
        
        assert "performance.max_workers" in result.warnings
        assert "performance.batch_size" in result.warnings
        assert "performance.profile" in result.errors
    
    def test_validate_storage(self, tmp_path):
        """Test storage validation."""
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        storage = {
            "search_db": str(tmp_path / "search.db"),
            "cache_size_mb": 10000  # Very large
        }
        
        validator._validate_storage(storage, result)
        
        # Should warn about large cache
        assert "storage.cache_size_mb" in result.warnings
    
    def test_validate_api_keys(self):
        """Test API key validation."""
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        config = {
            "understanding": {
                "enabled": True,
                "providers": ["openai"]
            }
        }
        
        # No API keys in environment
        with patch.dict(os.environ, {}, clear=True):
            validator._validate_api_keys(config, result)
        
        assert "api_keys" in result.warnings
    
    def test_validate_understanding(self):
        """Test understanding configuration validation."""
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        # Test missing providers
        understanding = {
            "enabled": True,
            "providers": []
        }
        
        validator._validate_understanding(understanding, result)
        
        assert "understanding.providers" in result.errors
        
        # Test negative cost limit
        result = ValidationResult(is_valid=True)
        understanding = {
            "enabled": True,
            "providers": ["openai"],
            "cost_limit": -10
        }
        
        validator._validate_understanding(understanding, result)
        
        assert "understanding.cost_limit" in result.errors
    
    @patch('alicemultiverse.core.config_validation.SystemResources.detect')
    def test_add_recommendations(self, mock_detect):
        """Test recommendation generation."""
        mock_detect.return_value = SystemResources(
            cpu_count=16,
            memory_mb=32768,  # 32GB
            available_disk_mb=10000
        )
        
        validator = ConfigValidator()
        result = ValidationResult(is_valid=True)
        
        config = {
            "performance": {
                "max_workers": 4,  # Under-utilizing
                "batch_size": 50,
                "profile": "default"
            }
        }
        
        validator._add_recommendations(config, result)
        
        # Should recommend more workers and fast profile
        assert any("max_workers" in rec for rec in result.recommendations)
        assert any("fast" in rec for rec in result.recommendations)
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    def test_validate_runtime_compatibility(self, mock_cpu, mock_memory):
        """Test runtime compatibility validation."""
        mock_memory.return_value = Mock(available=1024 * 1024 * 1024)  # 1GB available
        mock_cpu.return_value = 85.0  # High CPU
        
        validator = ConfigValidator()
        
        config = {
            "performance": {
                "batch_size": 200
            }
        }
        
        result = validator.validate_runtime_compatibility(config)
        
        assert "runtime.memory" in result.warnings
        assert "runtime.cpu" in result.warnings
        assert len(result.recommendations) > 0


class TestSmartConfigBuilder:
    """Test SmartConfigBuilder class."""
    
    @patch('alicemultiverse.core.config_validation.SystemResources.detect')
    def test_build_config(self, mock_detect):
        """Test configuration building."""
        mock_detect.return_value = SystemResources(
            cpu_count=8,
            memory_mb=16384,
            available_disk_mb=100000
        )
        
        builder = SmartConfigBuilder()
        
        base_config = {
            "paths": {
                "inbox": "/inbox",
                "organized": "/organized"
            }
        }
        
        # Test quick scan use case
        config = builder.build_config(base_config, "quick_scan")
        
        assert "performance" in config
        assert config["performance"]["enable_understanding"] is False
        assert config["performance"]["batch_size"] <= 50
    
    @patch('alicemultiverse.core.config_validation.SystemResources.detect')
    def test_optimize_for_collection_size(self, mock_detect):
        """Test collection size optimization."""
        mock_detect.return_value = SystemResources(
            cpu_count=8,
            memory_mb=16384,
            available_disk_mb=100000
        )
        
        builder = SmartConfigBuilder()
        
        config = {"performance": {}}
        
        # Test small collection
        small_config = builder.optimize_for_collection_size(config, 50)
        assert small_config["performance"]["batch_size"] == 10
        
        # Test large collection
        large_config = builder.optimize_for_collection_size(config, 5000)
        assert large_config["performance"]["batch_size"] == 200
        assert large_config["performance"]["enable_batch_operations"] is True
    
    @patch('alicemultiverse.core.config_validation.SystemResources.detect')
    def test_recommend_performance_profile(self, mock_detect):
        """Test performance profile recommendation."""
        # Test low memory system
        mock_detect.return_value = SystemResources(
            cpu_count=2,
            memory_mb=3000,
            available_disk_mb=50000
        )
        
        builder = SmartConfigBuilder()
        profile, settings = builder.validator.recommend_performance_profile()
        
        assert profile == "memory_constrained"
        assert settings["max_workers"] <= 4
        
        # Test high-end system
        mock_detect.return_value = SystemResources(
            cpu_count=16,
            memory_mb=64000,
            available_disk_mb=500000
        )
        
        builder = SmartConfigBuilder()
        profile, settings = builder.validator.recommend_performance_profile()
        
        assert profile == "large_collection"
        assert settings["batch_size"] == 500