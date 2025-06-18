"""Performance metrics collection and tracking."""

import time
import psutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import json


@dataclass
class MetricsSnapshot:
    """A snapshot of performance metrics at a point in time."""
    timestamp: datetime
    files_processed: int
    processing_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hits: int
    cache_misses: int
    database_operations: int
    database_time: float
    worker_utilization: float
    queue_depth: int
    errors: int
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    @property
    def average_processing_time(self) -> float:
        """Calculate average time per file."""
        return self.processing_time / self.files_processed if self.files_processed > 0 else 0.0
    
    @property
    def database_overhead_percent(self) -> float:
        """Calculate database time as percentage of total."""
        return (self.database_time / self.processing_time * 100) if self.processing_time > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "files_processed": self.files_processed,
            "processing_time": self.processing_time,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "cache_hit_rate": self.cache_hit_rate,
            "database_operations": self.database_operations,
            "database_time": self.database_time,
            "worker_utilization": self.worker_utilization,
            "queue_depth": self.queue_depth,
            "errors": self.errors,
            "average_processing_time": self.average_processing_time,
            "database_overhead_percent": self.database_overhead_percent
        }


@dataclass
class FileTypeMetrics:
    """Metrics for a specific file type."""
    count: int = 0
    total_time: float = 0.0
    total_size_bytes: int = 0
    min_time: float = float('inf')
    max_time: float = 0.0
    
    def add_sample(self, processing_time: float, size_bytes: int) -> None:
        """Add a processing sample."""
        self.count += 1
        self.total_time += processing_time
        self.total_size_bytes += size_bytes
        self.min_time = min(self.min_time, processing_time)
        self.max_time = max(self.max_time, processing_time)
    
    @property
    def average_time(self) -> float:
        """Average processing time."""
        return self.total_time / self.count if self.count > 0 else 0.0
    
    @property
    def average_size_mb(self) -> float:
        """Average file size in MB."""
        return (self.total_size_bytes / self.count / 1024 / 1024) if self.count > 0 else 0.0


class PerformanceMetrics:
    """Track performance metrics for the application."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = time.time()
        
        # Counters
        self.files_processed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.database_operations = 0
        self.errors = 0
        
        # Timers
        self.processing_time = 0.0
        self.database_time = 0.0
        
        # File type specific metrics
        self.file_type_metrics: Dict[str, FileTypeMetrics] = defaultdict(FileTypeMetrics)
        
        # Worker metrics
        self.active_workers = 0
        self.max_workers = 0
        self.queue_depth = 0
        
        # Memory tracking
        self._process = psutil.Process()
        self.peak_memory_mb = 0.0
        
        # Operation timings
        self._operation_times: Dict[str, List[float]] = defaultdict(list)
        
    def record_file_processed(self, file_path: Path, processing_time: float) -> None:
        """Record that a file was processed."""
        with self._lock:
            self.files_processed += 1
            self.processing_time += processing_time
            
            # Track by file type
            ext = file_path.suffix.lower()
            size = file_path.stat().st_size if file_path.exists() else 0
            self.file_type_metrics[ext].add_sample(processing_time, size)
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self.cache_misses += 1
    
    def record_database_operation(self, operation_time: float) -> None:
        """Record a database operation."""
        with self._lock:
            self.database_operations += 1
            self.database_time += operation_time
    
    def record_error(self) -> None:
        """Record an error occurred."""
        with self._lock:
            self.errors += 1
    
    def record_operation_time(self, operation: str, duration: float) -> None:
        """Record time for a specific operation type."""
        with self._lock:
            self._operation_times[operation].append(duration)
    
    def update_worker_count(self, active: int, max_workers: int) -> None:
        """Update worker thread counts."""
        with self._lock:
            self.active_workers = active
            self.max_workers = max_workers
    
    def update_queue_depth(self, depth: int) -> None:
        """Update queue depth."""
        with self._lock:
            self.queue_depth = depth
    
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        with self._lock:
            self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
        
        return memory_mb
    
    def get_current_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        return self._process.cpu_percent(interval=0.1)
    
    def get_snapshot(self) -> MetricsSnapshot:
        """Get a snapshot of current metrics."""
        with self._lock:
            worker_utilization = (self.active_workers / self.max_workers * 100) if self.max_workers > 0 else 0.0
            
            return MetricsSnapshot(
                timestamp=datetime.now(),
                files_processed=self.files_processed,
                processing_time=self.processing_time,
                memory_usage_mb=self.get_current_memory_mb(),
                cpu_usage_percent=self.get_current_cpu_percent(),
                cache_hits=self.cache_hits,
                cache_misses=self.cache_misses,
                database_operations=self.database_operations,
                database_time=self.database_time,
                worker_utilization=worker_utilization,
                queue_depth=self.queue_depth,
                errors=self.errors
            )
    
    def get_file_type_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary statistics by file type."""
        with self._lock:
            summary = {}
            for ext, metrics in self.file_type_metrics.items():
                if metrics.count > 0:
                    summary[ext] = {
                        "count": metrics.count,
                        "average_time": metrics.average_time,
                        "min_time": metrics.min_time,
                        "max_time": metrics.max_time,
                        "average_size_mb": metrics.average_size_mb,
                        "total_time": metrics.total_time
                    }
            return summary
    
    def get_operation_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of operation timings."""
        with self._lock:
            summary = {}
            for operation, times in self._operation_times.items():
                if times:
                    summary[operation] = {
                        "count": len(times),
                        "total": sum(times),
                        "average": sum(times) / len(times),
                        "min": min(times),
                        "max": max(times)
                    }
            return summary
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        snapshot = self.get_snapshot()
        uptime = time.time() - self._start_time
        
        return {
            "summary": {
                "uptime_seconds": uptime,
                "total_files": snapshot.files_processed,
                "total_time": snapshot.processing_time,
                "files_per_second": snapshot.files_processed / uptime if uptime > 0 else 0,
                "errors": snapshot.errors,
                "error_rate": (snapshot.errors / snapshot.files_processed * 100) if snapshot.files_processed > 0 else 0
            },
            "current_metrics": snapshot.to_dict(),
            "file_types": self.get_file_type_summary(),
            "operations": self.get_operation_summary(),
            "memory": {
                "current_mb": snapshot.memory_usage_mb,
                "peak_mb": self.peak_memory_mb
            },
            "cache": {
                "hits": snapshot.cache_hits,
                "misses": snapshot.cache_misses,
                "hit_rate": snapshot.cache_hit_rate
            },
            "database": {
                "operations": snapshot.database_operations,
                "total_time": snapshot.database_time,
                "overhead_percent": snapshot.database_overhead_percent
            }
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self.__init__()
    
    def save_report(self, path: Path) -> None:
        """Save performance report to file."""
        report = self.get_performance_report()
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)


class MetricsCollector:
    """Singleton metrics collector for the application."""
    
    _instance: Optional['MetricsCollector'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'MetricsCollector':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.metrics = PerformanceMetrics()
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'MetricsCollector':
        """Get the singleton instance."""
        return cls()
    
    def __getattr__(self, name):
        """Delegate to metrics object."""
        return getattr(self.metrics, name)