"""Real-time performance dashboard using Rich terminal UI."""

import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from .metrics import MetricsCollector, MetricsSnapshot


class MetricsDashboard:
    """Real-time performance metrics dashboard."""
    
    def __init__(self, refresh_interval: float = 1.0):
        self.console = Console()
        self.collector = MetricsCollector.get_instance()
        self.refresh_interval = refresh_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.history: List[MetricsSnapshot] = []
        self.max_history = 60  # Keep last 60 snapshots
    
    def create_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=4)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="overview", ratio=1),
            Layout(name="performance", ratio=1)
        )
        
        layout["right"].split_column(
            Layout(name="operations", ratio=1),
            Layout(name="file_types", ratio=1)
        )
        
        return layout
    
    def get_header(self) -> Panel:
        """Create header panel."""
        title = Text("AliceMultiverse Performance Monitor", style="bold magenta")
        subtitle = Text(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        
        header = Text.assemble(title, "\n", subtitle, justify="center")
        return Panel(header, style="cyan")
    
    def get_overview_panel(self, snapshot: MetricsSnapshot) -> Panel:
        """Create overview metrics panel."""
        report = self.collector.get_performance_report()
        summary = report["summary"]
        
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Files Processed", f"{snapshot.files_processed:,}")
        table.add_row("Processing Rate", f"{summary['files_per_second']:.2f} files/sec")
        table.add_row("Average Time/File", f"{snapshot.average_processing_time:.3f}s")
        table.add_row("Total Errors", f"{snapshot.errors}")
        table.add_row("Error Rate", f"{summary['error_rate']:.1f}%")
        
        return Panel(table, title="Overview", border_style="blue")
    
    def get_performance_panel(self, snapshot: MetricsSnapshot) -> Panel:
        """Create performance metrics panel."""
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("CPU Usage", f"{snapshot.cpu_usage_percent:.1f}%")
        table.add_row("Memory Usage", f"{snapshot.memory_usage_mb:.1f} MB")
        table.add_row("Peak Memory", f"{self.collector.peak_memory_mb:.1f} MB")
        table.add_row("Cache Hit Rate", f"{snapshot.cache_hit_rate:.1f}%")
        table.add_row("Worker Utilization", f"{snapshot.worker_utilization:.1f}%")
        table.add_row("Queue Depth", f"{snapshot.queue_depth}")
        
        return Panel(table, title="Performance", border_style="green")
    
    def get_operations_panel(self) -> Panel:
        """Create operations timing panel."""
        operations = self.collector.get_operation_summary()
        
        if not operations:
            return Panel("No operations recorded yet", title="Operations", border_style="yellow")
        
        table = Table(expand=True)
        table.add_column("Operation", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Avg Time", justify="right")
        table.add_column("Total Time", justify="right")
        
        for op_name, stats in sorted(operations.items()):
            table.add_row(
                op_name.split('.')[-1][:20],  # Truncate long names
                f"{stats['count']:,}",
                f"{stats['average']:.3f}s",
                f"{stats['total']:.1f}s"
            )
        
        return Panel(table, title="Operations", border_style="yellow")
    
    def get_file_types_panel(self) -> Panel:
        """Create file types panel."""
        file_types = self.collector.get_file_type_summary()
        
        if not file_types:
            return Panel("No files processed yet", title="File Types", border_style="magenta")
        
        table = Table(expand=True)
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Avg Time", justify="right")
        table.add_column("Avg Size", justify="right")
        
        for ext, stats in sorted(file_types.items(), key=lambda x: x[1]['count'], reverse=True):
            table.add_row(
                ext or "(none)",
                f"{stats['count']:,}",
                f"{stats['average_time']:.3f}s",
                f"{stats['average_size_mb']:.1f} MB"
            )
        
        return Panel(table, title="File Types", border_style="magenta")
    
    def get_footer(self, snapshot: MetricsSnapshot) -> Panel:
        """Create footer with database and cache stats."""
        lines = []
        
        # Database stats
        db_ops = snapshot.database_operations
        db_time = snapshot.database_time
        db_overhead = snapshot.database_overhead_percent
        lines.append(f"Database: {db_ops:,} ops, {db_time:.1f}s total, {db_overhead:.1f}% overhead")
        
        # Cache stats
        cache_total = snapshot.cache_hits + snapshot.cache_misses
        lines.append(f"Cache: {snapshot.cache_hits:,} hits, {snapshot.cache_misses:,} misses ({snapshot.cache_hit_rate:.1f}% hit rate)")
        
        # Progress bar for worker utilization
        if snapshot.worker_utilization > 0:
            bar_width = 40
            filled = int(bar_width * snapshot.worker_utilization / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            lines.append(f"Workers: [{bar}] {snapshot.worker_utilization:.0f}%")
        
        content = "\n".join(lines)
        return Panel(content, title="System Stats", border_style="dim")
    
    def update_display(self, layout: Layout) -> None:
        """Update the dashboard display."""
        snapshot = self.collector.get_snapshot()
        self.history.append(snapshot)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        layout["header"].update(self.get_header())
        layout["overview"].update(self.get_overview_panel(snapshot))
        layout["performance"].update(self.get_performance_panel(snapshot))
        layout["operations"].update(self.get_operations_panel())
        layout["file_types"].update(self.get_file_types_panel())
        layout["footer"].update(self.get_footer(snapshot))
    
    def run(self) -> None:
        """Run the dashboard in a separate thread."""
        if self._running:
            return
        
        self._running = True
        layout = self.create_layout()
        
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while self._running:
                self.update_display(layout)
                time.sleep(self.refresh_interval)
    
    def start(self) -> None:
        """Start the dashboard in background."""
        if self._running:
            return
        
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the dashboard."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
    
    def show_once(self) -> None:
        """Show dashboard once without continuous updates."""
        layout = self.create_layout()
        self.update_display(layout)
        self.console.print(layout)
    
    def export_metrics(self, path: Path) -> None:
        """Export current metrics to file."""
        self.collector.save_report(path)
        self.console.print(f"[green]Metrics exported to {path}[/green]")
    
    def get_performance_summary(self) -> str:
        """Get a text summary of performance."""
        report = self.collector.get_performance_report()
        summary = report["summary"]
        
        lines = [
            "Performance Summary",
            "=" * 50,
            f"Total Files: {summary['total_files']:,}",
            f"Total Time: {summary['total_time']:.1f}s",
            f"Processing Rate: {summary['files_per_second']:.2f} files/sec",
            f"Error Rate: {summary['error_rate']:.1f}%",
            "",
            "File Types:",
        ]
        
        for ext, stats in report["file_types"].items():
            lines.append(f"  {ext}: {stats['count']:,} files, {stats['average_time']:.3f}s avg")
        
        return "\n".join(lines)


def create_dashboard(refresh_interval: float = 1.0) -> MetricsDashboard:
    """Create a new metrics dashboard."""
    return MetricsDashboard(refresh_interval)


def show_metrics_once() -> None:
    """Show metrics dashboard once."""
    dashboard = MetricsDashboard()
    dashboard.show_once()


def export_metrics(path: Path) -> None:
    """Export metrics to file."""
    dashboard = MetricsDashboard()
    dashboard.export_metrics(path)