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


@dataclass
class SystemResources:
    """System resource information."""
    cpu_count: int
    memory_mb: int
    available_disk_mb: int
    has_gpu: bool = False
    
    @classmethod
    def detect(cls) -> 'SystemResources':
        """Detect system resources."""
        memory = psutil.virtual_memory()
        
        # Check for GPU (simplified - could be enhanced)
        has_gpu = False
        try:
            import torch
            has_gpu = torch.cuda.is_available()
        except ImportError:
            pass
        
        return cls(
            cpu_count=psutil.cpu_count(logical=True),
            memory_mb=int(memory.total / 1024 / 1024),
            available_disk_mb=int(psutil.disk_usage('/').free / 1024 / 1024),
            has_gpu=has_gpu
        )


class ConfigValidator:
    """Validates configuration and provides recommendations."""
    
    def __init__(self):
        self.system_resources = SystemResources.detect()
        logger.info(
            f"System resources: {self.system_resources.cpu_count} CPUs, "
            f"{self.system_resources.memory_mb}MB RAM, "
            f"{self.system_resources.available_disk_mb}MB disk"
        )
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate complete configuration."""
        result = ValidationResult(is_valid=True)
        
        # Validate paths
        self._validate_paths(config.get('paths', {}), result)
        
        # Validate performance settings
        self._validate_performance(config.get('performance', {}), result)
        
        # Validate storage settings
        self._validate_storage(config.get('storage', {}), result)
        
        # Validate API keys
        self._validate_api_keys(config, result)
        
        # Validate understanding settings
        self._validate_understanding(config.get('understanding', {}), result)
        
        # Add system-specific recommendations
        self._add_recommendations(config, result)
        
        return result
    
    def _validate_paths(self, paths: Dict[str, Any], result: ValidationResult) -> None:
        """Validate path configuration."""
        # Check inbox path
        inbox_path = paths.get('inbox')
        if inbox_path:
            inbox = Path(inbox_path).expanduser()
            if not inbox.exists():
                result.add_error('paths.inbox', f"Inbox path does not exist: {inbox}")
            elif not inbox.is_dir():
                result.add_error('paths.inbox', f"Inbox path is not a directory: {inbox}")
            elif not os.access(inbox, os.R_OK):
                result.add_error('paths.inbox', f"No read permission for inbox: {inbox}")
        else:
            result.add_error('paths.inbox', "Inbox path is required")
        
        # Check organized path
        organized_path = paths.get('organized')
        if organized_path:
            organized = Path(organized_path).expanduser()
            # Try to create if doesn't exist
            try:
                organized.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                result.add_error('paths.organized', f"Cannot create organized path: {e}")
            
            if organized.exists() and not os.access(organized, os.W_OK):
                result.add_error('paths.organized', f"No write permission for organized: {organized}")
        else:
            result.add_error('paths.organized', "Organized path is required")
        
        # Check disk space
        if inbox_path and organized_path:
            self._check_disk_space(Path(organized_path).expanduser(), result)
    
    def _check_disk_space(self, path: Path, result: ValidationResult) -> None:
        """Check available disk space."""
        try:
            stat = shutil.disk_usage(path.parent if not path.exists() else path)
            available_mb = stat.free / 1024 / 1024
            
            if available_mb < 100:
                result.add_error('disk_space', f"Insufficient disk space: {available_mb:.1f}MB")
            elif available_mb < 1000:
                result.add_warning('disk_space', f"Low disk space: {available_mb:.1f}MB")
        except Exception as e:
            result.add_warning('disk_space', f"Could not check disk space: {e}")
    
    def _validate_performance(self, performance: Dict[str, Any], result: ValidationResult) -> None:
        """Validate performance settings."""
        # Check worker count
        max_workers = performance.get('max_workers', 8)
        if max_workers > self.system_resources.cpu_count * 2:
            result.add_warning(
                'performance.max_workers',
                f"max_workers ({max_workers}) exceeds 2x CPU count ({self.system_resources.cpu_count})"
            )
        
        # Check batch size vs memory
        batch_size = performance.get('batch_size', 100)
        estimated_memory_per_file = 10  # MB, rough estimate
        estimated_batch_memory = batch_size * estimated_memory_per_file
        
        if estimated_batch_memory > self.system_resources.memory_mb * 0.5:
            result.add_warning(
                'performance.batch_size',
                f"Large batch size ({batch_size}) may use significant memory"
            )
        
        # Validate performance profile
        profile = performance.get('profile')
        if profile and profile not in ['default', 'fast', 'memory_constrained', 'large_collection']:
            result.add_error(
                'performance.profile',
                f"Invalid performance profile: {profile}"
            )
    
    def _validate_storage(self, storage: Dict[str, Any], result: ValidationResult) -> None:
        """Validate storage settings."""
        # Check search database path
        search_db = storage.get('search_db')
        if search_db:
            db_path = Path(search_db).expanduser()
            db_dir = db_path.parent
            
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                result.add_error('storage.search_db', f"Cannot create database directory: {e}")
            
            if db_dir.exists() and not os.access(db_dir, os.W_OK):
                result.add_error('storage.search_db', f"No write permission for database: {db_dir}")
        
        # Check cache settings
        cache_size = storage.get('cache_size_mb', 500)
        if cache_size > self.system_resources.memory_mb * 0.25:
            result.add_warning(
                'storage.cache_size_mb',
                f"Large cache size ({cache_size}MB) relative to system memory"
            )
    
    def _validate_api_keys(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate API key configuration."""
        # Check if any understanding providers are configured
        understanding = config.get('understanding', {})
        if understanding.get('enabled', False):
            providers = understanding.get('providers', [])
            
            # Check for API keys
            api_keys_found = []
            for provider in ['openai', 'anthropic', 'google']:
                if os.environ.get(f'{provider.upper()}_API_KEY'):
                    api_keys_found.append(provider)
            
            if not api_keys_found and providers:
                result.add_warning(
                    'api_keys',
                    "Understanding enabled but no API keys found. Run 'alice keys setup'"
                )
    
    def _validate_understanding(self, understanding: Dict[str, Any], result: ValidationResult) -> None:
        """Validate understanding configuration."""
        if not understanding.get('enabled', False):
            return
        
        providers = understanding.get('providers', [])
        if not providers:
            result.add_error(
                'understanding.providers',
                "Understanding enabled but no providers configured"
            )
        
        # Check cost limit
        cost_limit = understanding.get('cost_limit')
        if cost_limit and cost_limit < 0:
            result.add_error(
                'understanding.cost_limit',
                "Cost limit must be positive"
            )
    
    def _add_recommendations(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """Add system-specific recommendations."""
        performance = config.get('performance', {})
        current_workers = performance.get('max_workers', 8)
        
        # CPU-based recommendations
        if self.system_resources.cpu_count >= 8:
            if current_workers < self.system_resources.cpu_count:
                result.add_recommendation(
                    f"Consider increasing max_workers to {self.system_resources.cpu_count} "
                    f"to utilize all CPU cores"
                )
        
        # Memory-based recommendations
        if self.system_resources.memory_mb >= 16000:  # 16GB+
            if performance.get('profile') != 'fast':
                result.add_recommendation(
                    "System has ample memory - consider using 'fast' performance profile"
                )
        elif self.system_resources.memory_mb < 8000:  # Less than 8GB
            if performance.get('profile') != 'memory_constrained':
                result.add_recommendation(
                    "Limited memory detected - consider 'memory_constrained' profile"
                )
        
        # Batch size recommendations
        batch_size = performance.get('batch_size', 100)
        optimal_batch = min(500, max(50, self.system_resources.memory_mb // 100))
        if abs(batch_size - optimal_batch) > 100:
            result.add_recommendation(
                f"Consider batch_size around {optimal_batch} for your system"
            )
        
        # Storage recommendations
        if self.system_resources.available_disk_mb < 5000:  # Less than 5GB
            result.add_recommendation(
                "Low disk space - consider enabling move_files instead of copy"
            )
    
    def recommend_performance_profile(self) -> Tuple[str, Dict[str, Any]]:
        """Recommend optimal performance profile for system."""
        # Base decision on CPU and memory
        if self.system_resources.memory_mb < 4000:
            profile = "memory_constrained"
            settings = {
                "max_workers": min(4, self.system_resources.cpu_count),
                "batch_size": 50,
                "cache_size_mb": 200
            }
        elif self.system_resources.cpu_count >= 8 and self.system_resources.memory_mb >= 16000:
            profile = "fast"
            settings = {
                "max_workers": min(16, self.system_resources.cpu_count),
                "batch_size": 200,
                "cache_size_mb": 1000
            }
        elif self.system_resources.memory_mb >= 32000:
            profile = "large_collection"
            settings = {
                "max_workers": min(12, self.system_resources.cpu_count),
                "batch_size": 500,
                "cache_size_mb": 2000
            }
        else:
            profile = "default"
            settings = {
                "max_workers": min(8, self.system_resources.cpu_count),
                "batch_size": 100,
                "cache_size_mb": 500
            }
        
        return profile, settings
    
    def validate_runtime_compatibility(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration compatibility at runtime."""
        result = ValidationResult(is_valid=True)
        
        # Check if current memory usage allows for configured settings
        memory = psutil.virtual_memory()
        available_mb = memory.available / 1024 / 1024
        
        performance = config.get('performance', {})
        batch_size = performance.get('batch_size', 100)
        estimated_memory_needed = batch_size * 10  # Rough estimate
        
        if estimated_memory_needed > available_mb * 0.8:
            result.add_warning(
                'runtime.memory',
                f"Current memory usage high - only {available_mb:.0f}MB available"
            )
            result.add_recommendation(
                "Consider reducing batch_size or closing other applications"
            )
        
        # Check CPU load
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            result.add_warning(
                'runtime.cpu',
                f"High CPU usage detected: {cpu_percent}%"
            )
            result.add_recommendation(
                "Consider reducing max_workers or waiting for lower system load"
            )
        
        return result


class SmartConfigBuilder:
    """Builds optimized configuration based on system and usage."""
    
    def __init__(self):
        self.validator = ConfigValidator()
        self.system = self.validator.system_resources
    
    def build_config(self,
                    base_config: Dict[str, Any],
                    use_case: Optional[str] = None) -> Dict[str, Any]:
        """Build optimized configuration for use case."""
        config = base_config.copy()
        
        # Get recommended profile
        profile, settings = self.validator.recommend_performance_profile()
        
        # Apply use case specific adjustments
        if use_case == "quick_scan":
            settings["batch_size"] = min(50, settings["batch_size"])
            settings["enable_understanding"] = False
        elif use_case == "full_analysis":
            settings["enable_understanding"] = True
            settings["batch_size"] = min(100, settings["batch_size"])
        elif use_case == "bulk_import":
            settings["batch_size"] = min(1000, settings["batch_size"] * 2)
            settings["enable_batch_operations"] = True
        
        # Update config
        if 'performance' not in config:
            config['performance'] = {}
        
        config['performance'].update(settings)
        config['performance']['profile'] = profile
        
        logger.info(f"Built config with profile '{profile}' for use case '{use_case}'")
        
        return config
    
    def optimize_for_collection_size(self,
                                   config: Dict[str, Any],
                                   file_count: int) -> Dict[str, Any]:
        """Optimize configuration based on collection size."""
        config = config.copy()
        
        if file_count < 100:
            # Small collection - prioritize quality
            config['performance']['max_workers'] = min(4, self.system.cpu_count)
            config['performance']['batch_size'] = 10
        elif file_count < 1000:
            # Medium collection - balanced
            config['performance']['max_workers'] = min(8, self.system.cpu_count)
            config['performance']['batch_size'] = 50
        else:
            # Large collection - prioritize throughput
            config['performance']['max_workers'] = self.system.cpu_count
            config['performance']['batch_size'] = 200
            config['performance']['enable_batch_operations'] = True
        
        return config