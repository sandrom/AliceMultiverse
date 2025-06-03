"""CLI commands for storage management."""

import asyncio
import json
from pathlib import Path
from typing import Optional
from uuid import UUID

import click
from rich.console import Console
from rich.table import Table

from ..core.config import load_config
from ..core.structured_logging import get_logger
from .duckdb_cache import DuckDBSearchCache
from .location_registry import (
    LocationStatus,
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)
from .multi_path_scanner import MultiPathScanner

logger = get_logger(__name__)
console = Console()


@click.group()
def storage():
    """Manage storage locations and file discovery."""
    pass


@storage.command()
@click.option("--db-path", type=click.Path(), help="Path to location registry database")
def init(db_path: Optional[str]):
    """Initialize storage location registry."""
    if not db_path:
        config = load_config()
        db_path = config.storage.location_registry_db
    
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    registry = StorageRegistry(db_path)
    console.print(f"[green]✓[/green] Initialized storage registry at {db_path}")
    registry.close()


@storage.command()
@click.option("--name", required=True, help="Name of the storage location")
@click.option("--path", required=True, help="Path to the storage location")
@click.option("--type", type=click.Choice(["local", "s3", "gcs", "network"]), default="local")
@click.option("--priority", type=int, default=50, help="Priority (0-100, higher = preferred)")
@click.option("--rule", multiple=True, help="Storage rules in JSON format")
def add(name: str, path: str, type: str, priority: int, rule: tuple):
    """Add a new storage location."""
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    
    # Parse rules
    rules = []
    for rule_json in rule:
        try:
            rule_data = json.loads(rule_json)
            rules.append(StorageRule.from_dict(rule_data))
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing rule:[/red] {e}")
            return
    
    # Create location
    location = StorageLocation(
        location_id=None,  # Will be generated
        name=name,
        type=StorageType.from_string(type),
        path=path,
        priority=priority,
        rules=rules
    )
    
    try:
        registered = registry.register_location(location)
        console.print(f"[green]✓[/green] Added storage location: {name}")
        console.print(f"  ID: {registered.location_id}")
        console.print(f"  Type: {type}")
        console.print(f"  Path: {path}")
        console.print(f"  Priority: {priority}")
        if rules:
            console.print(f"  Rules: {len(rules)}")
    except Exception as e:
        console.print(f"[red]Error adding location:[/red] {e}")
    finally:
        registry.close()


@storage.command()
def list():
    """List all storage locations."""
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    
    locations = registry.get_locations()
    if not locations:
        console.print("No storage locations configured.")
        registry.close()
        return
    
    table = Table(title="Storage Locations")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Path")
    table.add_column("Priority", justify="right")
    table.add_column("Status")
    table.add_column("Last Scan")
    
    for loc in locations:
        table.add_row(
            loc.name,
            loc.type.value,
            loc.path,
            str(loc.priority),
            loc.status.value,
            loc.last_scan.strftime("%Y-%m-%d %H:%M") if loc.last_scan else "Never"
        )
    
    console.print(table)
    registry.close()


@storage.command()
@click.argument("location_id")
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
def scan(location_id: str, no_progress: bool):
    """Scan a storage location for assets."""
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    cache = DuckDBSearchCache(Path(config.storage.search_db))
    
    try:
        # Get location
        location = registry.get_location_by_id(UUID(location_id))
        if not location:
            console.print(f"[red]Location not found:[/red] {location_id}")
            return
        
        # Scan location
        scanner = MultiPathScanner(cache, registry)
        
        async def run_scan():
            return await scanner._scan_location(
                location, 
                force_scan=True, 
                show_progress=not no_progress
            )
        
        stats = asyncio.run(run_scan())
        
        console.print(f"[green]✓[/green] Scan complete for {location.name}")
        console.print(f"  Files found: {stats['files_found']}")
        console.print(f"  New files: {stats['new_files']}")
        console.print(f"  Projects: {len(stats['projects'])}")
        
    except Exception as e:
        console.print(f"[red]Error scanning location:[/red] {e}")
    finally:
        registry.close()
        cache.close()


@storage.command()
@click.option("--force", is_flag=True, help="Force re-scan all locations")
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
def discover(force: bool, no_progress: bool):
    """Discover all assets across all storage locations."""
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    cache = DuckDBSearchCache(Path(config.storage.search_db))
    
    try:
        scanner = MultiPathScanner(cache, registry)
        
        async def run_discovery():
            return await scanner.discover_all_assets(
                force_scan=force, 
                show_progress=not no_progress
            )
        
        stats = asyncio.run(run_discovery())
        
        console.print("[green]✓[/green] Discovery complete")
        console.print(f"  Locations scanned: {stats['locations_scanned']}")
        console.print(f"  Total files: {stats['total_files_found']}")
        console.print(f"  New files: {stats['new_files_discovered']}")
        console.print(f"  Projects found: {len(stats['projects_found'])}")
        
        if stats['errors']:
            console.print("[yellow]Errors:[/yellow]")
            for error in stats['errors']:
                console.print(f"  - {error['location']}: {error['error']}")
                
    except Exception as e:
        console.print(f"[red]Error during discovery:[/red] {e}")
    finally:
        registry.close()
        cache.close()


@storage.command()
def stats():
    """Show storage statistics."""
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    
    try:
        stats = registry.get_statistics()
        
        console.print("[bold]Storage Statistics[/bold]")
        console.print(f"Total locations: {stats['total_locations']}")
        console.print(f"Total unique files: {stats['total_unique_files']}")
        console.print(f"Total file instances: {stats['total_file_instances']}")
        console.print(f"Files with multiple copies: {stats['files_with_multiple_copies']}")
        console.print(f"Pending syncs: {stats['pending_syncs']}")
        
        if stats['by_location']:
            console.print("\n[bold]By Location:[/bold]")
            table = Table()
            table.add_column("Location")
            table.add_column("Files", justify="right")
            table.add_column("Size (GB)", justify="right")
            
            for loc in stats['by_location']:
                size_gb = loc['total_size_bytes'] / (1024**3)
                table.add_row(
                    loc['name'],
                    str(loc['file_count']),
                    f"{size_gb:.2f}"
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error getting statistics:[/red] {e}")
    finally:
        registry.close()


@storage.command()
@click.argument("project_name")
@click.option("--type", multiple=True, help="Asset types to include")
def find_project(project_name: str, type: tuple):
    """Find all assets for a project across locations."""
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    cache = DuckDBSearchCache(Path(config.storage.search_db))
    
    try:
        scanner = MultiPathScanner(cache, registry)
        
        async def run_find():
            return await scanner.find_project_assets(
                project_name,
                list(type) if type else None
            )
        
        assets = asyncio.run(run_find())
        
        if not assets:
            console.print(f"No assets found for project: {project_name}")
            return
        
        console.print(f"[green]Found {len(assets)} assets for project {project_name}[/green]")
        
        table = Table()
        table.add_column("File")
        table.add_column("Type")
        table.add_column("Locations")
        
        for asset in assets[:20]:  # Show first 20
            filename = Path(asset['path']).name
            media_type = asset['metadata'].get('media_type', 'unknown') if asset['metadata'] else 'unknown'
            location_count = len(asset['registry_locations'])
            
            table.add_row(
                filename,
                media_type,
                f"{location_count} location(s)"
            )
        
        console.print(table)
        
        if len(assets) > 20:
            console.print(f"\n... and {len(assets) - 20} more")
            
    except Exception as e:
        console.print(f"[red]Error finding project assets:[/red] {e}")
    finally:
        registry.close()
        cache.close()


@storage.command()
@click.option("--location-id", help="Update specific location by ID")
@click.option("--priority", type=int, help="New priority")
@click.option("--status", type=click.Choice(["active", "archived", "offline"]))
def update(location_id: Optional[str], priority: Optional[int], status: Optional[str]):
    """Update a storage location."""
    if not location_id:
        console.print("[red]Please specify --location-id[/red]")
        return
    
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    
    try:
        location = registry.get_location_by_id(UUID(location_id))
        if not location:
            console.print(f"[red]Location not found:[/red] {location_id}")
            return
        
        # Update fields
        updated = False
        if priority is not None:
            location.priority = priority
            updated = True
        
        if status is not None:
            location.status = LocationStatus.from_string(status)
            updated = True
        
        if updated:
            registry.update_location(location)
            console.print(f"[green]✓[/green] Updated location: {location.name}")
        else:
            console.print("No changes to apply")
            
    except Exception as e:
        console.print(f"[red]Error updating location:[/red] {e}")
    finally:
        registry.close()


@storage.command()
def from_config():
    """Initialize storage locations from config file."""
    config = load_config()
    
    if not config.storage.locations:
        console.print("No storage locations defined in configuration")
        return
    
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    
    try:
        added = 0
        for loc_config in config.storage.locations:
            # Parse rules
            rules = []
            for rule_data in loc_config.get("rules", []):
                rules.append(StorageRule.from_dict(rule_data))
            
            # Create location
            location = StorageLocation(
                location_id=None,
                name=loc_config["name"],
                type=StorageType.from_string(loc_config.get("type", "local")),
                path=loc_config["path"],
                priority=loc_config.get("priority", 50),
                rules=rules,
                config=loc_config.get("config", {})
            )
            
            try:
                registry.register_location(location)
                console.print(f"[green]✓[/green] Added: {location.name}")
                added += 1
            except Exception as e:
                console.print(f"[yellow]![/yellow] Skipped {location.name}: {e}")
        
        console.print(f"\nAdded {added} storage locations from config")
        
    except Exception as e:
        console.print(f"[red]Error loading from config:[/red] {e}")
    finally:
        registry.close()


@storage.command()
@click.argument("project_name")
@click.argument("target_location_id")
@click.option("--move", is_flag=True, help="Move files instead of copying")
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
def consolidate(project_name: str, target_location_id: str, move: bool, no_progress: bool):
    """Consolidate all project assets to a single location."""
    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    cache = DuckDBSearchCache(Path(config.storage.search_db))
    
    try:
        scanner = MultiPathScanner(cache, registry)
        
        async def run_consolidate():
            return await scanner.consolidate_project(
                project_name,
                target_location_id,
                move_files=move,
                show_progress=not no_progress
            )
        
        stats = asyncio.run(run_consolidate())
        
        console.print(f"[green]✓[/green] Consolidation complete for project {project_name}")
        console.print(f"  Files found: {stats['files_found']}")
        if move:
            console.print(f"  Files moved: {stats['files_moved']}")
        else:
            console.print(f"  Files copied: {stats['files_copied']}")
        
        if stats['errors']:
            console.print("[yellow]Errors:[/yellow]")
            for error in stats['errors']:
                console.print(f"  - {error['file']}: {error['error']}")
                
    except Exception as e:
        console.print(f"[red]Error during consolidation:[/red] {e}")
    finally:
        registry.close()
        cache.close()