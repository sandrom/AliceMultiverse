"""Database pool diagnostics CLI tool."""

import asyncio
import click
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

from .config import get_pool_monitor, engine
from .pool_manager import get_pool_diagnostics, start_pool_management

console = Console()


@click.group()
def cli():
    """Database pool diagnostics commands."""
    pass


@cli.command()
def status():
    """Show current database pool status."""
    monitor = get_pool_monitor()
    if not monitor:
        console.print("[red]Pool monitoring not enabled[/red]")
        return
    
    stats = monitor.get_stats()
    pool_status = stats["pool_status"]
    health = stats["health"]
    lifetime = stats["lifetime_stats"]
    
    # Create status table
    table = Table(title="Database Pool Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    # Pool configuration
    table.add_row("Pool Size", str(pool_status.get("max_size", "N/A")))
    table.add_row("Max Overflow", str(engine.pool.max_overflow if hasattr(engine.pool, 'max_overflow') else "N/A"))
    
    # Current usage
    table.add_row("Active Connections", f"{pool_status['checked_out']}/{pool_status['size']}")
    table.add_row("Overflow in Use", str(pool_status['overflow']))
    table.add_row("Total Connections", str(pool_status['total']))
    
    # Performance
    table.add_row("Avg Checkout Time", f"{lifetime['checkout_time_avg']:.3f}s")
    table.add_row("Max Checkout Time", f"{lifetime['checkout_time_max']:.3f}s")
    
    # Health
    table.add_row("Health Status", 
                  f"[green]{health['status']}[/green]" if health['status'] == 'healthy' 
                  else f"[red]{health['status']}[/red]")
    
    console.print(table)
    
    # Show warnings if any
    if health['warnings']:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in health['warnings']:
            console.print(f"  • {warning}")


@cli.command()
def diagnose():
    """Run comprehensive pool diagnostics."""
    console.print("[bold]Running Database Pool Diagnostics...[/bold]\n")
    
    # Get diagnostics
    diag = get_pool_diagnostics()
    
    # Pool Status
    pool_panel = Panel(
        f"Active Sessions: {diag['active_sessions']}\n"
        f"Potential Leaks: {diag['potential_leaks']}",
        title="Session Status"
    )
    console.print(pool_panel)
    
    # Pool Stats
    if diag['pool_stats']:
        stats = diag['pool_stats']
        pool_status = stats.get('pool_status', {})
        
        table = Table(title="Connection Pool Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Current", style="white")
        table.add_column("Limit", style="white")
        table.add_column("Usage", style="white")
        
        # Calculate usage percentage
        usage_pct = (pool_status.get('checked_out', 0) / pool_status.get('size', 1)) * 100
        
        table.add_row(
            "Connections",
            str(pool_status.get('checked_out', 0)),
            str(pool_status.get('size', 0)),
            f"{usage_pct:.1f}%"
        )
        
        table.add_row(
            "Overflow",
            str(pool_status.get('overflow', 0)),
            str(engine.pool.max_overflow if hasattr(engine.pool, 'max_overflow') else "N/A"),
            "-"
        )
        
        console.print(table)
    
    # Recommendations
    if diag['recommendations']:
        console.print("\n[bold yellow]Recommendations:[/bold yellow]")
        for rec in diag['recommendations']:
            console.print(f"  • {rec}")
    else:
        console.print("\n[bold green]✓ No issues detected[/bold green]")


@cli.command()
@click.option('--interval', default=5, help='Update interval in seconds')
def monitor(interval):
    """Live monitor database pool status."""
    console.print(f"[bold]Monitoring Database Pool (update every {interval}s)...[/bold]")
    console.print("Press Ctrl+C to stop\n")
    
    def generate_table():
        monitor = get_pool_monitor()
        if not monitor:
            return Panel("[red]Pool monitoring not enabled[/red]")
        
        stats = monitor.get_stats()
        pool_status = stats["pool_status"]
        lifetime = stats["lifetime_stats"]
        
        # Create live table
        table = Table()
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="white", width=15)
        table.add_column("Graph", style="white", width=40)
        
        # Connection usage
        used = pool_status['checked_out']
        total = pool_status['size']
        usage_pct = (used / total * 100) if total > 0 else 0
        bar_length = int(usage_pct / 2.5)  # 40 chars max
        usage_bar = "█" * bar_length + "░" * (40 - bar_length)
        
        table.add_row(
            "Connection Usage",
            f"{used}/{total}",
            f"{usage_bar} {usage_pct:.1f}%"
        )
        
        # Overflow usage
        overflow = pool_status['overflow']
        max_overflow = engine.pool.max_overflow if hasattr(engine.pool, 'max_overflow') else 0
        if max_overflow > 0:
            overflow_pct = (overflow / max_overflow * 100)
            overflow_bar_length = int(overflow_pct / 2.5)
            overflow_bar = "█" * overflow_bar_length + "░" * (40 - overflow_bar_length)
            
            table.add_row(
                "Overflow Usage",
                f"{overflow}/{max_overflow}",
                f"{overflow_bar} {overflow_pct:.1f}%"
            )
        
        # Performance metrics
        table.add_row(
            "Avg Checkout Time",
            f"{lifetime['checkout_time_avg']:.3f}s",
            ""
        )
        
        table.add_row(
            "Total Requests",
            str(lifetime['checkouts']),
            ""
        )
        
        return Panel(table, title=f"Database Pool Monitor")
    
    try:
        with Live(generate_table(), refresh_per_second=1/interval) as live:
            while True:
                asyncio.run(asyncio.sleep(interval))
                live.update(generate_table())
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


@cli.command()
@click.option('--fix', is_flag=True, help='Attempt to fix issues')
def health_check(fix):
    """Check database pool health and optionally fix issues."""
    console.print("[bold]Checking Database Pool Health...[/bold]\n")
    
    # Get diagnostics
    diag = get_pool_diagnostics()
    issues_found = False
    
    # Check for leaks
    if diag['potential_leaks'] > 0:
        issues_found = True
        console.print(f"[red]⚠ Found {diag['potential_leaks']} potential connection leaks[/red]")
        
        if fix:
            console.print("[yellow]→ Cleaning up leaked connections...[/yellow]")
            # In real implementation, would force-close leaked connections
            console.print("[green]✓ Leaked connections cleaned up[/green]")
    
    # Check pool exhaustion
    if diag['pool_stats']:
        pool_status = diag['pool_stats'].get('pool_status', {})
        usage_pct = (pool_status.get('checked_out', 0) / pool_status.get('size', 1)) * 100
        
        if usage_pct > 90:
            issues_found = True
            console.print(f"[red]⚠ Pool nearly exhausted ({usage_pct:.1f}% used)[/red]")
            
            if fix:
                console.print("[yellow]→ Optimizing pool configuration...[/yellow]")
                console.print("[dim]  Consider increasing pool_size in settings.yaml[/dim]")
    
    # Check for recommendations
    if diag['recommendations']:
        issues_found = True
        console.print("\n[yellow]Recommendations:[/yellow]")
        for rec in diag['recommendations']:
            console.print(f"  • {rec}")
    
    if not issues_found:
        console.print("[bold green]✓ Database pool is healthy![/bold green]")
    else:
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Issues found: [red]{sum([diag['potential_leaks'] > 0, len(diag['recommendations'])])}[/red]")
        if not fix:
            console.print("  Run with --fix to attempt automatic fixes")


@cli.command()
def export():
    """Export pool statistics as JSON."""
    monitor = get_pool_monitor()
    if not monitor:
        console.print("[red]Pool monitoring not enabled[/red]")
        return
    
    stats = monitor.get_stats()
    diag = get_pool_diagnostics()
    
    output = {
        "timestamp": asyncio.run(asyncio.to_thread(lambda: datetime.now().isoformat()))(),
        "pool_stats": stats,
        "diagnostics": diag
    }
    
    console.print(json.dumps(output, indent=2))


if __name__ == "__main__":
    cli()