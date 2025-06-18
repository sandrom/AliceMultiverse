"""Tests for performance monitoring and metrics system."""

import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from alicemultiverse.monitoring.metrics import (
    PerformanceMetrics,
    MetricsCollector,
    MetricsSnapshot,
    FileTypeMetrics
)
from alicemultiverse.monitoring.tracker import PerformanceTracker, get_tracker
from alicemultiverse.monitoring.dashboard import MetricsDashboard


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""
    
    def test_initialization(self):
        """Test metrics initialization."""
        metrics = PerformanceMetrics()
        
        assert metrics.files_processed == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.database_operations == 0
        assert metrics.errors == 0
        assert metrics.processing_time == 0.0
        assert metrics.database_time == 0.0
    
    def test_record_file_processed(self, tmp_path):
        """Test recording file processing."""
        metrics = PerformanceMetrics()
        
        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"test" * 1000)
        
        # Record processing
        metrics.record_file_processed(test_file, 0.5)
        
        assert metrics.files_processed == 1
        assert metrics.processing_time == 0.5
        
        # Check file type metrics
        assert ".jpg" in metrics.file_type_metrics
        jpg_metrics = metrics.file_type_metrics[".jpg"]
        assert jpg_metrics.count == 1
        assert jpg_metrics.total_time == 0.5
        assert jpg_metrics.average_time == 0.5
    
    def test_cache_tracking(self):
        """Test cache hit/miss tracking."""
        metrics = PerformanceMetrics()
        
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1
        
        snapshot = metrics.get_snapshot()
        assert snapshot.cache_hit_rate == pytest.approx(66.67, rel=0.01)
    
    def test_database_operations(self):
        """Test database operation tracking."""
        metrics = PerformanceMetrics()
        
        metrics.record_database_operation(0.1)
        metrics.record_database_operation(0.2)
        
        assert metrics.database_operations == 2
        assert metrics.database_time == 0.3
    
    def test_error_tracking(self):
        """Test error tracking."""
        metrics = PerformanceMetrics()
        
        metrics.record_error()
        metrics.record_error()
        
        assert metrics.errors == 2
    
    def test_operation_timing(self):
        """Test operation timing tracking."""
        metrics = PerformanceMetrics()
        
        metrics.record_operation_time("parse", 0.1)
        metrics.record_operation_time("parse", 0.2)
        metrics.record_operation_time("analyze", 0.5)
        
        summary = metrics.get_operation_summary()
        
        assert "parse" in summary
        assert summary["parse"]["count"] == 2
        assert summary["parse"]["total"] == 0.3
        assert summary["parse"]["average"] == 0.15
        
        assert "analyze" in summary
        assert summary["analyze"]["count"] == 1
        assert summary["analyze"]["average"] == 0.5
    
    def test_worker_metrics(self):
        """Test worker thread metrics."""
        metrics = PerformanceMetrics()
        
        metrics.update_worker_count(4, 8)
        metrics.update_queue_depth(10)
        
        snapshot = metrics.get_snapshot()
        assert snapshot.worker_utilization == 50.0
        assert snapshot.queue_depth == 10
    
    def test_memory_tracking(self):
        """Test memory usage tracking."""
        metrics = PerformanceMetrics()
        
        memory_mb = metrics.get_current_memory_mb()
        assert memory_mb > 0
        assert metrics.peak_memory_mb >= memory_mb
    
    def test_performance_report(self, tmp_path):
        """Test comprehensive performance report."""
        metrics = PerformanceMetrics()
        
        # Add some data
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"test")
        
        metrics.record_file_processed(test_file, 0.1)
        metrics.record_cache_hit()
        metrics.record_database_operation(0.05)
        metrics.record_operation_time("analyze", 0.2)
        
        report = metrics.get_performance_report()
        
        assert "summary" in report
        assert report["summary"]["total_files"] == 1
        
        assert "file_types" in report
        assert ".jpg" in report["file_types"]
        
        assert "operations" in report
        assert "analyze" in report["operations"]
        
        assert "cache" in report
        assert report["cache"]["hits"] == 1
        
        assert "database" in report
        assert report["database"]["operations"] == 1
    
    def test_save_report(self, tmp_path):
        """Test saving report to file."""
        metrics = PerformanceMetrics()
        metrics.record_file_processed(tmp_path / "test.jpg", 0.1)
        
        report_path = tmp_path / "report.json"
        metrics.save_report(report_path)
        
        assert report_path.exists()
        
        import json
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["summary"]["total_files"] == 1


class TestMetricsSnapshot:
    """Test MetricsSnapshot class."""
    
    def test_snapshot_properties(self):
        """Test snapshot calculated properties."""
        from datetime import datetime
        
        snapshot = MetricsSnapshot(
            timestamp=datetime.now(),
            files_processed=100,
            processing_time=50.0,
            memory_usage_mb=256.0,
            cpu_usage_percent=45.0,
            cache_hits=80,
            cache_misses=20,
            database_operations=200,
            database_time=10.0,
            worker_utilization=75.0,
            queue_depth=5,
            errors=2
        )
        
        assert snapshot.cache_hit_rate == 80.0
        assert snapshot.average_processing_time == 0.5
        assert snapshot.database_overhead_percent == 20.0
    
    def test_snapshot_to_dict(self):
        """Test snapshot serialization."""
        from datetime import datetime
        
        snapshot = MetricsSnapshot(
            timestamp=datetime.now(),
            files_processed=10,
            processing_time=5.0,
            memory_usage_mb=128.0,
            cpu_usage_percent=25.0,
            cache_hits=8,
            cache_misses=2,
            database_operations=20,
            database_time=1.0,
            worker_utilization=50.0,
            queue_depth=0,
            errors=0
        )
        
        data = snapshot.to_dict()
        
        assert "timestamp" in data
        assert data["files_processed"] == 10
        assert data["cache_hit_rate"] == 80.0
        assert data["average_processing_time"] == 0.5


class TestFileTypeMetrics:
    """Test FileTypeMetrics class."""
    
    def test_add_sample(self):
        """Test adding processing samples."""
        metrics = FileTypeMetrics()
        
        metrics.add_sample(0.1, 1024)
        metrics.add_sample(0.2, 2048)
        metrics.add_sample(0.15, 1536)
        
        assert metrics.count == 3
        assert metrics.total_time == 0.45
        assert metrics.average_time == 0.15
        assert metrics.min_time == 0.1
        assert metrics.max_time == 0.2
        assert metrics.average_size_mb == pytest.approx(0.00146, rel=0.01)


class TestMetricsCollector:
    """Test MetricsCollector singleton."""
    
    def test_singleton(self):
        """Test singleton behavior."""
        collector1 = MetricsCollector.get_instance()
        collector2 = MetricsCollector.get_instance()
        
        assert collector1 is collector2
    
    def test_delegation(self):
        """Test method delegation to metrics."""
        collector = MetricsCollector.get_instance()
        collector.metrics.reset()  # Reset to clean state
        
        collector.record_file_processed(Path("test.jpg"), 0.1)
        assert collector.files_processed == 1


class TestPerformanceTracker:
    """Test PerformanceTracker class."""
    
    def test_track_file_processing(self, tmp_path):
        """Test file processing tracking."""
        tracker = PerformanceTracker()
        tracker.collector.metrics.reset()
        
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test")
        
        with tracker.track_file_processing(test_file):
            time.sleep(0.01)  # Simulate processing
        
        assert tracker.collector.files_processed == 1
        assert tracker.collector.processing_time > 0
    
    def test_track_file_processing_error(self, tmp_path):
        """Test error tracking during file processing."""
        tracker = PerformanceTracker()
        tracker.collector.metrics.reset()
        
        test_file = tmp_path / "test.jpg"
        
        with pytest.raises(ValueError):
            with tracker.track_file_processing(test_file):
                raise ValueError("Test error")
        
        assert tracker.collector.errors == 1
    
    def test_track_database_operation(self):
        """Test database operation tracking."""
        tracker = PerformanceTracker()
        tracker.collector.metrics.reset()
        
        with tracker.track_database_operation():
            time.sleep(0.01)
        
        assert tracker.collector.database_operations == 1
        assert tracker.collector.database_time > 0
    
    def test_track_operation(self):
        """Test named operation tracking."""
        tracker = PerformanceTracker()
        tracker.collector.metrics.reset()
        
        with tracker.track_operation("test_op"):
            time.sleep(0.01)
        
        summary = tracker.collector.get_operation_summary()
        assert "test_op" in summary
        assert summary["test_op"]["count"] == 1
    
    def test_track_cache_access(self):
        """Test cache access tracking."""
        tracker = PerformanceTracker()
        tracker.collector.metrics.reset()
        
        tracker.track_cache_access(True)
        tracker.track_cache_access(False)
        
        assert tracker.collector.cache_hits == 1
        assert tracker.collector.cache_misses == 1
    
    def test_track_method_decorator(self):
        """Test method tracking decorator."""
        tracker = PerformanceTracker()
        tracker.collector.metrics.reset()
        
        @PerformanceTracker.track_method("test_method")
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        assert result == "result"
        
        summary = tracker.collector.get_operation_summary()
        assert "test_method" in summary
    
    def test_track_db_method_decorator(self):
        """Test database method decorator."""
        tracker = PerformanceTracker()
        tracker.collector.metrics.reset()
        
        @PerformanceTracker.track_db_method
        def db_operation():
            time.sleep(0.01)
            return "db_result"
        
        result = db_operation()
        assert result == "db_result"
        
        assert tracker.collector.database_operations == 1


class TestMetricsDashboard:
    """Test MetricsDashboard class."""
    
    def test_initialization(self):
        """Test dashboard initialization."""
        dashboard = MetricsDashboard(refresh_interval=2.0)
        
        assert dashboard.refresh_interval == 2.0
        assert dashboard.max_history == 60
        assert len(dashboard.history) == 0
    
    def test_create_layout(self):
        """Test layout creation."""
        dashboard = MetricsDashboard()
        layout = dashboard.create_layout()
        
        # Check main sections exist
        assert layout["header"] is not None
        assert layout["main"] is not None
        assert layout["footer"] is not None
    
    def test_show_once(self):
        """Test showing dashboard once."""
        dashboard = MetricsDashboard()
        
        # Add some test data
        dashboard.collector.record_file_processed(Path("test.jpg"), 0.1)
        
        # This should not raise
        dashboard.show_once()
    
    def test_export_metrics(self, tmp_path):
        """Test exporting metrics."""
        dashboard = MetricsDashboard()
        dashboard.collector.record_file_processed(Path("test.jpg"), 0.1)
        
        export_path = tmp_path / "metrics.json"
        dashboard.export_metrics(export_path)
        
        assert export_path.exists()
    
    def test_performance_summary(self):
        """Test getting performance summary."""
        dashboard = MetricsDashboard()
        dashboard.collector.record_file_processed(Path("test.jpg"), 0.1)
        dashboard.collector.record_cache_hit()
        
        summary = dashboard.get_performance_summary()
        
        assert "Performance Summary" in summary
        assert "Total Files: 1" in summary
        assert "File Types:" in summary
        assert ".jpg: 1 files" in summary


class TestGlobalFunctions:
    """Test global convenience functions."""
    
    def test_get_tracker(self):
        """Test global tracker access."""
        tracker1 = get_tracker()
        tracker2 = get_tracker()
        
        assert tracker1 is tracker2
    
    def test_convenience_functions(self, tmp_path):
        """Test convenience tracking functions."""
        from alicemultiverse.monitoring.tracker import (
            track_file_processing,
            track_database_operation,
            track_operation,
            track_cache_access,
            update_worker_metrics,
            update_queue_depth
        )
        
        # Reset metrics
        get_tracker().collector.metrics.reset()
        
        # Test file processing
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test")
        
        with track_file_processing(test_file):
            pass
        
        # Test database operation
        with track_database_operation():
            pass
        
        # Test named operation
        with track_operation("test"):
            pass
        
        # Test cache access
        track_cache_access(True)
        
        # Test worker metrics
        update_worker_metrics(2, 4)
        update_queue_depth(5)
        
        # Verify
        collector = get_tracker().collector
        assert collector.files_processed == 1
        assert collector.database_operations == 1
        assert collector.cache_hits == 1
        
        snapshot = collector.get_snapshot()
        assert snapshot.worker_utilization == 50.0
        assert snapshot.queue_depth == 5