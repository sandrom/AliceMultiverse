"""CLI commands for the comparison system."""

import click
from pathlib import Path
import logging

from .elo_system import ComparisonManager
from .populate import populate_from_directory, populate_default_directories

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Comparison system commands."""


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("-r", "--recursive", is_flag=True, help="Search recursively")
@click.option("-l", "--limit", type=int, help="Maximum number of assets to add")
def populate(directory: str, recursive: bool, limit: int):
    """Populate comparison system with images from a directory."""
    manager = ComparisonManager()
    dir_path = Path(directory)
    
    click.echo(f"Scanning directory: {dir_path}")
    count = populate_from_directory(dir_path, manager, recursive=recursive, limit=limit)
    click.echo(f"Added {count} assets to comparison system")


@cli.command()
@click.option("-l", "--limit", type=int, help="Maximum number of assets to add")
def populate_default(limit: int):
    """Populate from default organized directories."""
    manager = ComparisonManager()
    
    click.echo("Populating from default directories...")
    count = populate_default_directories(manager, limit=limit)
    click.echo(f"Added {count} assets to comparison system")


@cli.command()
def stats():
    """Show current model rankings."""
    manager = ComparisonManager()
    ratings = manager.get_ratings()
    
    if not ratings:
        click.echo("No ratings found. Add some assets first.")
        return
    
    click.echo("\nModel Rankings:")
    click.echo("-" * 60)
    click.echo(f"{'Rank':<6} {'Model':<20} {'Rating':<10} {'Games':<8} {'Win%':<8}")
    click.echo("-" * 60)
    
    for i, rating in enumerate(ratings, 1):
        click.echo(
            f"{i:<6} {rating.model:<20} {rating.rating:<10.0f} "
            f"{rating.comparison_count:<8} {rating.win_rate*100:<8.1f}"
        )


@cli.command()
def reset():
    """Reset all comparisons and ratings."""
    if not click.confirm("This will delete all comparison data. Continue?"):
        return
    
    manager = ComparisonManager()
    db_path = manager.db_path
    
    if db_path.exists():
        db_path.unlink()
        click.echo("Comparison database reset.")
    else:
        click.echo("No database found.")


if __name__ == "__main__":
    cli()