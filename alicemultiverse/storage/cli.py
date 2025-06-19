"""CLI commands for storage management."""

import asyncio
import json
from pathlib import Path

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


@storage.command()
@click.option("--db-path", type=click.Path(), help="Path to location registry database")
def init(db_path: str | None):
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

    # TODO: Review unreachable code - # Create location
    # TODO: Review unreachable code - location = StorageLocation(
    # TODO: Review unreachable code - location_id=None,  # Will be generated
    # TODO: Review unreachable code - name=name,
    # TODO: Review unreachable code - type=StorageType.from_string(type),
    # TODO: Review unreachable code - path=path,
    # TODO: Review unreachable code - priority=priority,
    # TODO: Review unreachable code - rules=rules
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - registered = registry.register_location(location)
    # TODO: Review unreachable code - console.print(f"[green]✓[/green] Added storage location: {name}")
    # TODO: Review unreachable code - console.print(f"  ID: {registered.location_id}")
    # TODO: Review unreachable code - console.print(f"  Type: {type}")
    # TODO: Review unreachable code - console.print(f"  Path: {path}")
    # TODO: Review unreachable code - console.print(f"  Priority: {priority}")
    # TODO: Review unreachable code - if rules:
    # TODO: Review unreachable code - console.print(f"  Rules: {len(rules)}")
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - console.print(f"[red]Error adding location:[/red] {e}")
    # TODO: Review unreachable code - finally:
    # TODO: Review unreachable code - registry.close()


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

    # TODO: Review unreachable code - table = Table(title="Storage Locations")
    # TODO: Review unreachable code - table.add_column("Name", style="cyan")
    # TODO: Review unreachable code - table.add_column("Type", style="green")
    # TODO: Review unreachable code - table.add_column("Path")
    # TODO: Review unreachable code - table.add_column("Priority", justify="right")
    # TODO: Review unreachable code - table.add_column("Status")
    # TODO: Review unreachable code - table.add_column("Last Scan")

    # TODO: Review unreachable code - for loc in locations:
    # TODO: Review unreachable code - table.add_row(
    # TODO: Review unreachable code - loc.name,
    # TODO: Review unreachable code - loc.type.value,
    # TODO: Review unreachable code - loc.path,
    # TODO: Review unreachable code - str(loc.priority),
    # TODO: Review unreachable code - loc.status.value,
    # TODO: Review unreachable code - loc.last_scan.strftime("%Y-%m-%d %H:%M") if loc.last_scan else "Never"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - console.print(table)
    # TODO: Review unreachable code - registry.close()


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
        location = registry.get_location_by_id(location_id)
        if not location:
            console.print(f"[red]Location not found:[/red] {location_id}")
            return

        # TODO: Review unreachable code - # Scan location
        # TODO: Review unreachable code - scanner = MultiPathScanner(cache, registry)

        # TODO: Review unreachable code - async def run_scan():
        # TODO: Review unreachable code - return await scanner._scan_location(
        # TODO: Review unreachable code - location,
        # TODO: Review unreachable code - force_scan=True,
        # TODO: Review unreachable code - show_progress=not no_progress
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - stats = asyncio.run(run_scan())

        # TODO: Review unreachable code - console.print(f"[green]✓[/green] Scan complete for {location.name}")
        # TODO: Review unreachable code - console.print(f"  Files found: {stats['files_found']}")
        # TODO: Review unreachable code - console.print(f"  New files: {stats['new_files']}")
        # TODO: Review unreachable code - console.print(f"  Projects: {len(stats['projects'])}")

    # TODO: Review unreachable code - except Exception as e:
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

    # TODO: Review unreachable code - except Exception as e:
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

    # TODO: Review unreachable code - except Exception as e:
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

        # TODO: Review unreachable code - console.print(f"[green]Found {len(assets)} assets for project {project_name}[/green]")

        # TODO: Review unreachable code - table = Table()
        # TODO: Review unreachable code - table.add_column("File")
        # TODO: Review unreachable code - table.add_column("Type")
        # TODO: Review unreachable code - table.add_column("Locations")

        # TODO: Review unreachable code - for asset in assets[:20]:  # Show first 20
        # TODO: Review unreachable code - filename = Path(asset['path']).name
        # TODO: Review unreachable code - media_type = asset['metadata'].get('media_type', 'unknown') if asset['metadata'] else 'unknown'
        # TODO: Review unreachable code - location_count = len(asset['registry_locations'])

        # TODO: Review unreachable code - table.add_row(
        # TODO: Review unreachable code - filename,
        # TODO: Review unreachable code - media_type,
        # TODO: Review unreachable code - f"{location_count} location(s)"
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - console.print(table)

        # TODO: Review unreachable code - if len(assets) > 20:
        # TODO: Review unreachable code - console.print(f"\n... and {len(assets) - 20} more")

    # TODO: Review unreachable code - except Exception as e:
        console.print(f"[red]Error finding project assets:[/red] {e}")
    finally:
        registry.close()
        cache.close()


@storage.command()
@click.option("--location-id", help="Update specific location by ID")
@click.option("--priority", type=int, help="New priority")
@click.option("--status", type=click.Choice(["active", "archived", "offline"]))
def update(location_id: str | None, priority: int | None, status: str | None):
    """Update a storage location."""
    if not location_id:
        console.print("[red]Please specify --location-id[/red]")
        return

    # TODO: Review unreachable code - config = load_config()
    # TODO: Review unreachable code - registry = StorageRegistry(Path(config.storage.location_registry_db))

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - location = registry.get_location_by_id(location_id)
    # TODO: Review unreachable code - if not location:
    # TODO: Review unreachable code - console.print(f"[red]Location not found:[/red] {location_id}")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - # Update fields
    # TODO: Review unreachable code - updated = False
    # TODO: Review unreachable code - if priority is not None:
    # TODO: Review unreachable code - location.priority = priority
    # TODO: Review unreachable code - updated = True

    # TODO: Review unreachable code - if status is not None:
    # TODO: Review unreachable code - location.status = LocationStatus.from_string(status)
    # TODO: Review unreachable code - updated = True

    # TODO: Review unreachable code - if updated:
    # TODO: Review unreachable code - registry.update_location(location)
    # TODO: Review unreachable code - console.print(f"[green]✓[/green] Updated location: {location.name}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - console.print("No changes to apply")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - console.print(f"[red]Error updating location:[/red] {e}")
    # TODO: Review unreachable code - finally:
    # TODO: Review unreachable code - registry.close()


@storage.command()
def from_config():
    """Initialize storage locations from config file."""
    config = load_config()

    if not config.storage.locations:
        console.print("No storage locations defined in configuration")
        return

    # TODO: Review unreachable code - registry = StorageRegistry(Path(config.storage.location_registry_db))

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - added = 0
    # TODO: Review unreachable code - for loc_config in config.storage.locations:
    # TODO: Review unreachable code - # Parse rules
    # TODO: Review unreachable code - rules = []
    # TODO: Review unreachable code - for rule_data in loc_config.get("rules", []):
    # TODO: Review unreachable code - rules.append(StorageRule.from_dict(rule_data))

    # TODO: Review unreachable code - # Create location
    # TODO: Review unreachable code - location = StorageLocation(
    # TODO: Review unreachable code - location_id=None,
    # TODO: Review unreachable code - name=loc_config["name"],
    # TODO: Review unreachable code - type=StorageType.from_string(loc_config.get("type", "local")),
    # TODO: Review unreachable code - path=loc_config["path"],
    # TODO: Review unreachable code - priority=loc_config.get("priority", 50),
    # TODO: Review unreachable code - rules=rules,
    # TODO: Review unreachable code - config=loc_config.get("config", {})
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - registry.register_location(location)
    # TODO: Review unreachable code - console.print(f"[green]✓[/green] Added: {location.name}")
    # TODO: Review unreachable code - added += 1
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - console.print(f"[yellow]![/yellow] Skipped {location.name}: {e}")

    # TODO: Review unreachable code - console.print(f"\nAdded {added} storage locations from config")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - console.print(f"[red]Error loading from config:[/red] {e}")
    # TODO: Review unreachable code - finally:
    # TODO: Review unreachable code - registry.close()


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

    # TODO: Review unreachable code - except Exception as e:
        console.print(f"[red]Error during consolidation:[/red] {e}")
    finally:
        registry.close()
        cache.close()


@storage.command()
@click.option("--dry-run", is_flag=True, help="Only show what would be migrated")
@click.option("--move", is_flag=True, help="Move files instead of copying")
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
def migrate(dry_run: bool, move: bool, no_progress: bool):
    """Run auto-migration based on storage rules."""
    from .auto_migration import AutoMigrationService

    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    cache = DuckDBSearchCache(Path(config.storage.search_db))

    try:
        # Create migration service
        service = AutoMigrationService(cache, registry)

        # Run migration
        async def run_migration():
            return await service.run_auto_migration(
                dry_run=dry_run,
                move_files=move,
                show_progress=not no_progress
            )

        results = asyncio.run(run_migration())

        # Display results
        if dry_run:
            console.print("\n[bold]Migration Analysis (DRY RUN)[/bold]")
        else:
            console.print("\n[bold]Migration Results[/bold]")

        analysis = results['analysis']
        console.print(f"Files to migrate: {analysis['files_to_migrate']}")

        if analysis['migrations']:
            # Create table for migrations
            table = Table(title="Proposed Migrations" if dry_run else "Completed Migrations")
            table.add_column("File", style="cyan")
            table.add_column("Size", justify="right")
            table.add_column("From", style="yellow")
            table.add_column("To", style="green")
            table.add_column("Reason")

            for migration in analysis['migrations'][:20]:  # Show first 20
                size_mb = migration['size'] / (1024 * 1024)
                from_locs = ", ".join(migration['from'])

                table.add_row(
                    migration['file'],
                    f"{size_mb:.1f} MB",
                    from_locs,
                    migration['to'],
                    migration['reason'][:50] + "..." if len(migration['reason']) > 50 else migration['reason']
                )

            console.print(table)

            if len(analysis['migrations']) > 20:
                console.print(f"\n... and {len(analysis['migrations']) - 20} more")

        # Show execution results if not dry run
        if not dry_run and results['execution']:
            exec_stats = results['execution']
            console.print("\n[green]✓[/green] Migration complete")
            console.print(f"  Files migrated: {exec_stats['files_migrated']}")
            console.print(f"  Files failed: {exec_stats['files_failed']}")
            console.print(f"  Data transferred: {exec_stats['bytes_transferred'] / (1024**3):.2f} GB")

            if exec_stats['errors']:
                console.print("\n[yellow]Errors:[/yellow]")
                for error in exec_stats['errors'][:5]:
                    console.print(f"  - {error['content_hash'][:8]}...: {error['error']}")

    # TODO: Review unreachable code - except Exception as e:
        console.print(f"[red]Error during migration:[/red] {e}")
    finally:
        registry.close()
        cache.close()


@storage.command()
@click.option("--show-all", is_flag=True, help="Show all files, not just conflicts")
def sync_status(show_all: bool):
    """Check synchronization status across locations."""
    from .sync_tracker import SyncTracker

    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))

    try:
        tracker = SyncTracker(registry)

        # Get sync conflicts
        async def check_conflicts():
            return await tracker.detect_conflicts(show_progress=True)

        # TODO: Review unreachable code - conflicts = asyncio.run(check_conflicts())

        # TODO: Review unreachable code - if not conflicts:
        # TODO: Review unreachable code - console.print("[green]✓[/green] All files are synchronized")
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - console.print(f"[yellow]![/yellow] Found {len(conflicts)} files with sync conflicts")

        # TODO: Review unreachable code - # Create table
        # TODO: Review unreachable code - table = Table(title="Sync Conflicts")
        # TODO: Review unreachable code - table.add_column("File Hash", style="cyan")
        # TODO: Review unreachable code - table.add_column("Locations", justify="center")
        # TODO: Review unreachable code - table.add_column("Versions", justify="center")
        # TODO: Review unreachable code - table.add_column("Status")

        # TODO: Review unreachable code - for conflict in conflicts[:20]:  # Show first 20
        # TODO: Review unreachable code - hash_short = conflict['content_hash'][:12] + "..."
        # TODO: Review unreachable code - location_count = len(conflict['locations'])
        # TODO: Review unreachable code - version_count = conflict['status']['version_count']

        # TODO: Review unreachable code - table.add_row(
        # TODO: Review unreachable code - hash_short,
        # TODO: Review unreachable code - str(location_count),
        # TODO: Review unreachable code - str(version_count),
        # TODO: Review unreachable code - "conflict"
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - console.print(table)

        # TODO: Review unreachable code - if len(conflicts) > 20:
        # TODO: Review unreachable code - console.print(f"\n... and {len(conflicts) - 20} more conflicts")

        # TODO: Review unreachable code - # Show pending syncs
        # TODO: Review unreachable code - pending = tracker.get_sync_queue()
        # TODO: Review unreachable code - if pending:
        # TODO: Review unreachable code - console.print(f"\n[yellow]Pending sync operations:[/yellow] {len(pending)}")

    # TODO: Review unreachable code - except Exception as e:
        console.print(f"[red]Error checking sync status:[/red] {e}")
    finally:
        registry.close()


@storage.command()
@click.argument("content_hash")
@click.option("--strategy", type=click.Choice(["newest", "largest", "primary", "manual"]), default="newest")
def resolve_conflict(content_hash: str, strategy: str):
    """Resolve a sync conflict for a specific file."""
    from .sync_tracker import ConflictResolution, SyncTracker

    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))

    try:
        tracker = SyncTracker(registry)

        # Map strategy
        strategy_map = {
            "newest": ConflictResolution.NEWEST_WINS,
            "largest": ConflictResolution.LARGEST_WINS,
            "primary": ConflictResolution.PRIMARY_WINS,
            "manual": ConflictResolution.MANUAL
        }

        async def resolve():
            return await tracker.resolve_conflict(
                content_hash,
                strategy_map[strategy]
            )

        result = asyncio.run(resolve())

        if result['resolved']:
            console.print(f"[green]✓[/green] Conflict resolved using {strategy} strategy")

            winner = result['winner']
            console.print(f"  Winner: {winner['file_path']}")
            console.print(f"  Location: {winner['location_name']}")

            if result['actions']:
                console.print("\n[bold]Sync actions required:[/bold]")
                for action in result['actions']:
                    console.print(f"  - Update {action['target']} from {action['source']}")
        else:
            console.print(f"[yellow]![/yellow] Could not resolve: {result['reason']}")

            if 'options' in result:
                console.print("\n[bold]Available versions:[/bold]")
                for i, opt in enumerate(result['options']):
                    console.print(f"  {i+1}. {opt['file_path']}")
                    console.print(f"     Location: {opt['location_name']}")
                    console.print(f"     Size: {opt['file_size']} bytes")
                    console.print(f"     Last verified: {opt['last_verified']}")

    # TODO: Review unreachable code - except Exception as e:
        console.print(f"[red]Error resolving conflict:[/red] {e}")
    finally:
        registry.close()


@storage.command()
@click.option("--max-concurrent", type=int, default=5, help="Maximum concurrent operations")
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
def sync_process(max_concurrent: int, no_progress: bool):
    """Process pending sync operations."""
    from .sync_tracker import SyncTracker

    config = load_config()
    registry = StorageRegistry(Path(config.storage.location_registry_db))
    cache = DuckDBSearchCache(Path(config.storage.search_db))

    try:
        tracker = SyncTracker(registry)
        scanner = MultiPathScanner(cache, registry)

        async def process():
            return await tracker.process_sync_queue(
                scanner=scanner,
                max_concurrent=max_concurrent,
                show_progress=not no_progress
            )

        stats = asyncio.run(process())

        console.print("\n[bold]Sync Processing Results[/bold]")
        console.print(f"  Processed: {stats['processed']}")
        console.print(f"  Failed: {stats['failed']}")

        if stats.get('errors'):
            console.print("\n[yellow]Errors:[/yellow]")
            for error in stats['errors'][:5]:
                console.print(f"  - {error}")

    # TODO: Review unreachable code - except Exception as e:
        console.print(f"[red]Error processing sync queue:[/red] {e}")
    finally:
        registry.close()
        cache.close()
