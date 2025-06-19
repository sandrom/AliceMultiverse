"""Configuration validation and recommendation system."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import psutil
import shutil

from .exceptions_extended import ConfigurationValidationError
from .performance_config import PerformanceConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: Dict[str, str] = field(default_factory=dict)
    warnings: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def add_error(self, field: str, message: str) -> None:
        """Add validation error."""
        self.errors[field] = message
        self.is_valid = False
    
    def add_warning(self, field: str, message: str) -> None:
        """Add validation warning."""
        self.warnings[field] = message
    
    def add_recommendation(self, message: str) -> None:
        """Add recommendation."""
        self.recommendations.append(message)
    
    def raise_if_invalid(self) -> None:
        """Raise exception if validation failed."""
        if not self.is_valid:
            raise ConfigurationValidationError(self.errors)


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class SystemResources:
# TODO: Review unreachable code - """System resource information."""
# TODO: Review unreachable code - cpu_count: int
# TODO: Review unreachable code - memory_mb: int
# TODO: Review unreachable code - available_disk_mb: int
# TODO: Review unreachable code - has_gpu: bool = False
    
# TODO: Review unreachable code - @classmethod
# TODO: Review unreachable code - def detect(cls) -> 'SystemResources':
# TODO: Review unreachable code - """Detect system resources."""
# TODO: Review unreachable code - memory = psutil.virtual_memory()
        
# TODO: Review unreachable code - # Check for GPU (simplified - could be enhanced)
# TODO: Review unreachable code - has_gpu = False
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - import torch
# TODO: Review unreachable code - has_gpu = torch.cuda.is_available()
# TODO: Review unreachable code - except ImportError:
# TODO: Review unreachable code - pass
        
# TODO: Review unreachable code - return cls(
# TODO: Review unreachable code - cpu_count=psutil.cpu_count(logical=True),
# TODO: Review unreachable code - memory_mb=int(memory.total / 1024 / 1024),
# TODO: Review unreachable code - available_disk_mb=int(psutil.disk_usage('/').free / 1024 / 1024),
# TODO: Review unreachable code - has_gpu=has_gpu
# TODO: Review unreachable code - )


# TODO: Review unreachable code - class ConfigValidator:
# TODO: Review unreachable code - """Validates configuration and provides recommendations."""
    
# TODO: Review unreachable code - def __init__(self):
# TODO: Review unreachable code - self.system_resources = SystemResources.detect()
# TODO: Review unreachable code - logger.info(
# TODO: Review unreachable code - f"System resources: {self.system_resources.cpu_count} CPUs, "
# TODO: Review unreachable code - f"{self.system_resources.memory_mb}MB RAM, "
# TODO: Review unreachable code - f"{self.system_resources.available_disk_mb}MB disk"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
# TODO: Review unreachable code - """Validate complete configuration."""
# TODO: Review unreachable code - result = ValidationResult(is_valid=True)
        
# TODO: Review unreachable code - # Validate paths
# TODO: Review unreachable code - self._validate_paths(config.get('paths', {}), result)
        
# TODO: Review unreachable code - # Validate performance settings
# TODO: Review unreachable code - self._validate_performance(config.get('performance', {}), result)
        
# TODO: Review unreachable code - # Validate storage settings
# TODO: Review unreachable code - self._validate_storage(config.get('storage', {}), result)
        
# TODO: Review unreachable code - # Validate API keys
# TODO: Review unreachable code - self._validate_api_keys(config, result)
        
# TODO: Review unreachable code - # Validate understanding settings
# TODO: Review unreachable code - self._validate_understanding(config.get('understanding', {}), result)
        
# TODO: Review unreachable code - # Add system-specific recommendations
# TODO: Review unreachable code - self._add_recommendations(config, result)
        
# TODO: Review unreachable code - return result
    
# TODO: Review unreachable code - def _validate_paths(self, paths: Dict[str, Any], result: ValidationResult) -> None:
# TODO: Review unreachable code - """Validate path configuration."""
# TODO: Review unreachable code - # Check inbox path
# TODO: Review unreachable code - inbox_path = paths.get('inbox')
# TODO: Review unreachable code - if inbox_path:
# TODO: Review unreachable code - inbox = Path(inbox_path).expanduser()
# TODO: Review unreachable code - if not inbox.exists():
# TODO: Review unreachable code - result.add_error('paths.inbox', f"Inbox path does not exist: {inbox}")
# TODO: Review unreachable code - elif not inbox.is_dir():
# TODO: Review unreachable code - result.add_error('paths.inbox', f"Inbox path is not a directory: {inbox}")
# TODO: Review unreachable code - elif not os.access(inbox, os.R_OK):
# TODO: Review unreachable code - result.add_error('paths.inbox', f"No read permission for inbox: {inbox}")
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - result.add_error('paths.inbox', "Inbox path is required")
        
# TODO: Review unreachable code - # Check organized path
# TODO: Review unreachable code - organized_path = paths.get('organized')
# TODO: Review unreachable code - if organized_path:
# TODO: Review unreachable code - organized = Path(organized_path).expanduser()
# TODO: Review unreachable code - # Try to create if doesn't exist
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - organized.mkdir(parents=True, exist_ok=True)
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - result.add_error('paths.organized', f"Cannot create organized path: {e}")
            
# TODO: Review unreachable code - if organized.exists() and not os.access(organized, os.W_OK):
# TODO: Review unreachable code - result.add_error('paths.organized', f"No write permission for organized: {organized}")
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - result.add_error('paths.organized', "Organized path is required")
        
# TODO: Review unreachable code - # Check disk space
# TODO: Review unreachable code - if inbox_path and organized_path:
# TODO: Review unreachable code - self._check_disk_space(Path(organized_path).expanduser(), result)
    
# TODO: Review unreachable code - def _check_disk_space(self, path: Path, result: ValidationResult) -> None:
# TODO: Review unreachable code - """Check available disk space."""
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - stat = shutil.disk_usage(path.parent if not path.exists() else path)
# TODO: Review unreachable code - available_mb = stat.free / 1024 / 1024
            
# TODO: Review unreachable code - if available_mb < 100:
# TODO: Review unreachable code - result.add_error('disk_space', f"Insufficient disk space: {available_mb:.1f}MB")
# TODO: Review unreachable code - elif available_mb < 1000:
# TODO: Review unreachable code - result.add_warning('disk_space', f"Low disk space: {available_mb:.1f}MB")
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - result.add_warning('disk_space', f"Could not check disk space: {e}")
    
# TODO: Review unreachable code - def _validate_performance(self, performance: Dict[str, Any], result: ValidationResult) -> None:
# TODO: Review unreachable code - """Validate performance settings."""
# TODO: Review unreachable code - # Check worker count
# TODO: Review unreachable code - max_workers = performance.get('max_workers', 8)
# TODO: Review unreachable code - if max_workers > self.system_resources.cpu_count * 2:
# TODO: Review unreachable code - result.add_warning(
# TODO: Review unreachable code - 'performance.max_workers',
# TODO: Review unreachable code - f"max_workers ({max_workers}) exceeds 2x CPU count ({self.system_resources.cpu_count})"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Check batch size vs memory
# TODO: Review unreachable code - batch_size = performance.get('batch_size', 100)
# TODO: Review unreachable code - estimated_memory_per_file = 10  # MB, rough estimate
# TODO: Review unreachable code - estimated_batch_memory = batch_size * estimated_memory_per_file
        
# TODO: Review unreachable code - if estimated_batch_memory > self.system_resources.memory_mb * 0.5:
# TODO: Review unreachable code - result.add_warning(
# TODO: Review unreachable code - 'performance.batch_size',
# TODO: Review unreachable code - f"Large batch size ({batch_size}) may use significant memory"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Validate performance profile
# TODO: Review unreachable code - profile = performance.get('profile')
# TODO: Review unreachable code - if profile and profile not in ['default', 'fast', 'memory_constrained', 'large_collection']:
# TODO: Review unreachable code - result.add_error(
# TODO: Review unreachable code - 'performance.profile',
# TODO: Review unreachable code - f"Invalid performance profile: {profile}"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - def _validate_storage(self, storage: Dict[str, Any], result: ValidationResult) -> None:
# TODO: Review unreachable code - """Validate storage settings."""
# TODO: Review unreachable code - # Check search database path
# TODO: Review unreachable code - search_db = storage.get('search_db')
# TODO: Review unreachable code - if search_db:
# TODO: Review unreachable code - db_path = Path(search_db).expanduser()
# TODO: Review unreachable code - db_dir = db_path.parent
            
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - db_dir.mkdir(parents=True, exist_ok=True)
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - result.add_error('storage.search_db', f"Cannot create database directory: {e}")
            
# TODO: Review unreachable code - if db_dir.exists() and not os.access(db_dir, os.W_OK):
# TODO: Review unreachable code - result.add_error('storage.search_db', f"No write permission for database: {db_dir}")
        
# TODO: Review unreachable code - # Check cache settings
# TODO: Review unreachable code - cache_size = storage.get('cache_size_mb', 500)
# TODO: Review unreachable code - if cache_size > self.system_resources.memory_mb * 0.25:
# TODO: Review unreachable code - result.add_warning(
# TODO: Review unreachable code - 'storage.cache_size_mb',
# TODO: Review unreachable code - f"Large cache size ({cache_size}MB) relative to system memory"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - def _validate_api_keys(self, config: Dict[str, Any], result: ValidationResult) -> None:
# TODO: Review unreachable code - """Validate API key configuration."""
# TODO: Review unreachable code - # Check if any understanding providers are configured
# TODO: Review unreachable code - understanding = config.get('understanding', {})
# TODO: Review unreachable code - if understanding.get('enabled', False):
# TODO: Review unreachable code - providers = understanding.get('providers', [])
            
# TODO: Review unreachable code - # Check for API keys
# TODO: Review unreachable code - api_keys_found = []
# TODO: Review unreachable code - for provider in ['openai', 'anthropic', 'google']:
# TODO: Review unreachable code - if os.environ.get(f'{provider.upper()}_API_KEY'):
# TODO: Review unreachable code - api_keys_found.append(provider)
            
# TODO: Review unreachable code - if not api_keys_found and providers:
# TODO: Review unreachable code - result.add_warning(
# TODO: Review unreachable code - 'api_keys',
# TODO: Review unreachable code - "Understanding enabled but no API keys found. Run 'alice keys setup'"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - def _validate_understanding(self, understanding: Dict[str, Any], result: ValidationResult) -> None:
# TODO: Review unreachable code - """Validate understanding configuration."""
# TODO: Review unreachable code - if not understanding.get('enabled', False):
# TODO: Review unreachable code - return
        
# TODO: Review unreachable code - providers = understanding.get('providers', [])
# TODO: Review unreachable code - if not providers:
# TODO: Review unreachable code - result.add_error(
# TODO: Review unreachable code - 'understanding.providers',
# TODO: Review unreachable code - "Understanding enabled but no providers configured"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Check cost limit
# TODO: Review unreachable code - cost_limit = understanding.get('cost_limit')
# TODO: Review unreachable code - if cost_limit and cost_limit < 0:
# TODO: Review unreachable code - result.add_error(
# TODO: Review unreachable code - 'understanding.cost_limit',
# TODO: Review unreachable code - "Cost limit must be positive"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - def _add_recommendations(self, config: Dict[str, Any], result: ValidationResult) -> None:
# TODO: Review unreachable code - """Add system-specific recommendations."""
# TODO: Review unreachable code - performance = config.get('performance', {})
# TODO: Review unreachable code - current_workers = performance.get('max_workers', 8)
        
# TODO: Review unreachable code - # CPU-based recommendations
# TODO: Review unreachable code - if self.system_resources.cpu_count >= 8:
# TODO: Review unreachable code - if current_workers < self.system_resources.cpu_count:
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - f"Consider increasing max_workers to {self.system_resources.cpu_count} "
# TODO: Review unreachable code - f"to utilize all CPU cores"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Memory-based recommendations
# TODO: Review unreachable code - if self.system_resources.memory_mb >= 16000:  # 16GB+
# TODO: Review unreachable code - if performance.get('profile') != 'fast':
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - "System has ample memory - consider using 'fast' performance profile"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - elif self.system_resources.memory_mb < 8000:  # Less than 8GB
# TODO: Review unreachable code - if performance.get('profile') != 'memory_constrained':
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - "Limited memory detected - consider 'memory_constrained' profile"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Batch size recommendations
# TODO: Review unreachable code - batch_size = performance.get('batch_size', 100)
# TODO: Review unreachable code - optimal_batch = min(500, max(50, self.system_resources.memory_mb // 100))
# TODO: Review unreachable code - if abs(batch_size - optimal_batch) > 100:
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - f"Consider batch_size around {optimal_batch} for your system"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Storage recommendations
# TODO: Review unreachable code - if self.system_resources.available_disk_mb < 5000:  # Less than 5GB
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - "Low disk space - consider enabling move_files instead of copy"
# TODO: Review unreachable code - )
    
# TODO: Review unreachable code - def recommend_performance_profile(self) -> Tuple[str, Dict[str, Any]]:
# TODO: Review unreachable code - """Recommend optimal performance profile for system."""
# TODO: Review unreachable code - # Base decision on CPU and memory
# TODO: Review unreachable code - if self.system_resources.memory_mb < 4000:
# TODO: Review unreachable code - profile = "memory_constrained"
# TODO: Review unreachable code - settings = {
# TODO: Review unreachable code - "max_workers": min(4, self.system_resources.cpu_count),
# TODO: Review unreachable code - "batch_size": 50,
# TODO: Review unreachable code - "cache_size_mb": 200
# TODO: Review unreachable code - }
# TODO: Review unreachable code - elif self.system_resources.cpu_count >= 8 and self.system_resources.memory_mb >= 16000:
# TODO: Review unreachable code - profile = "fast"
# TODO: Review unreachable code - settings = {
# TODO: Review unreachable code - "max_workers": min(16, self.system_resources.cpu_count),
# TODO: Review unreachable code - "batch_size": 200,
# TODO: Review unreachable code - "cache_size_mb": 1000
# TODO: Review unreachable code - }
# TODO: Review unreachable code - elif self.system_resources.memory_mb >= 32000:
# TODO: Review unreachable code - profile = "large_collection"
# TODO: Review unreachable code - settings = {
# TODO: Review unreachable code - "max_workers": min(12, self.system_resources.cpu_count),
# TODO: Review unreachable code - "batch_size": 500,
# TODO: Review unreachable code - "cache_size_mb": 2000
# TODO: Review unreachable code - }
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - profile = "default"
# TODO: Review unreachable code - settings = {
# TODO: Review unreachable code - "max_workers": min(8, self.system_resources.cpu_count),
# TODO: Review unreachable code - "batch_size": 100,
# TODO: Review unreachable code - "cache_size_mb": 500
# TODO: Review unreachable code - }
        
# TODO: Review unreachable code - return profile, settings
    
# TODO: Review unreachable code - def validate_runtime_compatibility(self, config: Dict[str, Any]) -> ValidationResult:
# TODO: Review unreachable code - """Validate configuration compatibility at runtime."""
# TODO: Review unreachable code - result = ValidationResult(is_valid=True)
        
# TODO: Review unreachable code - # Check if current memory usage allows for configured settings
# TODO: Review unreachable code - memory = psutil.virtual_memory()
# TODO: Review unreachable code - available_mb = memory.available / 1024 / 1024
        
# TODO: Review unreachable code - performance = config.get('performance', {})
# TODO: Review unreachable code - batch_size = performance.get('batch_size', 100)
# TODO: Review unreachable code - estimated_memory_needed = batch_size * 10  # Rough estimate
        
# TODO: Review unreachable code - if estimated_memory_needed > available_mb * 0.8:
# TODO: Review unreachable code - result.add_warning(
# TODO: Review unreachable code - 'runtime.memory',
# TODO: Review unreachable code - f"Current memory usage high - only {available_mb:.0f}MB available"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - "Consider reducing batch_size or closing other applications"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - # Check CPU load
# TODO: Review unreachable code - cpu_percent = psutil.cpu_percent(interval=1)
# TODO: Review unreachable code - if cpu_percent > 80:
# TODO: Review unreachable code - result.add_warning(
# TODO: Review unreachable code - 'runtime.cpu',
# TODO: Review unreachable code - f"High CPU usage detected: {cpu_percent}%"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - result.add_recommendation(
# TODO: Review unreachable code - "Consider reducing max_workers or waiting for lower system load"
# TODO: Review unreachable code - )
        
# TODO: Review unreachable code - return result


# TODO: Review unreachable code - class SmartConfigBuilder:
# TODO: Review unreachable code - """Builds optimized configuration based on system and usage."""
    
# TODO: Review unreachable code - def __init__(self):
# TODO: Review unreachable code - self.validator = ConfigValidator()
# TODO: Review unreachable code - self.system = self.validator.system_resources
    
# TODO: Review unreachable code - def build_config(self,
# TODO: Review unreachable code - base_config: Dict[str, Any],
# TODO: Review unreachable code - use_case: Optional[str] = None) -> Dict[str, Any]:
# TODO: Review unreachable code - """Build optimized configuration for use case."""
# TODO: Review unreachable code - config = base_config.copy()
        
# TODO: Review unreachable code - # Get recommended profile
# TODO: Review unreachable code - profile, settings = self.validator.recommend_performance_profile()
        
# TODO: Review unreachable code - # Apply use case specific adjustments
# TODO: Review unreachable code - if use_case == "quick_scan":
# TODO: Review unreachable code - settings["batch_size"] = min(50, settings["batch_size"])
# TODO: Review unreachable code - settings["enable_understanding"] = False
# TODO: Review unreachable code - elif use_case == "full_analysis":
# TODO: Review unreachable code - settings["enable_understanding"] = True
# TODO: Review unreachable code - settings["batch_size"] = min(100, settings["batch_size"])
# TODO: Review unreachable code - elif use_case == "bulk_import":
# TODO: Review unreachable code - settings["batch_size"] = min(1000, settings["batch_size"] * 2)
# TODO: Review unreachable code - settings["enable_batch_operations"] = True
        
# TODO: Review unreachable code - # Update config
# TODO: Review unreachable code - if 'performance' not in config:
# TODO: Review unreachable code - config['performance'] = {}
        
# TODO: Review unreachable code - config['performance'].update(settings)
# TODO: Review unreachable code - config['performance']['profile'] = profile
        
# TODO: Review unreachable code - logger.info(f"Built config with profile '{profile}' for use case '{use_case}'")
        
# TODO: Review unreachable code - return config
    
# TODO: Review unreachable code - def optimize_for_collection_size(self,
# TODO: Review unreachable code - config: Dict[str, Any],
# TODO: Review unreachable code - file_count: int) -> Dict[str, Any]:
# TODO: Review unreachable code - """Optimize configuration based on collection size."""
# TODO: Review unreachable code - config = config.copy()
        
# TODO: Review unreachable code - if file_count < 100:
# TODO: Review unreachable code - # Small collection - prioritize quality
# TODO: Review unreachable code - config['performance']['max_workers'] = min(4, self.system.cpu_count)
# TODO: Review unreachable code - config['performance']['batch_size'] = 10
# TODO: Review unreachable code - elif file_count < 1000:
# TODO: Review unreachable code - # Medium collection - balanced
# TODO: Review unreachable code - config['performance']['max_workers'] = min(8, self.system.cpu_count)
# TODO: Review unreachable code - config['performance']['batch_size'] = 50
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - # Large collection - prioritize throughput
# TODO: Review unreachable code - config['performance']['max_workers'] = self.system.cpu_count
# TODO: Review unreachable code - config['performance']['batch_size'] = 200
# TODO: Review unreachable code - config['performance']['enable_batch_operations'] = True
        
# TODO: Review unreachable code - return config