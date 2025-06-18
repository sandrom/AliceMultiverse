"""Performance monitoring command for Alice CLI."""

import click
from pathlib import Path

from ..monitoring.dashboard import MetricsDashboard
from ..monitoring.metrics import MetricsCollector


@click.group()
def performance():
    """Performance monitoring and metrics commands."""
    pass


@performance.command()
@click.option('--refresh', '-r', default=1.0, help='Refresh interval in seconds')
@click.option('--once', is_flag=True, help='Show metrics once and exit')
def monitor(refresh: float, once: bool):
    """Monitor performance metrics in real-time."""
    dashboard = MetricsDashboard(refresh_interval=refresh)
    
    if once:
        dashboard.show_once()
    else:
        click.echo("Starting performance monitor... Press Ctrl+C to exit")
        try:
            dashboard.run()
        except KeyboardInterrupt:
            click.echo("\nStopping performance monitor...")


@performance.command()
@click.argument('output_path', type=click.Path(path_type=Path))
def export(output_path: Path):
    """Export performance metrics to a file."""
    collector = MetricsCollector.get_instance()
    collector.save_report(output_path)
    click.echo(f"Performance report exported to: {output_path}")


@performance.command()
def report():
    """Show current performance report."""
    collector = MetricsCollector.get_instance()
    report = collector.get_performance_report()
    
    # Format and display the report
    click.echo("\n=== Performance Report ===\n")
    
    # Summary
    summary = report['summary']
    click.echo("Summary:")
    click.echo(f"  Total Files: {summary['total_files']:,}")
    click.echo(f"  Total Time: {summary['total_time']:.1f}s")
    click.echo(f"  Files/Second: {summary['files_per_second']:.2f}")
    click.echo(f"  Error Rate: {summary['error_rate']:.1f}%")
    
    # Memory
    memory = report['memory']
    click.echo("\nMemory:")
    click.echo(f"  Current: {memory['current_mb']:.1f} MB")
    click.echo(f"  Peak: {memory['peak_mb']:.1f} MB")
    
    # Cache
    cache = report['cache']
    click.echo("\nCache:")
    click.echo(f"  Hits: {cache['hits']:,}")
    click.echo(f"  Misses: {cache['misses']:,}")
    click.echo(f"  Hit Rate: {cache['hit_rate']:.1f}%")
    
    # Database
    database = report['database']
    click.echo("\nDatabase:")
    click.echo(f"  Operations: {database['operations']:,}")
    click.echo(f"  Total Time: {database['total_time']:.1f}s")
    click.echo(f"  Overhead: {database['overhead_percent']:.1f}%")
    
    # File Types
    file_types = report['file_types']
    if file_types:
        click.echo("\nFile Types:")
        for ext, stats in sorted(file_types.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
            click.echo(f"  {ext}: {stats['count']:,} files, {stats['average_time']:.3f}s avg")
    
    # Operations
    operations = report['operations']
    if operations:
        click.echo("\nTop Operations:")
        sorted_ops = sorted(operations.items(), key=lambda x: x[1]['total'], reverse=True)[:5]
        for op_name, stats in sorted_ops:
            click.echo(f"  {op_name}: {stats['count']:,} calls, {stats['average']:.3f}s avg")


@performance.command()
def reset():
    """Reset all performance metrics."""
    collector = MetricsCollector.get_instance()
    collector.reset()
    click.echo("Performance metrics have been reset.")