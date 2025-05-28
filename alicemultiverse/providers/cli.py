"""CLI commands for provider management."""

import argparse
import json
from typing import Optional

from rich.console import Console
from rich.table import Table

from .registry import get_cost_report, get_registry

console = Console()


def create_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add provider commands to CLI.
    
    Args:
        subparsers: Subparser group to add commands to
    """
    providers_parser = subparsers.add_parser(
        "providers",
        help="Manage AI generation providers"
    )
    
    providers_subparsers = providers_parser.add_subparsers(
        dest="subcommand",
        help="Provider subcommands"
    )
    
    # List providers
    list_parser = providers_subparsers.add_parser(
        "list",
        help="List available providers"
    )
    list_parser.add_argument(
        "--show-disabled",
        action="store_true",
        help="Include disabled providers"
    )
    
    # Cost report
    cost_parser = providers_subparsers.add_parser(
        "cost",
        help="Show cost report"
    )
    cost_parser.add_argument(
        "--provider",
        help="Show costs for specific provider"
    )
    cost_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    
    # Enable/disable
    enable_parser = providers_subparsers.add_parser(
        "enable",
        help="Enable a provider"
    )
    enable_parser.add_argument(
        "provider",
        help="Provider name"
    )
    
    disable_parser = providers_subparsers.add_parser(
        "disable",
        help="Disable a provider"
    )
    disable_parser.add_argument(
        "provider",
        help="Provider name"
    )
    
    # Set budget
    budget_parser = providers_subparsers.add_parser(
        "budget",
        help="Set global budget limit"
    )
    budget_parser.add_argument(
        "limit",
        type=float,
        help="Budget limit in USD"
    )


def run_providers_command(args: argparse.Namespace) -> int:
    """Run provider commands.
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    registry = get_registry()
    
    if args.subcommand == "list":
        return list_providers(registry, args.show_disabled)
    
    elif args.subcommand == "cost":
        return show_cost_report(args.provider, args.json)
    
    elif args.subcommand == "enable":
        registry.enable_provider(args.provider)
        console.print(f"[green]Enabled provider: {args.provider}[/green]")
        return 0
    
    elif args.subcommand == "disable":
        registry.disable_provider(args.provider)
        console.print(f"[yellow]Disabled provider: {args.provider}[/yellow]")
        return 0
    
    elif args.subcommand == "budget":
        registry.set_budget_limit(args.limit)
        console.print(f"[green]Set global budget limit: ${args.limit:.2f}[/green]")
        return 0
    
    else:
        console.print("[red]No subcommand specified[/red]")
        return 1


def list_providers(registry, show_disabled: bool = False) -> int:
    """List available providers.
    
    Args:
        registry: Provider registry
        show_disabled: Include disabled providers
        
    Returns:
        Exit code
    """
    providers = registry.list_providers()
    
    if show_disabled:
        # Get all providers including disabled
        all_providers = registry._enhanced_registry._provider_classes.keys()
        disabled = registry._enhanced_registry._disabled_providers
        
        table = Table(title="AI Generation Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Type", style="yellow")
        
        for provider in sorted(all_providers):
            status = "Disabled" if provider in disabled else "Enabled"
            style = "red" if provider in disabled else "green"
            
            # Get capabilities
            try:
                temp_provider = registry._enhanced_registry._provider_classes[provider]()
                types = ", ".join(t.value for t in temp_provider.capabilities.generation_types)
            except:
                types = "Unknown"
            
            table.add_row(
                provider,
                f"[{style}]{status}[/{style}]",
                types
            )
    else:
        table = Table(title="Available Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Models", style="blue")
        
        for provider in sorted(providers):
            try:
                # Get provider info
                temp_provider = registry.get_provider(provider)
                types = ", ".join(t.value for t in temp_provider.capabilities.generation_types)
                models = ", ".join(temp_provider.capabilities.models[:3])
                if len(temp_provider.capabilities.models) > 3:
                    models += "..."
                
                table.add_row(provider, types, models)
            except:
                table.add_row(provider, "Error", "Unable to load")
    
    console.print(table)
    return 0


def show_cost_report(provider: Optional[str] = None, as_json: bool = False) -> int:
    """Show cost report.
    
    Args:
        provider: Specific provider or None for all
        as_json: Output as JSON
        
    Returns:
        Exit code
    """
    report = get_cost_report()
    
    if as_json:
        print(json.dumps(report, indent=2, default=str))
        return 0
    
    if provider:
        # Show specific provider stats
        stats = report.get("provider_stats", {}).get(provider)
        if not stats:
            console.print(f"[red]No data for provider: {provider}[/red]")
            return 1
        
        table = Table(title=f"Provider Statistics: {provider}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Cost", f"${stats['total_cost']:.4f}")
        table.add_row("Total Requests", str(stats['total_requests']))
        table.add_row("Success Rate", f"{stats['success_rate']:.1%}")
        table.add_row("Average Cost", f"${stats['average_cost']:.4f}")
        table.add_row("Average Time", f"{stats['average_time']:.2f}s")
        
        if stats['last_used']:
            table.add_row("Last Used", stats['last_used'])
        
        console.print(table)
        
        if stats['costs_by_model']:
            model_table = Table(title="Costs by Model")
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Cost", style="green")
            
            for model, cost in sorted(stats['costs_by_model'].items()):
                model_table.add_row(model, f"${cost:.4f}")
            
            console.print(model_table)
    
    else:
        # Show overall report
        table = Table(title="Cost Report")
        table.add_column("Category", style="cyan")
        table.add_column("Cost", style="green")
        
        table.add_row("Total Cost", f"${report['total_cost']:.4f}")
        
        console.print(table)
        
        # Provider breakdown
        if report['costs_by_provider']:
            provider_table = Table(title="Costs by Provider")
            provider_table.add_column("Provider", style="cyan")
            provider_table.add_column("Cost", style="green")
            provider_table.add_column("Percentage", style="yellow")
            
            total = report['total_cost']
            for provider, cost in sorted(report['costs_by_provider'].items(), key=lambda x: x[1], reverse=True):
                percentage = (cost / total * 100) if total > 0 else 0
                provider_table.add_row(
                    provider,
                    f"${cost:.4f}",
                    f"{percentage:.1f}%"
                )
            
            console.print(provider_table)
        
        # Project breakdown
        if report['costs_by_project']:
            project_table = Table(title="Costs by Project")
            project_table.add_column("Project", style="cyan")
            project_table.add_column("Cost", style="green")
            
            for project, cost in sorted(report['costs_by_project'].items(), key=lambda x: x[1], reverse=True):
                project_table.add_row(project, f"${cost:.4f}")
            
            console.print(project_table)
        
        # Daily costs (last 7 days)
        if report['daily_costs']:
            daily_table = Table(title="Daily Costs (Recent)")
            daily_table.add_column("Date", style="cyan")
            daily_table.add_column("Cost", style="green")
            
            # Sort by date and take last 7
            daily_items = sorted(report['daily_costs'].items())[-7:]
            for date, cost in daily_items:
                daily_table.add_row(date, f"${cost:.4f}")
            
            console.print(daily_table)
    
    return 0