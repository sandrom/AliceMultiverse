"""CLI commands for recreating generations from existing assets."""

import asyncio
import click
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .generation_tracker import get_generation_tracker
from .registry import get_registry
from ..core.structured_logging import get_logger
from ..core.file_operations import FileHandler

console = Console()
logger = get_logger(__name__)


@click.group()
def cli():
    """Commands for recreating AI generations."""


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def inspect(file_path):
    """Inspect generation metadata from a file."""
    path = Path(file_path)
    
    console.print(f"\n[bold]Inspecting: {path.name}[/bold]\n")
    
    # Try to read embedded metadata
    from ..metadata.embedder import MetadataEmbedder
    embedder = MetadataEmbedder()
    metadata = embedder.extract_metadata(path)
    
    if metadata:
        # Display metadata in a nice table
        table = Table(title="Embedded Metadata")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in metadata.items():
            if isinstance(value, dict):
                value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            table.add_row(key, str(value))
        
        console.print(table)
    else:
        console.print("[yellow]No embedded metadata found[/yellow]")
    
    # Check for sidecar files (YAML or JSON)
    yaml_sidecar = path.with_suffix(path.suffix + '.yaml')
    json_sidecar = path.with_suffix(path.suffix + '.json')
    
    sidecar_data = None
    sidecar_path = None
    
    if yaml_sidecar.exists():
        sidecar_path = yaml_sidecar
        with open(yaml_sidecar) as f:
            sidecar_data = yaml.safe_load(f)
    elif json_sidecar.exists():
        sidecar_path = json_sidecar
        with open(json_sidecar) as f:
            sidecar_data = json.load(f)
    
    if sidecar_data:
        console.print(f"\n[green]✓ Sidecar file found:[/green] {sidecar_path.name}")
        
        # Show key generation info
        panel = Panel(
            f"[bold]Prompt:[/bold] {sidecar_data.get('prompt', 'N/A')}\n"
            f"[bold]Model:[/bold] {sidecar_data.get('model', 'N/A')}\n"
            f"[bold]Provider:[/bold] {sidecar_data.get('provider', 'N/A')}\n"
            f"[bold]Cost:[/bold] ${sidecar_data.get('cost', 0):.3f}\n"
            f"[bold]Generated:[/bold] {sidecar_data.get('timestamp', 'N/A')}",
            title="Generation Context"
        )
        console.print(panel)
    
    # Calculate content hash
    file_handler = FileHandler()
    content_hash = file_handler.calculate_file_hash(path)
    console.print(f"\n[dim]Content Hash: {content_hash}[/dim]")


@cli.command()
@click.argument('asset_id')
@click.option('--provider', help='Override original provider')
@click.option('--model', help='Override original model')
@click.option('--output', '-o', type=click.Path(), help='Output path')
@click.option('--dry-run', '-n', is_flag=True, help='Show what would be done')
def recreate(asset_id, provider, model, output, dry_run):
    """Recreate a generation from its asset ID."""
    
    async def _recreate():
        tracker = get_generation_tracker()
        
        # Get original generation context
        context = await tracker.get_generation_context(asset_id)
        if not context:
            console.print(f"[red]No generation context found for asset {asset_id}[/red]")
            return
        
        # Show original context
        console.print("\n[bold]Original Generation:[/bold]")
        console.print(f"Prompt: {context.get('prompt', 'N/A')}")
        console.print(f"Model: {context.get('model', 'N/A')}")
        console.print(f"Provider: {context.get('provider', 'N/A')}")
        console.print(f"Cost: ${context.get('cost', 0):.3f}")
        
        if context.get('reference_assets'):
            console.print(f"References: {len(context['reference_assets'])} assets")
        
        if dry_run:
            console.print("\n[yellow]Dry run - no generation will be performed[/yellow]")
            return
        
        # Build recreation request
        request = await tracker.recreate_generation(asset_id)
        if not request:
            console.print("[red]Failed to build recreation request[/red]")
            return
        
        # Override if specified
        if model:
            request.model = model
        if output:
            request.output_path = Path(output)
        
        # Determine provider
        provider_name = provider or context.get('provider', 'fal')
        
        console.print(f"\n[bold]Recreating with:[/bold]")
        console.print(f"Provider: {provider_name}")
        console.print(f"Model: {request.model}")
        
        # Get provider and generate
        registry = get_registry()
        provider_instance = registry.get_provider(provider_name)
        
        with console.status("Generating..."):
            result = await provider_instance.generate(request)
        
        if result.success:
            console.print(f"\n[green]✓ Recreation successful![/green]")
            console.print(f"Output: {result.file_path}")
            console.print(f"Cost: ${result.cost:.3f}")
            console.print(f"New Asset ID: {result.asset_id}")
        else:
            console.print(f"\n[red]✗ Recreation failed: {result.error}[/red]")
    
    asyncio.run(_recreate())


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--recursive', '-r', is_flag=True, help='Search recursively')
def catalog(directory, recursive):
    """Catalog all generations in a directory."""
    path = Path(directory)
    pattern = "**/*" if recursive else "*"
    
    console.print(f"\n[bold]Cataloging generations in: {path}[/bold]\n")
    
    # Supported extensions
    extensions = {'.png', '.jpg', '.jpeg', '.webp', '.mp4', '.mov'}
    
    # Find all media files
    files = []
    for ext in extensions:
        files.extend(path.glob(f"{pattern}{ext}"))
    
    if not files:
        console.print("[yellow]No media files found[/yellow]")
        return
    
    # Create table
    table = Table(title=f"Found {len(files)} files")
    table.add_column("File", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Model", style="green")
    table.add_column("Provider", style="blue")
    table.add_column("Has Context", style="yellow")
    
    embedder = MetadataEmbedder()
    FileHandler()
    
    for file_path in sorted(files):
        # Check for generation context
        metadata = embedder.extract_metadata(file_path)
        yaml_sidecar = file_path.with_suffix(file_path.suffix + '.yaml')
        json_sidecar = file_path.with_suffix(file_path.suffix + '.json')
        
        model = "Unknown"
        provider = "Unknown"
        has_context = "No"
        
        if metadata and 'generation_params' in metadata:
            try:
                params = json.loads(metadata['generation_params'])
                model = params.get('model', 'Unknown')
                provider = params.get('provider', 'Unknown')
                has_context = "Embedded"
            except:
                pass
        elif yaml_sidecar.exists():
            try:
                with open(yaml_sidecar) as f:
                    data = yaml.safe_load(f)
                model = data.get('model', 'Unknown')
                provider = data.get('provider', 'Unknown')
                has_context = "YAML"
            except:
                pass
        elif json_sidecar.exists():
            try:
                with open(json_sidecar) as f:
                    data = json.load(f)
                model = data.get('model', 'Unknown')
                provider = data.get('provider', 'Unknown')
                has_context = "JSON"
            except:
                pass
        
        file_type = "Image" if file_path.suffix in {'.png', '.jpg', '.jpeg', '.webp'} else "Video"
        
        table.add_row(
            file_path.name[:40] + "..." if len(file_path.name) > 40 else file_path.name,
            file_type,
            model[:20] + "..." if len(model) > 20 else model,
            provider,
            has_context
        )
    
    console.print(table)
    
    # Summary
    with_context = sum(
        1 for f in files 
        if f.with_suffix(f.suffix + '.yaml').exists() 
        or f.with_suffix(f.suffix + '.json').exists() 
        or embedder.extract_metadata(f)
    )
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"Total files: {len(files)}")
    console.print(f"With context: {with_context} ({with_context/len(files)*100:.1f}%)")


if __name__ == "__main__":
    cli()