"""Memory profiling and optimization CLI commands."""

import click
import psutil
import gc
import tracemalloc
import time
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from ..core.memory_optimization import MemoryConfig, MemoryMonitor
from ..core.config import load_config
from ..organizer.memory_optimized_organizer import MemoryOptimizedOrganizer

console = Console()


@click.group()
def memory():
    """Memory profiling and optimization commands."""
    pass


@memory.command()
@click.option('--duration', '-d', default=60, help='Monitoring duration in seconds')
@click.option('--interval', '-i', default=1, help='Update interval in seconds')
def monitor(duration: int, interval: float):
    """Monitor memory usage in real-time."""
    config = MemoryConfig()
    monitor = MemoryMonitor(config)
    
    start_time = time.time()
    
    def create_memory_table() -> Table:
        """Create memory usage table."""
        table = Table(title="Memory Usage")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        usage = monitor.get_memory_usage()
        
        table.add_row("Current", f"{usage['current_mb']:.1f} MB")
        table.add_row("Peak", f"{usage['peak_mb']:.1f} MB")
        table.add_row("Available", f"{usage['available_mb']:.1f} MB")
        table.add_row("System %", f"{usage['percent']:.1f}%")
        table.add_row("Limit", f"{usage['limit_mb']} MB")
        table.add_row("Usage Ratio", f"{usage['usage_ratio']:.1%}")
        
        # Add time info
        elapsed = time.time() - start_time
        remaining = max(0, duration - elapsed)
        table.add_row("Elapsed", f"{elapsed:.0f}s")
        table.add_row("Remaining", f"{remaining:.0f}s")
        
        return table
    
    # TODO: Review unreachable code - with Live(create_memory_table(), refresh_per_second=1/interval) as live:
    # TODO: Review unreachable code - while time.time() - start_time < duration:
    # TODO: Review unreachable code - time.sleep(interval)
    # TODO: Review unreachable code - live.update(create_memory_table())
            
    # TODO: Review unreachable code - # Trigger GC if needed
    # TODO: Review unreachable code - monitor.maybe_collect_garbage()
    
    # TODO: Review unreachable code - console.print("\n[green]Monitoring complete![/green]")


@memory.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--top', '-n', default=10, help='Number of top allocations to show')
def profile(path: str, top: int):
    """Profile memory usage for processing a directory."""
    tracemalloc.start()
    
    console.print(f"\n[cyan]Profiling memory for: {path}[/cyan]")
    
    # Take initial snapshot
    snapshot1 = tracemalloc.take_snapshot()
    
    # Process files
    config = load_config()
    config.paths.inbox = Path(path)
    
    with console.status("Processing files..."):
        organizer = MemoryOptimizedOrganizer(config)
        results = organizer.organize()
    
    # Take final snapshot
    snapshot2 = tracemalloc.take_snapshot()
    
    # Show statistics
    console.print(f"\n[green]Processed {results.statistics['organized']} files[/green]")
    
    # Memory statistics
    stats = organizer.get_memory_stats()
    
    table = Table(title="Memory Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Peak Memory", f"{stats['peak_memory_mb']:.1f} MB")
    table.add_row("GC Collections", str(stats['gc_collections']))
    table.add_row("Cache Hit Rate", f"{stats['cache_stats']['hit_rate']:.1%}")
    table.add_row("Cache Size", f"{stats['cache_stats']['size_mb']:.1f} MB")
    
    console.print(table)
    
    # Top memory allocations
    console.print(f"\n[yellow]Top {top} memory allocations:[/yellow]")
    
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    
    for index, stat in enumerate(top_stats[:top], 1):
        console.print(f"{index}. {stat}")
    
    tracemalloc.stop()


@memory.command()
@click.option('--profile', '-p', 
              type=click.Choice(['default', 'fast', 'memory_constrained', 'large_collection']),
              help='Performance profile to analyze')
def optimize(profile: Optional[str]):
    """Show memory optimization recommendations."""
    # Get system info
    virtual_mem = psutil.virtual_memory()
    
    console.print(Panel.fit(
        f"[bold]System Memory[/bold]\n"
        f"Total: {virtual_mem.total / 1024 / 1024 / 1024:.1f} GB\n"
        f"Available: {virtual_mem.available / 1024 / 1024 / 1024:.1f} GB\n"
        f"Used: {virtual_mem.percent:.1f}%",
        title="Current Status"
    ))
    
    # Recommendations based on system
    recommendations = []
    
    if virtual_mem.total < 8 * 1024 * 1024 * 1024:  # Less than 8GB
        recommendations.append("• Use 'memory_constrained' profile for systems with < 8GB RAM")
        recommendations.append("• Reduce batch_size to 50 or less")
        recommendations.append("• Limit max_workers to 4")
        recommendations.append("• Enable adaptive batch sizing")
    
    if virtual_mem.percent > 80:
        recommendations.append("• System memory usage is high - close other applications")
        recommendations.append("• Consider using streaming mode for large files")
        recommendations.append("• Enable aggressive garbage collection")
    
    # Profile-specific recommendations
    if profile:
        config = load_config()
        memory_config = MemoryConfig()
        
        if profile == 'memory_constrained':
            memory_config.max_memory_mb = 512
            memory_config.cache_size_mb = 64
        elif profile == 'large_collection':
            memory_config.max_memory_mb = 2048
            memory_config.cache_size_mb = 512
        
        table = Table(title=f"Memory Settings for '{profile}' Profile")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Description", style="yellow")
        
        table.add_row("Max Memory", f"{memory_config.max_memory_mb} MB", 
                     "Maximum memory usage limit")
        table.add_row("Cache Size", f"{memory_config.cache_size_mb} MB",
                     "Maximum cache size")
        table.add_row("Chunk Size", f"{memory_config.chunk_size_kb} KB",
                     "File reading chunk size")
        table.add_row("GC Threshold", f"{memory_config.gc_threshold_mb} MB",
                     "Trigger GC above this")
        table.add_row("Adaptive Batch", str(memory_config.adaptive_batch_size),
                     "Adjust batch size based on memory")
        
        console.print(table)
    
    if recommendations:
        console.print("\n[yellow]Recommendations:[/yellow]")
        for rec in recommendations:
            console.print(rec)


@memory.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--max-memory', '-m', default=1024, help='Maximum memory in MB')
@click.option('--cache-size', '-c', default=256, help='Cache size in MB')
def test(path: str, max_memory: int, cache_size: int):
    """Test memory usage with different configurations."""
    console.print(f"\n[cyan]Testing memory configurations for: {path}[/cyan]")
    
    # Create test configuration
    memory_config = MemoryConfig(
        max_memory_mb=max_memory,
        cache_size_mb=cache_size,
        adaptive_batch_size=True
    )
    
    # Count files
    file_count = sum(1 for _ in Path(path).rglob("*") if _.is_file())
    console.print(f"Found {file_count} files to process")
    
    # Test with configuration
    config = load_config()
    config.paths.inbox = Path(path)
    
    # Monitor memory during processing
    monitor = MemoryMonitor(memory_config)
    
    console.print(f"\n[yellow]Testing with max_memory={max_memory}MB, cache_size={cache_size}MB[/yellow]")
    
    start_time = time.time()
    initial_memory = monitor.get_memory_usage()
    
    with console.status("Processing..."):
        organizer = MemoryOptimizedOrganizer(config, memory_config)
        results = organizer.organize()
    
    duration = time.time() - start_time
    final_memory = monitor.get_memory_usage()
    
    # Show results
    table = Table(title="Test Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Files Processed", str(results.statistics['organized']))
    table.add_row("Duration", f"{duration:.1f}s")
    table.add_row("Files/Second", f"{results.statistics['organized']/duration:.1f}")
    table.add_row("Initial Memory", f"{initial_memory['current_mb']:.1f} MB")
    table.add_row("Peak Memory", f"{final_memory['peak_mb']:.1f} MB")
    table.add_row("Memory Growth", f"{final_memory['peak_mb'] - initial_memory['current_mb']:.1f} MB")
    
    console.print(table)
    
    # Check if configuration was suitable
    if final_memory['peak_mb'] > max_memory * 0.9:
        console.print("\n[red]⚠ Memory usage approached limit - consider increasing max_memory[/red]")
    else:
        console.print("\n[green]✓ Memory usage stayed within limits[/green]")


@memory.command()
def gc():
    """Force garbage collection and show statistics."""
    console.print("\n[cyan]Running garbage collection...[/cyan]")
    
    # Get initial state
    before = gc.get_stats()
    before_objects = len(gc.get_objects())
    
    # Run full collection
    collected = gc.collect(2)  # Full collection
    
    # Get final state
    after = gc.get_stats()
    after_objects = len(gc.get_objects())
    
    # Show results
    table = Table(title="Garbage Collection Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Objects Collected", str(collected))
    table.add_row("Objects Before", f"{before_objects:,}")
    table.add_row("Objects After", f"{after_objects:,}")
    table.add_row("Objects Freed", f"{before_objects - after_objects:,}")
    
    # Show generation stats
    for i, (b, a) in enumerate(zip(before, after)):
        table.add_row(f"Generation {i} Collections", 
                     f"{b['collections']} → {a['collections']}")
    
    console.print(table)
    
    # Memory impact
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    console.print(f"\nCurrent memory usage: {memory_mb:.1f} MB")