"""CLI commands for deduplication system."""

import click
import logging
from pathlib import Path
from typing import Optional

from . import DuplicateFinder, SimilarityIndex

logger = logging.getLogger(__name__)


@click.group(name="dedup")
def dedup_cli():
    """Advanced deduplication commands."""
    pass


@dedup_cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--threshold", "-t", default=0.9, help="Similarity threshold (0.8-1.0)")
@click.option("--recursive/--no-recursive", "-r/-R", default=True, help="Scan subdirectories")
@click.option("--include-similar/--exact-only", "-s/-e", default=True, help="Include similar images")
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
def find(directory: str, threshold: float, recursive: bool, include_similar: bool, output: Optional[str]):
    """Find duplicate and similar images."""
    scan_dir = Path(directory)
    
    click.echo(f"Scanning {scan_dir} for duplicates...")
    click.echo(f"Similarity threshold: {threshold}")
    
    # Create finder
    finder = DuplicateFinder(similarity_threshold=threshold)
    
    # Scan
    with click.progressbar(length=100, label="Scanning") as bar:
        exact_count, similar_count = finder.scan_directory(scan_dir, recursive=recursive)
        bar.update(100)
    
    # Get report
    report = finder.get_duplicate_report()
    
    # Display results
    click.echo(f"\nFound {exact_count} exact duplicates")
    if include_similar:
        click.echo(f"Found {similar_count} similar images")
    
    # Show details
    if report['exact_duplicates']['groups']:
        click.echo("\nExact Duplicates:")
        for i, group in enumerate(report['exact_duplicates']['groups'][:10]):  # Show first 10
            click.echo(f"  Group {i+1}:")
            click.echo(f"    Master: {group['master']}")
            click.echo(f"    Duplicates: {len(group['duplicates'])}")
            click.echo(f"    Savings: {group['potential_savings'] / 1_000_000:.2f} MB")
    
    if include_similar and report['similar_images']['groups']:
        click.echo("\nSimilar Images:")
        for i, group in enumerate(report['similar_images']['groups'][:10]):  # Show first 10
            click.echo(f"  Group {i+1}:")
            click.echo(f"    Master: {group['master']}")
            click.echo(f"    Similar: {len(group['duplicates'])} images")
            click.echo(f"    Avg similarity: {sum(group['similarity_scores'].values()) / len(group['similarity_scores']):.2%}")
    
    click.echo(f"\nTotal potential savings: {report['potential_savings'] / 1_000_000:.2f} MB")
    
    # Save report if requested
    if output:
        import json
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        click.echo(f"Report saved to: {output}")


@dedup_cli.command()
@click.argument("report", type=click.Path(exists=True))
@click.option("--strategy", "-s", type=click.Choice(["safe", "aggressive"]), default="safe", 
              help="Removal strategy")
@click.option("--backup", "-b", type=click.Path(), help="Backup directory")
@click.option("--dry-run/--execute", "-n/-x", default=True, help="Dry run or execute")
@click.confirmation_option(prompt="Are you sure you want to remove duplicates?")
def remove(report: str, strategy: str, backup: Optional[str], dry_run: bool):
    """Remove duplicate images based on report."""
    import json
    
    # Load report
    with open(report, 'r') as f:
        report_data = json.load(f)
    
    # Create finder
    finder = DuplicateFinder()
    
    # Restore state from report
    for group in report_data.get('exact_duplicates', {}).get('groups', []):
        master = Path(group['master'])
        duplicates = [Path(p) for p in group['duplicates']]
        file_hash = group.get('hash', 'unknown')
        finder.exact_duplicates[file_hash] = [master] + duplicates
    
    # Remove duplicates
    backup_path = Path(backup) if backup else None
    stats = finder.remove_duplicates(
        dry_run=dry_run,
        backup_dir=backup_path,
        remove_similar=(strategy == "aggressive")
    )
    
    # Show results
    action = "Would remove" if dry_run else "Removed"
    click.echo(f"{action} {stats['exact_removed']} exact duplicates")
    if strategy == "aggressive":
        click.echo(f"{action} {stats['similar_removed']} similar images")
    click.echo(f"Space {'would be' if dry_run else ''} freed: {stats['space_freed'] / 1_000_000:.2f} MB")
    
    if stats['errors'] > 0:
        click.echo(f"Errors: {stats['errors']}", err=True)


@dedup_cli.command()
@click.argument("directories", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Index save path")
@click.option("--type", "-t", type=click.Choice(["Flat", "IVF", "HNSW"]), default="IVF", 
              help="Index type")
def index(directories: tuple, output: Optional[str], type: str):
    """Build similarity search index."""
    # Collect images
    image_paths = []
    for directory in directories:
        scan_dir = Path(directory)
        click.echo(f"Scanning {scan_dir}...")
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            image_paths.extend(scan_dir.rglob(f"*{ext}"))
            image_paths.extend(scan_dir.rglob(f"*{ext.upper()}"))
    
    click.echo(f"Found {len(image_paths)} images")
    
    if not image_paths:
        click.echo("No images found", err=True)
        return
    
    # Create index
    index_obj = SimilarityIndex(index_type=type)
    
    # Build
    click.echo("Building index...")
    with click.progressbar(image_paths, label="Extracting features") as bar:
        cache_dir = Path.home() / ".alice" / "cache" / "similarity"
        indexed_count = index_obj.build_index(list(bar), cache_dir=cache_dir)
    
    # Save
    if output:
        index_path = Path(output)
    else:
        index_path = Path.home() / ".alice" / "similarity_index"
    
    index_obj.save_index(index_path)
    click.echo(f"Index saved to: {index_path}")
    click.echo(f"Indexed {indexed_count} images")


@dedup_cli.command()
@click.argument("image", type=click.Path(exists=True))
@click.option("--index", "-i", type=click.Path(), help="Index path")
@click.option("--count", "-k", default=10, help="Number of results")
@click.option("--threshold", "-t", default=0.7, help="Minimum similarity")
def search(image: str, index: Optional[str], count: int, threshold: float):
    """Search for similar images."""
    query_path = Path(image)
    
    # Load index
    if index:
        index_path = Path(index)
    else:
        index_path = Path.home() / ".alice" / "similarity_index"
    
    if not index_path.with_suffix('.faiss').exists():
        click.echo("Index not found. Build it first with 'alice dedup index'", err=True)
        return
    
    # Create and load index
    index_obj = SimilarityIndex()
    index_obj.load_index(index_path)
    
    click.echo(f"Searching {index_obj.index.ntotal} images...")
    
    # Search
    results = index_obj.search(query_path, k=count, include_self=False)
    
    # Display results
    click.echo(f"\nImages similar to: {query_path.name}")
    for i, result in enumerate(results):
        if result.similarity >= threshold:
            click.echo(f"{i+1:2d}. {result.path.name}")
            click.echo(f"    Path: {result.path}")
            click.echo(f"    Similarity: {result.similarity:.1%}")


# Add to main CLI
def register_commands(cli):
    """Register deduplication commands with main CLI."""
    cli.add_command(dedup_cli)