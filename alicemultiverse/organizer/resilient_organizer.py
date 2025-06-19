"""Resilient media organizer with comprehensive error recovery."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..core.performance_config import PerformanceConfig, get_performance_config
from ..core.graceful_degradation import GracefulDegradation, AdaptiveProcessor
from ..core.error_recovery import ErrorRecovery, DeadLetterQueue, CircuitBreaker
from ..core.exceptions_extended import (
    BatchProcessingError,
    PartialBatchFailure,
    DatabaseError,
    InsufficientDiskSpaceError
)
from ..monitoring.tracker import (
    PerformanceTracker,
    track_operation,
    update_worker_metrics
)
from .components.organizer import MediaOrganizer
from .components.process_file_enhanced import EnhancedProcessFileMixin

logger = logging.getLogger(__name__)


class ResilientMediaOrganizer(MediaOrganizer, EnhancedProcessFileMixin):
    """Media organizer with comprehensive error recovery and resilience."""
    
    def __init__(self, config=None):
        """Initialize resilient organizer with enhanced error handling."""
        super().__init__(config)
        
        # Error recovery components
        self.degradation = GracefulDegradation()
        self.dead_letter_queue = DeadLetterQueue("failed_files")
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=300.0,  # 5 minutes
            expected_exception=DatabaseError
        )
        
        # Adaptive processor for dynamic configuration
        self.adaptive_processor = AdaptiveProcessor({
            "max_workers": self.perf_config.max_workers,
            "batch_size": self.perf_config.batch_size,
            "enable_batch_operations": self.perf_config.enable_batch_operations
        })
        
        # Track component health
        self.component_health = {
            "database": True,
            "cache": True,
            "parallel_processing": True,
            "batch_operations": True,
            "understanding": True
        }
    
    def organize(self, watch: bool = False) -> 'Statistics':
        """Organize media files with resilient error handling."""
        if watch:
            return self._watch_and_organize_resilient()
        
        # TODO: Review unreachable code - with track_operation("organize.resilient"):
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - # Pre-flight checks
        # TODO: Review unreachable code - self._perform_preflight_checks()
                
        # TODO: Review unreachable code - # Find all media files
        # TODO: Review unreachable code - media_files = list(self._find_media_files())
        # TODO: Review unreachable code - logger.info(f"Found {len(media_files)} media files to process")
                
        # TODO: Review unreachable code - if not media_files:
        # TODO: Review unreachable code - return self.stats
                
        # TODO: Review unreachable code - # Process with adaptive strategy
        # TODO: Review unreachable code - self._organize_with_adaptation(media_files)
                
        # TODO: Review unreachable code - # Handle any items in dead letter queue
        # TODO: Review unreachable code - self._process_dead_letter_queue()
                
        # TODO: Review unreachable code - self._log_statistics()
        # TODO: Review unreachable code - return self.stats
                
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Critical error during organization: {e}")
        # TODO: Review unreachable code - self._handle_critical_failure(e)
        # TODO: Review unreachable code - raise
    
    def _perform_preflight_checks(self) -> None:
        """Perform pre-flight checks before processing."""
        with track_operation("organize.preflight"):
            # Check disk space
            self._check_disk_space()
            
            # Test database connection
            self._test_database_connection()
            
            # Validate configuration
            self._validate_configuration()
    
    def _check_disk_space(self) -> None:
        """Check available disk space."""
        try:
            import shutil
            stat = shutil.disk_usage(self.output_dir)
            available_mb = stat.free / 1024 / 1024
            
            if available_mb < 100:  # Less than 100MB
                raise InsufficientDiskSpaceError(
                    required_bytes=100 * 1024 * 1024,
                    available_bytes=stat.free
                )
            elif available_mb < 1000:  # Less than 1GB
                logger.warning(f"Low disk space: {available_mb:.1f}MB available")
                
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
    
    def _test_database_connection(self) -> None:
        """Test database connection and degrade if necessary."""
        if not self.component_health["database"]:
            return
        
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - with self.circuit_breaker:
        # TODO: Review unreachable code - # Simple query to test connection
        # TODO: Review unreachable code - if hasattr(self.search_db, 'execute'):
        # TODO: Review unreachable code - self.search_db.execute("SELECT 1")
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Database connection test failed: {e}")
        # TODO: Review unreachable code - self.component_health["database"] = False
        # TODO: Review unreachable code - self.degradation.degrade("Database unavailable", "database")
    
    def _validate_configuration(self) -> None:
        """Validate configuration and adjust if needed."""
        # Adjust configuration based on degradation level
        constraints = self.degradation.current_level.constraints
        
        if constraints is not None and "max_workers" in constraints:
            self.perf_config.max_workers = constraints["max_workers"]
            update_worker_metrics(0, constraints["max_workers"])
        
        if constraints is not None and "batch_size" in constraints:
            self.perf_config.batch_size = constraints["batch_size"]
        
        if constraints is not None and "enable_batch_operations" in constraints:
            self.batch_operations_enabled = constraints["enable_batch_operations"]
    
    def _organize_with_adaptation(self, media_files: List[Path]) -> None:
        """Organize files with adaptive strategy."""
        # Let adaptive processor handle the organization
        try:
            self.adaptive_processor.process_with_adaptation(
                media_files,
                self._process_file_resilient,
                "file_processing"
            )
        except PartialBatchFailure as e:
            # Handle partial failure
            logger.warning(f"Partial batch failure: {len(e.failed_items)} files failed")
            
            # Add failed items to dead letter queue
            for item in e.failed_items:
                self.dead_letter_queue.add(item, e, 1)
            
            # Update statistics for successful items
            self.stats["processed"] = len(e.successful_items)
            self.stats["failed"] = len(e.failed_items)
    
    def _process_file_resilient(self, media_path: Path) -> Dict[str, Any]:
        """Process file with full resilience."""
        # TODO: Review unreachable code - try:
            # Use enhanced processing with recovery
        result = self._process_file_with_recovery(media_path)
            
            # Update statistics
        self._update_statistics(result)
            
            # Update component health based on result
        self._update_component_health(result)
            
        return result
            
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Failed to process {media_path}: {e}")
            
        # TODO: Review unreachable code - # Check if we should degrade
        # TODO: Review unreachable code - if self._should_degrade_component(e):
        # TODO: Review unreachable code - self._degrade_component(e)
            
        # TODO: Review unreachable code - raise
    
    def _should_degrade_component(self, error: Exception) -> bool:
        """Determine if we should degrade a component."""
        if isinstance(error, DatabaseError):
            return self.component_health["database"]
        # TODO: Review unreachable code - elif "parallel" in str(error).lower():
        # TODO: Review unreachable code - return self.component_health["parallel_processing"]
        # TODO: Review unreachable code - elif "batch" in str(error).lower():
        # TODO: Review unreachable code - return self.component_health["batch_operations"]
        # TODO: Review unreachable code - return False
    
    def _degrade_component(self, error: Exception) -> None:
        """Degrade specific component based on error."""
        if isinstance(error, DatabaseError):
            self.component_health["database"] = False
            self.degradation.degrade("Database errors", "database")
            # Disable batch operations if database is down
            self.batch_operations_enabled = False
    
    def _update_component_health(self, result: Dict[str, Any]) -> None:
        """Update component health based on processing result."""
        if result.get("status") == "success":
            # Successful operation might indicate recovery
            if not self.component_health["database"] and result.get("database_used"):
                logger.info("Database appears to be working again")
                self.component_health["database"] = True
                self.circuit_breaker.reset()
    
    def _process_dead_letter_queue(self) -> None:
        """Process items in dead letter queue."""
        if not self.dead_letter_queue.items:
            return
        
        # TODO: Review unreachable code - logger.info(f"Processing {len(self.dead_letter_queue.items)} items from dead letter queue")
        
        # TODO: Review unreachable code - # Save failed items for manual inspection
        # TODO: Review unreachable code - failed_items_path = self.output_dir / "failed_items.json"
        # TODO: Review unreachable code - self.dead_letter_queue.save_to_file(failed_items_path)
        
        # TODO: Review unreachable code - # Optionally retry with most degraded settings
        # TODO: Review unreachable code - if self.config.get("retry_failed_items", False):
        # TODO: Review unreachable code - with self.degradation.LEVELS[-1]:  # Use safe mode
        # TODO: Review unreachable code - successful, still_failed = self.dead_letter_queue.retry_all(
        # TODO: Review unreachable code - self._process_file_resilient
        # TODO: Review unreachable code - )
                
        # TODO: Review unreachable code - if successful:
        # TODO: Review unreachable code - logger.info(f"Successfully recovered {len(successful)} items")
                
        # TODO: Review unreachable code - if still_failed:
        # TODO: Review unreachable code - logger.error(f"{len(still_failed)} items still failed after retry")
    
    def _watch_and_organize_resilient(self) -> 'Statistics':
        """Watch mode with resilient processing."""
        logger.info("Starting resilient watch mode...")
        
        try:
            while True:
                # Reset circuit breaker periodically
                self.circuit_breaker.reset()
                
                # Process new files
                new_files = self._find_new_files_for_watch()
                if new_files:
                    self._organize_with_adaptation(new_files)
                
                # Sleep before next check
                time.sleep(self.config.get("watch_interval", 5))
                
        except KeyboardInterrupt:
            logger.info("Watch mode stopped by user")
            self._process_dead_letter_queue()
            return self.stats
    
    # TODO: Review unreachable code - def _handle_critical_failure(self, error: Exception) -> None:
    # TODO: Review unreachable code - """Handle critical failures that stop processing."""
    # TODO: Review unreachable code - # Save current state
    # TODO: Review unreachable code - state_file = self.output_dir / "organizer_state.json"
        
    # TODO: Review unreachable code - import json
    # TODO: Review unreachable code - state = {
    # TODO: Review unreachable code - "error": str(error),
    # TODO: Review unreachable code - "error_type": type(error).__name__,
    # TODO: Review unreachable code - "degradation_level": self.degradation.current_level.name,
    # TODO: Review unreachable code - "component_health": self.component_health,
    # TODO: Review unreachable code - "statistics": dict(self.stats),
    # TODO: Review unreachable code - "failed_items": len(self.dead_letter_queue.items)
    # TODO: Review unreachable code - }
        
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(state_file, 'w') as f:
    # TODO: Review unreachable code - json.dump(state, f, indent=2)
    # TODO: Review unreachable code - logger.info(f"Saved failure state to {state_file}")
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Could not save failure state: {e}")
        
    # TODO: Review unreachable code - # Save dead letter queue
    # TODO: Review unreachable code - if self.dead_letter_queue.items:
    # TODO: Review unreachable code - self._process_dead_letter_queue()
    
    # TODO: Review unreachable code - def get_health_report(self) -> Dict[str, Any]:
    # TODO: Review unreachable code - """Get current health report of the organizer."""
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "degradation_level": self.degradation.current_level.name,
    # TODO: Review unreachable code - "component_health": self.component_health.copy(),
    # TODO: Review unreachable code - "circuit_breaker_state": self.circuit_breaker.state,
    # TODO: Review unreachable code - "dead_letter_queue_size": len(self.dead_letter_queue.items),
    # TODO: Review unreachable code - "failure_history": self.degradation.degradation_history[-10:],  # Last 10 events
    # TODO: Review unreachable code - "feature_failures": self.degradation.feature_failures.copy()
    # TODO: Review unreachable code - }