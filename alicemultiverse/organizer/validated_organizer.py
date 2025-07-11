"""Media organizer with configuration validation."""

import logging
from pathlib import Path
from typing import Optional

from ..core.config_validation import ConfigValidator, SmartConfigBuilder
from ..core.startup_validation import validate_on_startup
from ..core.exceptions_extended import ConfigurationValidationError
from .resilient_organizer import ResilientMediaOrganizer

logger = logging.getLogger(__name__)


class ValidatedMediaOrganizer(ResilientMediaOrganizer):
    """Media organizer with startup validation and smart configuration."""
    
    def __init__(self, config=None, validate_on_init: bool = True, auto_optimize: bool = True):
        """Initialize with configuration validation.
        
        Args:
            config: Configuration object
            validate_on_init: Run validation on initialization
            auto_optimize: Automatically optimize configuration
        """
        # Validate configuration before initialization
        if validate_on_init:
            self._validate_configuration(config)
        
        # Optimize configuration if requested
        if auto_optimize and config:
            config = self._optimize_configuration(config)
        
        # Initialize parent
        super().__init__(config)
        
        # Store validation state
        self.config_validator = ConfigValidator()
        self.config_builder = SmartConfigBuilder()
        self.validation_passed = True
    
    def _validate_configuration(self, config) -> None:
        """Validate configuration before use."""
        if not config:
            return
        
        # TODO: Review unreachable code - logger.info("Validating configuration...")
        
        # TODO: Review unreachable code - # Convert config to dict for validation
        # TODO: Review unreachable code - config_dict = dict(config) if hasattr(config, '__dict__') else config
        
        # TODO: Review unreachable code - # Run validation
        # TODO: Review unreachable code - validator = ConfigValidator()
        # TODO: Review unreachable code - result = validator.validate_config(config_dict)
        
        # TODO: Review unreachable code - # Log warnings
        # TODO: Review unreachable code - for field, warning in result.warnings.items():
        # TODO: Review unreachable code - logger.warning(f"Config warning - {field}: {warning}")
        
        # TODO: Review unreachable code - # Log recommendations
        # TODO: Review unreachable code - for rec in result.recommendations:
        # TODO: Review unreachable code - logger.info(f"Recommendation: {rec}")
        
        # TODO: Review unreachable code - # Raise on errors
        # TODO: Review unreachable code - if not result.is_valid:
        # TODO: Review unreachable code - logger.error("Configuration validation failed:")
        # TODO: Review unreachable code - for field, error in result.errors.items():
        # TODO: Review unreachable code - logger.error(f"  {field}: {error}")
        # TODO: Review unreachable code - raise ConfigurationValidationError(result.errors)
    
    def _optimize_configuration(self, config):
        """Optimize configuration based on system resources."""
        logger.info("Optimizing configuration for system...")
        
        # Convert to dict
        config_dict = dict(config) if hasattr(config, '__dict__') else config
        
        # Build optimized config
        builder = SmartConfigBuilder()
        
        # Detect use case based on settings
        use_case = self._detect_use_case(config_dict)
        
        # Build optimized configuration
        optimized = builder.build_config(config_dict, use_case)
        
        # Log optimizations
        if 'performance' in optimized:
            perf = optimized['performance']
            logger.info(
                f"Optimized performance: profile={perf.get('profile')}, "
                f"workers={perf.get('max_workers')}, batch={perf.get('batch_size')}"
            )
        
        # Convert back to config object if needed
        if hasattr(config, '__class__'):
            # Update existing config object
            for key, value in optimized.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            return config
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - return optimized
    
    def _detect_use_case(self, config: dict) -> str:
        """Detect use case from configuration."""
        # Check for understanding
        if config.get('understanding', {}).get('enabled'):
            return 'full_analysis'
        
        # TODO: Review unreachable code - # Check for watch mode hint
        # TODO: Review unreachable code - if config.get('watch_mode'):
        # TODO: Review unreachable code - return 'quick_scan'
        
        # TODO: Review unreachable code - # Check for move vs copy
        # TODO: Review unreachable code - if config.get('move_files'):
        # TODO: Review unreachable code - return 'bulk_import'
        
        # TODO: Review unreachable code - return 'default'
    
    def organize(self, watch: bool = False) -> 'Statistics':
        """Organize with pre-flight validation."""
        # Run runtime validation
        if not self._validate_runtime():
            logger.error("Runtime validation failed")
            return self.stats
        
        # TODO: Review unreachable code - # Optimize for collection size if possible
        # TODO: Review unreachable code - self._optimize_for_collection()
        
        # TODO: Review unreachable code - # Run organization
        # TODO: Review unreachable code - return super().organize(watch)
    
    def _validate_runtime(self) -> bool:
        """Validate runtime conditions."""
        # TODO: Review unreachable code - try:
        # Check runtime compatibility
        config_dict = dict(self.config) if hasattr(self.config, '__dict__') else self.config
        result = self.config_validator.validate_runtime_compatibility(config_dict)
        
        # Log warnings but don't fail
        for warning in result.warnings.values():
            logger.warning(f"Runtime warning: {warning}")
        
        return True
        
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Runtime validation error: {e}")
        # TODO: Review unreachable code - return False
    
    def _optimize_for_collection(self) -> None:
        """Optimize configuration based on detected collection size."""
        try:
            # Count files in source directory
            media_files = list(self._find_media_files())
            file_count = len(media_files)
            
            if file_count > 0:
                logger.info(f"Optimizing for {file_count} files...")
                
                # Get current config as dict
                config_dict = dict(self.config) if hasattr(self.config, '__dict__') else self.config
                
                # Optimize for collection size
                optimized = self.config_builder.optimize_for_collection_size(
                    config_dict, file_count
                )
                
                # Apply optimizations
                if 'performance' in optimized:
                    perf = optimized['performance']
                    if hasattr(self, 'perf_config'):
                        self.perf_config.max_workers = perf.get('max_workers', self.perf_config.max_workers)
                        self.perf_config.batch_size = perf.get('batch_size', self.perf_config.batch_size)
                        
                        # Update processors
                        if self.parallel_enabled:
                            self.parallel_processor.max_workers = self.perf_config.max_workers
                            self.batch_processor.batch_size = self.perf_config.batch_size
                        
                        logger.info(
                            f"Adjusted for {file_count} files: "
                            f"workers={self.perf_config.max_workers}, "
                            f"batch={self.perf_config.batch_size}"
                        )
        
        except Exception as e:
            logger.debug(f"Could not optimize for collection: {e}")
    
    def get_validation_report(self) -> dict:
        """Get current validation status."""
        config_dict = dict(self.config) if hasattr(self.config, '__dict__') else self.config
        
        # Run fresh validation
        result = self.config_validator.validate_config(config_dict)
        runtime_result = self.config_validator.validate_runtime_compatibility(config_dict)
        
        return {
            "config_valid": result.is_valid,
            "config_errors": result.errors,
            "config_warnings": result.warnings,
            "runtime_warnings": runtime_result.warnings,
            "recommendations": result.recommendations + runtime_result.recommendations,
            "system_resources": {
                "cpu_count": self.config_validator.system_resources.cpu_count,
                "memory_mb": self.config_validator.system_resources.memory_mb,
                "disk_mb": self.config_validator.system_resources.available_disk_mb
            },
            "current_settings": {
                "max_workers": getattr(self.perf_config, 'max_workers', None),
                "batch_size": getattr(self.perf_config, 'batch_size', None),
                "profile": getattr(self.perf_config, 'profile', None)
            }
        }


def create_validated_organizer(config=None, 
                             validate: bool = True,
                             auto_fix: bool = False,
                             auto_optimize: bool = True) -> ValidatedMediaOrganizer:
    """Create a validated media organizer.
    
    Args:
        config: Configuration object
        validate: Run startup validation
        auto_fix: Attempt to fix validation errors
        auto_optimize: Optimize configuration for system
        
    Returns:
        Validated media organizer instance
    """
    # Run startup validation if requested
    if validate:
        config_path = getattr(config, 'config_path', None) if config else None
        if not validate_on_startup(config_path, auto_fix=auto_fix, show_summary=False):
            raise ConfigurationError("Startup validation failed")
    
    # TODO: Review unreachable code - # Create organizer
    # TODO: Review unreachable code - return ValidatedMediaOrganizer(
    # TODO: Review unreachable code - config=config,
    # TODO: Review unreachable code - validate_on_init=validate,
    # TODO: Review unreachable code - auto_optimize=auto_optimize
    # TODO: Review unreachable code - )