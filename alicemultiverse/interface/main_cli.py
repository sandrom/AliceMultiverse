"""Command-line interface for AliceMultiverse."""

import argparse
import logging
import sys
from pathlib import Path

from omegaconf import DictConfig

from ..core.config import load_config
from ..core.exceptions import AliceMultiverseError, ConfigurationError
from ..core.logging import setup_logging
from ..core.structured_logging import setup_structured_logging
from ..version import __version__

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="AliceMultiverse Debug CLI - For Development and Debugging Only\n\n⚠️  DEPRECATION WARNING: Direct CLI usage is deprecated!\nAlice is now an AI-native service designed to be used through AI assistants.\n\nFor normal usage, configure Alice with Claude Desktop or another AI assistant.\nSee: https://github.com/yourusername/AliceMultiverse/docs/integrations/claude-desktop.md\n\nThis CLI is maintained only for debugging and development purposes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Debug Examples:
  %(prog)s --check-deps              # Check system dependencies
  %(prog)s --dry-run --verbose       # Debug organization logic
  %(prog)s keys setup                # Configure API keys
  %(prog)s mcp-server                # Start MCP server
  
For normal usage, use Alice through an AI assistant instead.
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Cost subcommand for cost tracking
    cost_parser = subparsers.add_parser("cost", help="Cost tracking and budget management")
    cost_subparsers = cost_parser.add_subparsers(dest="cost_command", help="Cost management commands")
    
    # Cost - report
    cost_report = cost_subparsers.add_parser("report", help="Show cost report")
    cost_report.add_argument("--days", type=int, default=30, help="Number of days to include")
    
    # Cost - set-budget
    cost_budget = cost_subparsers.add_parser("set-budget", help="Set spending budget")
    cost_budget.add_argument("--daily", type=float, help="Daily budget limit (USD)")
    cost_budget.add_argument("--monthly", type=float, help="Monthly budget limit (USD)")
    cost_budget.add_argument("--alert", type=float, default=0.8, help="Alert threshold (0-1)")
    
    # Cost - providers
    cost_providers = cost_subparsers.add_parser("providers", help="Compare provider costs")
    cost_providers.add_argument("--category", choices=["understanding", "generation", "enhancement", "audio"], 
                               help="Filter by category")
    
    # Keys subcommand
    keys_parser = subparsers.add_parser("keys", help="Manage API keys")
    keys_subparsers = keys_parser.add_subparsers(
        dest="keys_command", help="Key management commands"
    )

    # Keys - set
    keys_set = keys_subparsers.add_parser("set", help="Set an API key")
    keys_set.add_argument(
        "key_name",
        choices=["sightengine_user", "sightengine_secret", "anthropic_api_key"],
        help="API key to set",
    )
    keys_set.add_argument(
        "--method",
        choices=["keychain", "config", "env"],
        default="keychain",
        help="Storage method (default: keychain on macOS)",
    )

    # Keys - get
    keys_get = keys_subparsers.add_parser("get", help="Get an API key")
    keys_get.add_argument(
        "key_name",
        choices=["sightengine_user", "sightengine_secret", "anthropic_api_key"],
        help="API key to get",
    )

    # Keys - delete
    keys_delete = keys_subparsers.add_parser("delete", help="Delete an API key")
    keys_delete.add_argument(
        "key_name",
        choices=["sightengine_user", "sightengine_secret", "anthropic_api_key"],
        help="API key to delete",
    )

    # Keys - list
    keys_list = keys_subparsers.add_parser("list", help="List stored API keys")

    # Keys - setup
    keys_setup = keys_subparsers.add_parser("setup", help="Interactive setup wizard")
    
    # Setup subcommand (first-run wizard)
    setup_parser = subparsers.add_parser(
        "setup", 
        help="Run first-time setup wizard"
    )
    setup_parser.add_argument(
        "--reconfigure", 
        action="store_true", 
        help="Reconfigure even if already set up"
    )
    
    # Recreate subcommand
    recreate_parser = subparsers.add_parser("recreate", help="Recreate AI generations")
    recreate_subparsers = recreate_parser.add_subparsers(
        dest="recreate_command", help="Recreation commands"
    )
    
    # Recreate - inspect
    recreate_inspect = recreate_subparsers.add_parser("inspect", help="Inspect generation metadata")
    recreate_inspect.add_argument("file_path", help="Path to media file")
    
    # Recreate - recreate
    recreate_recreate = recreate_subparsers.add_parser("recreate", help="Recreate a generation")
    recreate_recreate.add_argument("asset_id", help="Asset ID or file path")
    recreate_recreate.add_argument("--provider", help="Override provider")
    recreate_recreate.add_argument("--model", help="Override model")
    recreate_recreate.add_argument("-o", "--output", help="Output path")
    recreate_recreate.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")
    
    # Recreate - catalog
    recreate_catalog = recreate_subparsers.add_parser("catalog", help="Catalog generations in directory")
    recreate_catalog.add_argument("directory", help="Directory to catalog")
    recreate_catalog.add_argument("-r", "--recursive", action="store_true", help="Search recursively")

    # Interface subcommand (for AI interaction demo)
    interface_parser = subparsers.add_parser(
        "interface", help="Start Alice interface for AI interaction"
    )
    interface_parser.add_argument(
        "--demo", action="store_true", help="Run demonstration of AI interaction"
    )
    interface_parser.add_argument(
        "--structured", action="store_true", help="Use structured interface (recommended)"
    )

    # MCP server subcommand
    mcp_parser = subparsers.add_parser("mcp-server", help="Start MCP server for AI integration")
    mcp_parser.add_argument(
        "--port", type=int, help="Port to run on (for TCP mode, not implemented yet)"
    )
    
    # Metrics server subcommand
    metrics_parser = subparsers.add_parser("metrics-server", help="Start Prometheus metrics server")
    metrics_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    metrics_parser.add_argument(
        "--port", type=int, default=9090, help="Port to listen on (default: 9090)"
    )
    
    # Comparison subcommand with subcommands
    comparison_parser = subparsers.add_parser("comparison", help="Model comparison system")
    comparison_subparsers = comparison_parser.add_subparsers(
        dest="comparison_command", help="Comparison commands"
    )
    
    # Comparison - server
    comparison_server = comparison_subparsers.add_parser("server", help="Start web interface")
    comparison_server.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    comparison_server.add_argument(
        "--port", type=int, default=8000, help="Port to listen on (default: 8000)"
    )
    comparison_server.add_argument(
        "--populate-test-data", action="store_true", help="Populate with test data (development only)"
    )
    
    # Comparison - populate
    comparison_populate = comparison_subparsers.add_parser("populate", help="Populate with images")
    comparison_populate.add_argument("directory", help="Directory to scan")
    comparison_populate.add_argument("-r", "--recursive", action="store_true", help="Search recursively")
    comparison_populate.add_argument("-l", "--limit", type=int, help="Maximum number to add")
    
    # Comparison - populate-default
    comparison_populate_default = comparison_subparsers.add_parser("populate-default", help="Populate from default dirs")
    comparison_populate_default.add_argument("-l", "--limit", type=int, help="Maximum number to add")
    
    # Comparison - stats
    comparison_stats = comparison_subparsers.add_parser("stats", help="Show model rankings")
    
    # Comparison - reset
    comparison_reset = comparison_subparsers.add_parser("reset", help="Reset all comparison data")
    
    # Index subcommand for search index management
    index_parser = subparsers.add_parser("index", help="Manage search index")
    index_subparsers = index_parser.add_subparsers(
        dest="index_command", help="Index management commands"
    )
    
    # Index - rebuild
    index_rebuild = index_subparsers.add_parser("rebuild", help="Rebuild search index from files")
    index_rebuild.add_argument(
        "paths", nargs="+", help="Paths to scan for media files"
    )
    index_rebuild.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )
    
    # Index - update
    index_update = index_subparsers.add_parser("update", help="Update index with new/modified files")
    index_update.add_argument(
        "path", help="Path to scan for updates"
    )
    
    # Index - verify
    index_verify = index_subparsers.add_parser("verify", help="Verify index integrity")
    
    # Index - stats
    index_stats = index_subparsers.add_parser("stats", help="Show index statistics")
    
    # Storage subcommand for multi-path storage management
    storage_parser = subparsers.add_parser("storage", help="Manage storage locations")
    storage_subparsers = storage_parser.add_subparsers(
        dest="storage_command", help="Storage management commands"
    )
    
    # Storage - init
    storage_init = storage_subparsers.add_parser("init", help="Initialize storage registry")
    storage_init.add_argument("--db-path", help="Path to location registry database")
    
    # Storage - add
    storage_add = storage_subparsers.add_parser("add", help="Add a storage location")
    storage_add.add_argument("--name", required=True, help="Name of the storage location")
    storage_add.add_argument("--path", required=True, help="Path to the storage location")
    storage_add.add_argument("--type", choices=["local", "s3", "gcs", "network"], default="local")
    storage_add.add_argument("--priority", type=int, default=50, help="Priority (0-100)")
    storage_add.add_argument("--rule", action="append", help="Storage rule in JSON format")
    
    # Storage - list
    storage_list = storage_subparsers.add_parser("list", help="List storage locations")
    
    # Storage - scan
    storage_scan = storage_subparsers.add_parser("scan", help="Scan a storage location")
    storage_scan.add_argument("location_id", help="Location ID to scan")
    
    # Storage - discover
    storage_discover = storage_subparsers.add_parser("discover", help="Discover all assets")
    storage_discover.add_argument("--force", action="store_true", help="Force re-scan")
    
    # Storage - stats
    storage_stats = storage_subparsers.add_parser("stats", help="Show storage statistics")
    
    # Storage - find-project
    storage_find = storage_subparsers.add_parser("find-project", help="Find project assets")
    storage_find.add_argument("project_name", help="Project name")
    storage_find.add_argument("--type", action="append", help="Asset types to include")
    
    # Storage - update
    storage_update = storage_subparsers.add_parser("update", help="Update storage location")
    storage_update.add_argument("--location-id", help="Location ID")
    storage_update.add_argument("--priority", type=int, help="New priority")
    storage_update.add_argument("--status", choices=["active", "archived", "offline"])
    
    # Storage - from-config
    storage_from_config = storage_subparsers.add_parser("from-config", help="Load from config")

    # Directory arguments
    parser.add_argument(
        "-i",
        "--inbox",
        "--input",
        dest="inbox",
        help="Input directory containing media to organize",
    )

    parser.add_argument(
        "-o", "--output", "--organized", dest="output", help="Output directory for organized media"
    )

    parser.add_argument(
        "-c", "--config", help="Path to configuration file (default: settings.yaml)"
    )

    # Processing options
    parser.add_argument(
        "-m", "--move", action="store_true", help="Move files instead of copying them"
    )

    parser.add_argument(
        "-n",
        "--dry-run",
        "--preview",
        dest="dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )

    parser.add_argument(
        "-f",
        "--force",
        "--force-reindex",
        dest="force_reindex",
        action="store_true",
        help="Bypass cache and force re-analysis of all files",
    )

    parser.add_argument(
        "-Q",
        "--quality",
        "--assess-quality",
        dest="quality",
        action="store_true",
        help="Enable BRISQUE quality assessment for images",
    )

    parser.add_argument(
        "-u",
        "--understand",
        "--understanding",
        dest="understand",
        action="store_true",
        help="Enable AI understanding to analyze and tag images (costs apply)",
    )
    
    parser.add_argument(
        "--providers",
        help="AI providers to use for understanding (comma-separated: google,deepseek,anthropic,openai)",
    )

    parser.add_argument(
        "-w",
        "--watch",
        "--monitor",
        dest="watch",
        action="store_true",
        help="Watch mode: continuously monitor for new files",
    )

    parser.add_argument(
        "--enhanced-metadata",
        action="store_true",
        help="Enable enhanced metadata extraction for AI navigation (experimental)",
    )

    # Pipeline options
    parser.add_argument(
        "--pipeline",
        choices=[
            # Named presets
            "basic",
            "standard",
            "premium",
            # Explicit combinations
            "brisque",
            "brisque-sightengine",
            "brisque-claude",
            "brisque-sightengine-claude",
            "full",
            # Custom
            "custom",
        ],
        help="Quality pipeline - 4 main options: "
        "brisque (free), brisque-sightengine ($0.001/image), "
        "brisque-claude (~$0.002/image), brisque-sightengine-claude (~$0.003/image). "
        "Aliases: basic=brisque, standard=brisque-sightengine, premium/full=all-3",
    )

    parser.add_argument("--stages", help="Custom pipeline stages (comma-separated)")

    parser.add_argument(
        "--cost-limit", type=float, help="Maximum cost limit for API calls (in USD)"
    )

    parser.add_argument(
        "--sightengine-key", help="SightEngine API credentials (format: 'user,secret')"
    )

    parser.add_argument("--claude-key", help="Anthropic/Claude API key")

    # Logging options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output (DEBUG level)"
    )

    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")

    parser.add_argument("--log-file", help="Path to log file")
    
    parser.add_argument(
        "--log-format",
        choices=["json", "console"],
        default="console",
        help="Log output format (default: console)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    # Debug/Development options
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (acknowledges CLI deprecation)")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies and exit")
    parser.add_argument("--force-cli", action="store_true", help="Force CLI usage without deprecation warning")

    return parser


def parse_cli_overrides(args: list[str]) -> list[str]:
    """Extract OmegaConf-style overrides from command-line arguments.

    Args:
        args: List of command-line arguments

    Returns:
        List of override strings in format ["key=value", ...]
    """
    overrides = []
    for arg in args:
        if arg.startswith("--") and "=" in arg:
            # Remove -- prefix and add to overrides
            override = arg[2:]
            overrides.append(override)
    return overrides


def apply_cli_args_to_config(config: DictConfig, args: argparse.Namespace) -> None:
    """Apply command-line arguments to configuration.

    Args:
        config: Configuration object to update
        args: Parsed command-line arguments
    """
    # Override paths
    if hasattr(args, "inbox") and args.inbox:
        config.paths.inbox = args.inbox

    if hasattr(args, "output") and args.output:
        config.paths.organized = args.output

    # Override processing options
    if hasattr(args, "move") and args.move:
        config.processing.copy_mode = False
    if hasattr(args, "force_reindex") and args.force_reindex:
        config.processing.force_reindex = True
    if hasattr(args, "quality") and args.quality:
        config.processing.quality = True
    if hasattr(args, "understand") and args.understand:
        config.processing.understanding = True
    if hasattr(args, "providers") and args.providers:
        # Set understanding providers
        providers = [p.strip() for p in args.providers.split(",")]
        if not hasattr(config, "understanding"):
            from omegaconf import OmegaConf
            config.understanding = OmegaConf.create({})
        config.understanding.providers = providers
        config.understanding.preferred_provider = providers[0] if providers else None
    if hasattr(args, "watch") and args.watch:
        config.processing.watch = True
    if hasattr(args, "dry_run") and args.dry_run:
        config.processing.dry_run = True
    if hasattr(args, "enhanced_metadata") and args.enhanced_metadata:
        config.enhanced_metadata = True

    # Pipeline options
    if hasattr(args, "pipeline") and args.pipeline:
        config.pipeline.mode = args.pipeline
    if hasattr(args, "stages") and args.stages:
        config.pipeline.stages = [s.strip() for s in args.stages.split(",")]
    if hasattr(args, "cost_limit") and args.cost_limit:
        config.pipeline.cost_limits.total = args.cost_limit


def check_dependencies() -> bool:
    """Check if required external tools are available.

    Returns:
        True if all required dependencies are available
    """
    import subprocess

    deps_ok = True

    # Check for ffprobe (required for video metadata)
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        print("✓ ffprobe found (video metadata extraction)")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("✗ ffprobe not found - install ffmpeg for video metadata")
        print("  Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")
        deps_ok = False

    # Check for understanding system
    try:
        from ..understanding import analyzer
        print("✓ Understanding system available (advanced analysis)")
    except ImportError:
        print("ℹ Understanding system not available - advanced analysis disabled")
        print("  Understanding system provides AI-powered asset analysis")

    return deps_ok


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (for testing)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse arguments
    parser = create_parser()
    args, unknown = parser.parse_known_args(argv)

    # Handle setup subcommand
    if args.command == "setup":
        from ..core.first_run import run_setup_command
        return run_setup_command()
    
    # Handle cost subcommand
    if args.command == "cost":
        from ..core.cost_tracker import get_cost_tracker, CostCategory
        
        cost_tracker = get_cost_tracker()
        
        if args.cost_command == "report":
            report = cost_tracker.format_cost_report()
            print(report)
            return 0
            
        elif args.cost_command == "set-budget":
            if args.daily:
                cost_tracker.set_budget("daily", args.daily, args.alert)
                print(f"✅ Set daily budget: ${args.daily:.2f}")
            if args.monthly:
                cost_tracker.set_budget("monthly", args.monthly, args.alert)
                print(f"✅ Set monthly budget: ${args.monthly:.2f}")
            if not args.daily and not args.monthly:
                print("❌ Please specify --daily and/or --monthly budget")
                return 1
            return 0
            
        elif args.cost_command == "providers":
            category = CostCategory[args.category.upper()] if args.category else None
            comparison = cost_tracker.get_provider_comparison(category)
            
            print("\n📊 Provider Cost Comparison")
            print("=" * 60)
            for provider in comparison:
                print(f"\n{provider['provider']}:")
                print(f"  Category: {provider['category']}")
                print(f"  Total spent: ${provider['total_spent']:.2f}")
                print(f"  Requests: {provider['request_count']}")
                if provider['request_count'] > 0:
                    print(f"  Average cost: ${provider['average_cost']:.4f}")
                print(f"  Pricing: {provider['pricing_model']}")
                if 'typical_cost' in provider:
                    print(f"  Typical cost: ${provider['typical_cost']:.4f}")
                print(f"  Free tier: {provider['free_tier']}")
            return 0
    
    # Handle keys subcommand
    if args.command == "keys":
        from ..core.keys.cli import run_keys_command

        return run_keys_command(args)
    
    # Handle recreate subcommand
    if args.command == "recreate":
        from ..providers.recreate_cli import cli as recreate_cli
        
        # Build command line args for click
        click_args = [args.recreate_command]
        if args.recreate_command == "inspect":
            click_args.append(args.file_path)
        elif args.recreate_command == "recreate":
            click_args.append(args.asset_id)
            if hasattr(args, "provider") and args.provider:
                click_args.extend(["--provider", args.provider])
            if hasattr(args, "model") and args.model:
                click_args.extend(["--model", args.model])
            if hasattr(args, "output") and args.output:
                click_args.extend(["--output", args.output])
            if hasattr(args, "dry_run") and args.dry_run:
                click_args.append("--dry-run")
        elif args.recreate_command == "catalog":
            click_args.append(args.directory)
            if hasattr(args, "recursive") and args.recursive:
                click_args.append("--recursive")
        
        # Run the click command
        recreate_cli(click_args)
        return 0

    # Handle interface subcommand
    if args.command == "interface":
        if hasattr(args, "structured") and args.structured:
            from .cli_handler_structured import run_interface_command
        else:
            from .cli_handler import run_interface_command

        return run_interface_command(args)

    # Handle MCP server subcommand
    if args.command == "mcp-server":
        from .mcp_server import main as run_mcp_server

        run_mcp_server()
        return 0
    
    # Handle metrics server subcommand
    if args.command == "metrics-server":
        from ..core.metrics_server import run_metrics_server
        
        run_metrics_server(host=args.host, port=args.port)
        return 0
    
    # Handle comparison subcommand
    if args.command == "comparison":
        if args.comparison_command == "server":
            import os
            from ..comparison.web_server import run_server
            
            if args.populate_test_data:
                os.environ["ALICE_ENV"] = "development"
            
            run_server(host=args.host, port=args.port)
            return 0
        else:
            # Handle other comparison commands
            from ..comparison.cli import cli as comparison_cli
            
            # Build command line args for click
            click_args = [args.comparison_command]
            
            if args.comparison_command == "populate":
                click_args.append(args.directory)
                if args.recursive:
                    click_args.append("--recursive")
                if args.limit:
                    click_args.extend(["--limit", str(args.limit)])
            elif args.comparison_command == "populate-default":
                if hasattr(args, "limit") and args.limit:
                    click_args.extend(["--limit", str(args.limit)])
            # stats and reset don't need additional args
            
            comparison_cli(click_args)
            return 0
    
    # Handle index subcommand
    if args.command == "index":
        from ..storage.index_builder import SearchIndexBuilder
        
        # Load config to get DB path
        config = load_config()
        db_path = None
        if hasattr(config, 'storage') and hasattr(config.storage, 'search_db'):
            db_path = config.storage.search_db
        
        builder = SearchIndexBuilder(db_path)
        
        if args.index_command == "rebuild":
            print(f"Rebuilding search index from {len(args.paths)} paths...")
            count = builder.rebuild_from_paths(
                args.paths, 
                show_progress=not args.no_progress
            )
            print(f"\nSuccessfully indexed {count} assets")
            return 0
            
        elif args.index_command == "update":
            print(f"Updating search index from {args.path}...")
            count = builder.update_from_path(args.path)
            print(f"Updated {count} assets in index")
            return 0
            
        elif args.index_command == "verify":
            print("Verifying search index...")
            results = builder.verify_index()
            print(f"\nIndex verification results:")
            print(f"  Total indexed: {results['total_indexed']}")
            print(f"  Valid files: {results['valid_files']}")
            print(f"  Missing files: {results['missing_files']}")
            if results['missing_files'] > 0 and results['missing_file_paths']:
                print(f"\nFirst few missing files:")
                for path in results['missing_file_paths'][:10]:
                    print(f"  - {path}")
            return 0
            
        elif args.index_command == "stats":
            print("Search index statistics:")
            stats = builder.search_db.get_statistics()
            print(f"  Total assets: {stats.get('total_assets', 0)}")
            print(f"  Unique tags: {stats.get('unique_tags', 0)}")
            print(f"  Storage size: {stats.get('storage_size_mb', 0):.1f} MB")
            return 0
    
    # Handle storage subcommand
    if args.command == "storage":
        from ..storage.cli import storage as storage_cli
        
        # Build command line args for click
        click_args = [args.storage_command]
        
        if args.storage_command == "init":
            if hasattr(args, "db_path") and args.db_path:
                click_args.extend(["--db-path", args.db_path])
        elif args.storage_command == "add":
            click_args.extend(["--name", args.name])
            click_args.extend(["--path", args.path])
            click_args.extend(["--type", args.type])
            click_args.extend(["--priority", str(args.priority)])
            if hasattr(args, "rule") and args.rule:
                for rule in args.rule:
                    click_args.extend(["--rule", rule])
        elif args.storage_command == "scan":
            click_args.append(args.location_id)
        elif args.storage_command == "discover":
            if hasattr(args, "force") and args.force:
                click_args.append("--force")
        elif args.storage_command == "find-project":
            click_args.append(args.project_name)
            if hasattr(args, "type") and args.type:
                for t in args.type:
                    click_args.extend(["--type", t])
        elif args.storage_command == "update":
            if hasattr(args, "location_id") and args.location_id:
                click_args.extend(["--location-id", args.location_id])
            if hasattr(args, "priority") and args.priority:
                click_args.extend(["--priority", str(args.priority)])
            if hasattr(args, "status") and args.status:
                click_args.extend(["--status", args.status])
        # list, stats, from-config don't need additional args
        
        storage_cli(click_args)
        return 0

    # Setup logging for main command
    log_level = args.log_level if hasattr(args, "log_level") else "INFO"
    if hasattr(args, "verbose") and args.verbose:
        log_level = "DEBUG"
    elif hasattr(args, "quiet") and args.quiet:
        log_level = "ERROR"
    
    # Use structured logging
    setup_structured_logging(
        log_level=log_level,
        json_logs=(getattr(args, "log_format", "console") == "json"),
        include_caller_info=(log_level == "DEBUG")
    )
    
    # Show deprecation warning for direct CLI usage (except for allowed commands)
    allowed_commands = ["mcp-server", "metrics-server", "keys", "interface", "recreate", "index", "comparison", "setup", "storage", "cost"]
    force_cli = hasattr(args, "force_cli") and args.force_cli
    debug_mode = hasattr(args, "debug") and args.debug
    check_deps = hasattr(args, "check_deps") and args.check_deps
    
    # Skip warning for allowed commands or debug flags
    if (args.command not in allowed_commands and 
        not force_cli and 
        not debug_mode and 
        not check_deps and
        args.command is not None):
        
        print("\n" + "="*70)
        print("⚠️  ALICE IS NOW AN AI-NATIVE SERVICE")
        print("="*70)
        print("\nDirect CLI usage is deprecated. Alice should be used through AI assistants.")
        print("\nFor normal usage:")
        print("1. Install: pip install -e .")
        print("2. Configure Claude Desktop to use Alice")
        print("3. Chat naturally: 'Claude, organize my AI images'")
        print("\nSee documentation: https://github.com/yourusername/AliceMultiverse")
        print("\nTo proceed with debugging, use --debug flag")
        print("Example: alice --debug --dry-run --verbose")
        print("="*70 + "\n")
        return 1

    # Check dependencies if requested
    if hasattr(args, "check_deps") and args.check_deps:
        deps_ok = check_dependencies()
        return 0 if deps_ok else 1

    try:
        # Check first run for organize command
        if args.command is None:  # Default organize command
            from ..core.first_run import check_first_run
            if not check_first_run():
                return 1
        
        # Load configuration
        config_path = Path(args.config) if hasattr(args, "config") and args.config else None
        cli_overrides = parse_cli_overrides(unknown)
        config = load_config(config_path, cli_overrides)

        # Apply explicit CLI arguments
        apply_cli_args_to_config(config, args)

        # Validate configuration
        if not config.paths.inbox:
            raise ConfigurationError(
                "No source directory specified. " "Use --inbox or set paths.inbox in settings.yaml"
            )

        source_path = Path(config.paths.inbox)
        if not source_path.exists():
            raise ConfigurationError(f"Source directory does not exist: {source_path}")

        output_path = Path(config.paths.organized)
        if output_path.resolve().is_relative_to(source_path.resolve()):
            raise ConfigurationError("Output directory cannot be inside source directory")

        # Log configuration
        logger.info(f"AliceMultiverse v{__version__}")
        logger.info(f"Source: {source_path}")
        logger.info(f"Output: {output_path}")
        logger.info(f"Mode: {'Move' if not config.processing.copy_mode else 'Copy'}")

        if config.processing.dry_run:
            logger.info("DRY RUN - No files will be modified")

        # Import and run organizer
        # This is imported here to avoid circular imports and speed up CLI
        from ..organizer import run_organizer

        pipeline = getattr(args, "pipeline", None)
        stages = getattr(args, "stages", None)
        cost_limit = getattr(args, "cost_limit", None)
        sightengine_key = getattr(args, "sightengine_key", None)
        claude_key = getattr(args, "claude_key", None)

        result = run_organizer(config, pipeline, stages, cost_limit, sightengine_key, claude_key)

        return 0 if result else 1

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 130

    except ConfigurationError as e:
        from ..core.error_handling import wrap_error, format_error_for_user
        wrapped = wrap_error(e, "configuration")
        print(format_error_for_user(wrapped, include_traceback=args.debug if 'args' in locals() else False))
        return 1

    except AliceMultiverseError as e:
        from ..core.error_handling import wrap_error, format_error_for_user
        wrapped = wrap_error(e, "processing")
        print(format_error_for_user(wrapped, include_traceback=args.debug if 'args' in locals() else False))
        return 1

    except Exception as e:
        from ..core.error_handling import wrap_error, format_error_for_user
        wrapped = wrap_error(e, "unexpected error")
        print(format_error_for_user(wrapped, include_traceback=args.debug if 'args' in locals() else False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
