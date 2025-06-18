"""Graceful degradation strategies for maintaining functionality under failures."""

import logging
from typing import Optional, Callable, Any, Dict, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from .exceptions_extended import (
    RecoverableError,
    DatabaseError,
    ProviderError,
    ProcessingError,
    BatchProcessingError
)

logger = logging.getLogger(__name__)


@dataclass
class DegradationLevel:
    """Represents a degradation level with its constraints."""
    name: str
    description: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    disabled_features: List[str] = field(default_factory=list)
    

class GracefulDegradation:
    """Manages graceful degradation of features under failure conditions."""
    
    # Degradation levels from least to most degraded
    LEVELS = [
        DegradationLevel(
            name="normal",
            description="Full functionality",
            constraints={},
            disabled_features=[]
        ),
        DegradationLevel(
            name="reduced_parallel",
            description="Reduced parallel processing",
            constraints={
                "max_workers": 4,
                "batch_size": 50
            },
            disabled_features=[]
        ),
        DegradationLevel(
            name="sequential_only",
            description="Sequential processing only",
            constraints={
                "max_workers": 1,
                "batch_size": 1,
                "enable_batch_operations": False
            },
            disabled_features=["parallel_processing", "batch_operations"]
        ),
        DegradationLevel(
            name="basic_only",
            description="Basic functionality only",
            constraints={
                "max_workers": 1,
                "batch_size": 1,
                "enable_understanding": False,
                "enable_quality_assessment": False
            },
            disabled_features=[
                "parallel_processing",
                "batch_operations", 
                "ai_understanding",
                "quality_assessment",
                "similarity_search"
            ]
        ),
        DegradationLevel(
            name="safe_mode",
            description="Safe mode - minimal operations",
            constraints={
                "max_workers": 1,
                "batch_size": 1,
                "dry_run": True
            },
            disabled_features=[
                "parallel_processing",
                "batch_operations",
                "ai_understanding", 
                "quality_assessment",
                "similarity_search",
                "file_operations",
                "database_writes"
            ]
        )
    ]
    
    def __init__(self):
        self.current_level_index = 0
        self.degradation_history: List[Dict[str, Any]] = []
        self.feature_failures: Dict[str, int] = {}
        
    @property
    def current_level(self) -> DegradationLevel:
        """Get current degradation level."""
        return self.LEVELS[self.current_level_index]
    
    def degrade(self, reason: str, feature: Optional[str] = None) -> DegradationLevel:
        """Degrade to next level."""
        if self.current_level_index < len(self.LEVELS) - 1:
            old_level = self.current_level
            self.current_level_index += 1
            new_level = self.current_level
            
            # Track failure
            if feature:
                self.feature_failures[feature] = self.feature_failures.get(feature, 0) + 1
            
            # Log degradation
            self.degradation_history.append({
                "timestamp": datetime.now(),
                "from_level": old_level.name,
                "to_level": new_level.name,
                "reason": reason,
                "feature": feature
            })
            
            logger.warning(
                f"Degrading from '{old_level.name}' to '{new_level.name}': {reason}"
            )
            
            if new_level.disabled_features:
                logger.warning(f"Disabled features: {', '.join(new_level.disabled_features)}")
        
        return self.current_level
    
    def recover(self) -> DegradationLevel:
        """Attempt to recover to previous level."""
        if self.current_level_index > 0:
            old_level = self.current_level
            self.current_level_index -= 1
            new_level = self.current_level
            
            logger.info(f"Recovering from '{old_level.name}' to '{new_level.name}'")
            
            self.degradation_history.append({
                "timestamp": datetime.now(),
                "from_level": old_level.name,
                "to_level": new_level.name,
                "reason": "recovery_attempt",
                "feature": None
            })
        
        return self.current_level
    
    def reset(self) -> DegradationLevel:
        """Reset to normal operation."""
        self.current_level_index = 0
        self.feature_failures.clear()
        logger.info("Reset to normal operation level")
        return self.current_level
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled at current degradation level."""
        return feature not in self.current_level.disabled_features
    
    def get_constraint(self, constraint: str, default: Any = None) -> Any:
        """Get constraint value for current level."""
        return self.current_level.constraints.get(constraint, default)
    
    def should_degrade_for_feature(self, feature: str, threshold: int = 3) -> bool:
        """Check if we should degrade based on feature failures."""
        return self.feature_failures.get(feature, 0) >= threshold


class FallbackChain:
    """Chain of fallback handlers for progressive degradation."""
    
    def __init__(self):
        self.handlers: List[Tuple[str, Callable, Dict[str, Any]]] = []
    
    def add_handler(self, 
                   name: str,
                   handler: Callable,
                   constraints: Optional[Dict[str, Any]] = None) -> 'FallbackChain':
        """Add a fallback handler to the chain."""
        self.handlers.append((name, handler, constraints or {}))
        return self
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute handlers in order until one succeeds."""
        last_error = None
        
        for name, handler, constraints in self.handlers:
            try:
                logger.debug(f"Attempting handler: {name}")
                
                # Apply constraints
                constrained_kwargs = kwargs.copy()
                constrained_kwargs.update(constraints)
                
                result = handler(*args, **constrained_kwargs)
                logger.debug(f"Handler '{name}' succeeded")
                return result
                
            except Exception as e:
                logger.warning(f"Handler '{name}' failed: {e}")
                last_error = e
                continue
        
        # All handlers failed
        if last_error:
            raise last_error
        else:
            raise RuntimeError("All fallback handlers failed")


class AdaptiveProcessor:
    """Processor that adapts strategy based on failure patterns."""
    
    def __init__(self, base_config: Dict[str, Any]):
        self.base_config = base_config
        self.degradation = GracefulDegradation()
        self.success_count = 0
        self.failure_count = 0
        self.consecutive_failures = 0
        
    def process_with_adaptation(self,
                               items: List[Any],
                               process_func: Callable,
                               feature: str = "processing") -> List[Any]:
        """Process items with adaptive degradation."""
        current_config = self._get_adapted_config()
        
        try:
            # Attempt processing with current configuration
            if current_config.get("max_workers", 1) > 1:
                results = self._process_parallel(items, process_func, current_config)
            else:
                results = self._process_sequential(items, process_func)
            
            # Success - try to recover
            self._handle_success()
            return results
            
        except BatchProcessingError as e:
            # Partial failure
            self._handle_failure(e, feature)
            
            if e.failure_rate > 0.5:  # More than 50% failed
                # Degrade and retry
                logger.warning(f"High failure rate ({e.failure_rate:.1%}), degrading...")
                self.degradation.degrade(f"High failure rate: {e.failure_rate:.1%}", feature)
                return self.process_with_adaptation(items, process_func, feature)
            else:
                # Accept partial results
                return e.successful_items
                
        except Exception as e:
            # Complete failure
            self._handle_failure(e, feature)
            
            # Degrade and retry if possible
            if self.degradation.current_level_index < len(self.degradation.LEVELS) - 1:
                self.degradation.degrade(str(e), feature)
                return self.process_with_adaptation(items, process_func, feature)
            else:
                raise
    
    def _get_adapted_config(self) -> Dict[str, Any]:
        """Get configuration adapted to current degradation level."""
        config = self.base_config.copy()
        config.update(self.degradation.current_level.constraints)
        return config
    
    def _process_parallel(self, 
                         items: List[Any],
                         process_func: Callable,
                         config: Dict[str, Any]) -> List[Any]:
        """Process items in parallel."""
        # This would use the actual parallel processor
        # Simplified for example
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        failed = []
        
        with ThreadPoolExecutor(max_workers=config["max_workers"]) as executor:
            future_to_item = {
                executor.submit(process_func, item): item 
                for item in items
            }
            
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process {item}: {e}")
                    failed.append(item)
        
        if failed:
            raise PartialBatchFailure(
                batch_size=len(items),
                failed_items=failed,
                successful_items=results
            )
        
        return results
    
    def _process_sequential(self,
                           items: List[Any],
                           process_func: Callable) -> List[Any]:
        """Process items sequentially."""
        results = []
        
        for item in items:
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {item}: {e}")
                # In sequential mode, we continue on error
                continue
        
        return results
    
    def _handle_success(self) -> None:
        """Handle successful processing."""
        self.success_count += 1
        self.consecutive_failures = 0
        
        # Try to recover after sustained success
        if self.success_count % 10 == 0 and self.degradation.current_level_index > 0:
            logger.info("Attempting recovery after sustained success")
            self.degradation.recover()
    
    def _handle_failure(self, error: Exception, feature: str) -> None:
        """Handle processing failure."""
        self.failure_count += 1
        self.consecutive_failures += 1
        
        # Check if we should degrade
        if self.consecutive_failures >= 3:
            if self.degradation.should_degrade_for_feature(feature):
                self.degradation.degrade(
                    f"Repeated failures in {feature}",
                    feature
                )