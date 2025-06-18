"""Performance tracking integration for AliceMultiverse components."""

import time
import functools
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Callable, Any, TypeVar, cast
from datetime import datetime

from .metrics import MetricsCollector

# Type variable for decorators
F = TypeVar('F', bound=Callable[..., Any])


class PerformanceTracker:
    """Track performance metrics throughout the application."""
    
    def __init__(self):
        self.collector = MetricsCollector.get_instance()
    
    @contextmanager
    def track_file_processing(self, file_path: Path):
        """Track processing of a single file."""
        start_time = time.time()
        try:
            yield
        except Exception:
            self.collector.record_error()
            raise
        finally:
            processing_time = time.time() - start_time
            self.collector.record_file_processed(file_path, processing_time)
    
    @contextmanager
    def track_database_operation(self):
        """Track a database operation."""
        start_time = time.time()
        try:
            yield
        finally:
            operation_time = time.time() - start_time
            self.collector.record_database_operation(operation_time)
    
    @contextmanager
    def track_operation(self, operation_name: str):
        """Track a named operation."""
        start_time = time.time()
        try:
            yield
        finally:
            operation_time = time.time() - start_time
            self.collector.record_operation_time(operation_name, operation_time)
    
    def track_cache_access(self, hit: bool) -> None:
        """Track cache hit or miss."""
        if hit:
            self.collector.record_cache_hit()
        else:
            self.collector.record_cache_miss()
    
    def update_worker_metrics(self, active_workers: int, max_workers: int) -> None:
        """Update worker thread metrics."""
        self.collector.update_worker_count(active_workers, max_workers)
    
    def update_queue_depth(self, depth: int) -> None:
        """Update processing queue depth."""
        self.collector.update_queue_depth(depth)
    
    @staticmethod
    def track_method(operation_name: Optional[str] = None) -> Callable[[F], F]:
        """Decorator to track method execution time."""
        def decorator(func: F) -> F:
            tracker = PerformanceTracker()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with tracker.track_operation(op_name):
                    return func(*args, **kwargs)
            
            return cast(F, wrapper)
        return decorator
    
    @staticmethod
    def track_db_method(func: F) -> F:
        """Decorator to track database method execution."""
        tracker = PerformanceTracker()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tracker.track_database_operation():
                return func(*args, **kwargs)
        
        return cast(F, wrapper)


# Global tracker instance
_tracker = PerformanceTracker()


def get_tracker() -> PerformanceTracker:
    """Get the global performance tracker."""
    return _tracker


# Convenience functions
def track_file_processing(file_path: Path):
    """Context manager for tracking file processing."""
    return _tracker.track_file_processing(file_path)


def track_database_operation():
    """Context manager for tracking database operations."""
    return _tracker.track_database_operation()


def track_operation(operation_name: str):
    """Context manager for tracking named operations."""
    return _tracker.track_operation(operation_name)


def track_cache_access(hit: bool) -> None:
    """Track cache hit or miss."""
    _tracker.track_cache_access(hit)


def update_worker_metrics(active_workers: int, max_workers: int) -> None:
    """Update worker thread metrics."""
    _tracker.update_worker_metrics(active_workers, max_workers)


def update_queue_depth(depth: int) -> None:
    """Update processing queue depth."""
    _tracker.update_queue_depth(depth)