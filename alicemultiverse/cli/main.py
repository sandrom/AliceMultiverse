"""Simplified CLI for AliceMultiverse - Essential commands only."""

import argparse
import logging
import sys
from pathlib import Path

from ..core.config import load_config
from ..core.exceptions import AliceMultiverseError
from ..version import __version__

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create simplified argument parser with only essential commands."""
    parser = argparse.ArgumentParser(
        description="""AliceMultiverse - AI-Native Media Organization

⚠️  This CLI is for debugging only. Use Alice through AI assistants for normal usage.

Essential commands:
  alice mcp-server     Start MCP server for Claude Desktop
  alice keys setup     Configure API keys
  alice --version      Show version

Debug commands (use --debug flag):
  alice --debug organize    Basic file organization
  alice --debug dedup      Deduplication tools
  alice --debug prompts    Prompt management
  alice --debug storage    Storage management
  alice --debug scenes     Scene detection
  alice --debug transitions Video transitions
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for advanced commands")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # MCP server (essential for AI integration)
    subparsers.add_parser("mcp-server", help="Start MCP server for AI integration")

    # Keys management (essential for API access)
    keys_parser = subparsers.add_parser("keys", help="Manage API keys")
    keys_subparsers = keys_parser.add_subparsers(dest="keys_command", help="Key commands")
    keys_subparsers.add_parser("setup", help="Interactive setup wizard")
    keys_subparsers.add_parser("list", help="List configured keys")

    # Debug command with subcommands
    debug_parser = subparsers.add_parser("debug", help="Debug commands (requires --debug flag)")
    debug_subparsers = debug_parser.add_subparsers(dest="debug_command", help="Debug commands")

    # Basic organization (debug only)
    organize_parser = debug_subparsers.add_parser("organize", help="Basic file organization")
    organize_parser.add_argument("-i", "--inbox", help="Input directory")
    organize_parser.add_argument("-o", "--output", help="Output directory")
    organize_parser.add_argument("-n", "--dry-run", action="store_true", help="Preview without changes")
    organize_parser.add_argument("-w", "--watch", action="store_true", help="Watch for new files")
    organize_parser.add_argument("-u", "--understand", action="store_true", help="Enable AI understanding")

    # Add placeholders for other debug commands
    debug_subparsers.add_parser("dedup", help="Deduplication and similarity search")
    debug_subparsers.add_parser("prompts", help="Prompt management")
    debug_subparsers.add_parser("storage", help="Multi-location storage management")
    debug_subparsers.add_parser("scenes", help="Scene detection and analysis")
    debug_subparsers.add_parser("transitions", help="Video transition analysis")
    debug_subparsers.add_parser("performance", help="Performance monitoring and metrics")
    debug_subparsers.add_parser("config", help="Configuration validation and management")

    return parser


# TODO: Review unreachable code - def main(argv: list[str] | None = None) -> int:
# TODO: Review unreachable code - """Simplified main entry point."""
# TODO: Review unreachable code - parser = create_parser()
# TODO: Review unreachable code - args = parser.parse_args(argv)

# TODO: Review unreachable code - # Configure logging
# TODO: Review unreachable code - level = logging.DEBUG if args.debug else logging.INFO if args.verbose else logging.WARNING
# TODO: Review unreachable code - logging.basicConfig(level=level, format='%(message)s')

# TODO: Review unreachable code - try:
# TODO: Review unreachable code - # Handle MCP server
# TODO: Review unreachable code - if args.command == "mcp-server":
# TODO: Review unreachable code - logger.info("Starting MCP server...")
# TODO: Review unreachable code - from ..mcp import main as mcp_main
# TODO: Review unreachable code - return mcp_main()

# TODO: Review unreachable code - # Handle keys
# TODO: Review unreachable code - elif args.command == "keys":
# TODO: Review unreachable code - from ..core.keys.cli import run_keys_command
# TODO: Review unreachable code - return run_keys_command(args)

# TODO: Review unreachable code - # Handle debug commands
# TODO: Review unreachable code - elif args.command == "debug":
# TODO: Review unreachable code - if not args.debug:
# TODO: Review unreachable code - logger.error("⚠️  Debug commands require --debug flag!")
# TODO: Review unreachable code - logger.error("Example: alice --debug debug organize -i ~/inbox -o ~/organized")
# TODO: Review unreachable code - return 1

# TODO: Review unreachable code - # Handle organize subcommand
# TODO: Review unreachable code - if args.debug_command == "organize":
# TODO: Review unreachable code - from ..organizer.media_organizer import MediaOrganizer
# TODO: Review unreachable code - config = load_config()

# TODO: Review unreachable code - # Override paths if provided
# TODO: Review unreachable code - if args.inbox:
# TODO: Review unreachable code - config.paths.inbox = Path(args.inbox)
# TODO: Review unreachable code - if args.output:
# TODO: Review unreachable code - config.paths.organized = Path(args.output)

# TODO: Review unreachable code - organizer = MediaOrganizer(
# TODO: Review unreachable code - config,
# TODO: Review unreachable code - dry_run=args.dry_run,
# TODO: Review unreachable code - watch_mode=args.watch,
# TODO: Review unreachable code - enable_understanding=args.understand
# TODO: Review unreachable code - )

# TODO: Review unreachable code - results = organizer.organize()
# TODO: Review unreachable code - return 0 if results else 1

# TODO: Review unreachable code - # Delegate to Click-based commands
# TODO: Review unreachable code - elif args.debug_command in ["dedup", "prompts", "storage", "scenes", "transitions", "performance", "config"]:
# TODO: Review unreachable code - # Import the appropriate Click command group
# TODO: Review unreachable code - click_args = sys.argv[sys.argv.index(args.debug_command) + 1:]

# TODO: Review unreachable code - if args.debug_command == "dedup":
# TODO: Review unreachable code - from ..assets.deduplication.cli import dedup_cli
# TODO: Review unreachable code - return dedup_cli(click_args, standalone_mode=False)
# TODO: Review unreachable code - elif args.debug_command == "prompts":
# TODO: Review unreachable code - from ..prompts.cli import prompts_cli
# TODO: Review unreachable code - return prompts_cli(click_args, standalone_mode=False)
# TODO: Review unreachable code - elif args.debug_command == "storage":
# TODO: Review unreachable code - from ..storage.cli import storage
# TODO: Review unreachable code - return storage(click_args, standalone_mode=False)
# TODO: Review unreachable code - elif args.debug_command == "scenes":
# TODO: Review unreachable code - from ..scene_detection.cli import scenes_cli
# TODO: Review unreachable code - return scenes_cli(click_args, standalone_mode=False)
# TODO: Review unreachable code - elif args.debug_command == "transitions":
# TODO: Review unreachable code - from ..workflows.transitions.cli import transitions_cli
# TODO: Review unreachable code - return transitions_cli(click_args, standalone_mode=False)
# TODO: Review unreachable code - elif args.debug_command == "performance":
# TODO: Review unreachable code - from ..cli.performance_command import performance
# TODO: Review unreachable code - return performance(click_args, standalone_mode=False)
# TODO: Review unreachable code - elif args.debug_command == "config":
# TODO: Review unreachable code - from ..cli.config_command import config
# TODO: Review unreachable code - return config(click_args, standalone_mode=False)

# TODO: Review unreachable code - else:
# TODO: Review unreachable code - parser.print_help()
# TODO: Review unreachable code - return 1
# TODO: Review unreachable code - logger.info(f"Organized {results.statistics['organized']} files")
# TODO: Review unreachable code - return 0

# TODO: Review unreachable code - else:
# TODO: Review unreachable code - parser.print_help()
# TODO: Review unreachable code - return 0

# TODO: Review unreachable code - except AliceMultiverseError as e:
# TODO: Review unreachable code - logger.error(f"Error: {e}")
# TODO: Review unreachable code - return 1
# TODO: Review unreachable code - except KeyboardInterrupt:
# TODO: Review unreachable code - logger.info("\nInterrupted by user")
# TODO: Review unreachable code - return 130
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Unexpected error: {e}", exc_info=args.debug)
# TODO: Review unreachable code - return 1


# TODO: Review unreachable code - if __name__ == "__main__":
# TODO: Review unreachable code - sys.exit(main())
