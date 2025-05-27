"""Command-line interface for AliceMultiverse."""

import argparse
import logging
import sys
from pathlib import Path

from omegaconf import DictConfig

from ..core.config import load_config
from ..core.exceptions import AliceMultiverseError, ConfigurationError
from ..core.logging import setup_logging
from ..version import __version__

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="AliceMultiverse - AI Assistant Interface & Creative Workflow Hub\nConnect AI assistants with local tools and creative workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Use defaults from settings.yaml
  %(prog)s --inbox ~/Downloads       # Specify input directory
  %(prog)s -i ~/Downloads -o ~/AI    # Specify both directories
  %(prog)s --quality                 # Enable quality assessment
  %(prog)s -w --quality              # Watch mode with quality
  %(prog)s keys setup                # Configure API keys
  
Configuration overrides:
  %(prog)s --paths.inbox=~/Downloads --quality.thresholds.3_star.max=70
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

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

    # Interface subcommand (for AI interaction demo)
    interface_parser = subparsers.add_parser(
        "interface", help="Start Alice interface for AI interaction"
    )
    interface_parser.add_argument(
        "--demo", action="store_true", help="Run demonstration of AI interaction"
    )

    # MCP server subcommand
    mcp_parser = subparsers.add_parser("mcp-server", help="Start MCP server for AI integration")
    mcp_parser.add_argument(
        "--port", type=int, help="Port to run on (for TCP mode, not implemented yet)"
    )

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

    # Utility options
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies and exit")

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

    # Check for BRISQUE
    from ..quality.brisque import is_available

    if is_available():
        print("✓ BRISQUE available (quality assessment)")
    else:
        print("ℹ BRISQUE not available - quality assessment disabled")
        print("  Install with: pip install image-quality")

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

    # Handle keys subcommand
    if args.command == "keys":
        from ..core.keys.cli import run_keys_command

        return run_keys_command(args)

    # Handle interface subcommand
    if args.command == "interface":
        from .cli_handler import run_interface_command

        return run_interface_command(args)

    # Handle MCP server subcommand
    if args.command == "mcp-server":
        from .mcp_server import main as run_mcp_server

        run_mcp_server()
        return 0

    # Setup logging for main command
    log_level = "DEBUG" if hasattr(args, "verbose") and args.verbose else "INFO"
    log_file = Path(args.log_file) if hasattr(args, "log_file") and args.log_file else None
    quiet = hasattr(args, "quiet") and args.quiet
    setup_logging(level=log_level, log_file=log_file, quiet=quiet)

    # Check dependencies if requested
    if hasattr(args, "check_deps") and args.check_deps:
        deps_ok = check_dependencies()
        return 0 if deps_ok else 1

    try:
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
        logger.error(f"Configuration error: {e}")
        return 1

    except AliceMultiverseError as e:
        logger.error(f"Error: {e}")
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
