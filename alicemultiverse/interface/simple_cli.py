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
  alice mcp-server    Start MCP server for Claude Desktop
  alice keys setup    Configure API keys
  alice --version     Show version
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # MCP server (essential for AI integration)
    subparsers.add_parser("mcp-server", help="Start MCP server for AI integration")

    # Keys management (essential for API access)
    keys_parser = subparsers.add_parser("keys", help="Manage API keys")
    keys_subparsers = keys_parser.add_subparsers(dest="keys_command", help="Key commands")
    keys_subparsers.add_parser("setup", help="Interactive setup wizard")
    keys_subparsers.add_parser("list", help="List configured keys")

    # Basic organization (for debugging)
    parser.add_argument("-i", "--inbox", help="Input directory (debug only)")
    parser.add_argument("-o", "--output", help="Output directory (debug only)")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch for new files")
    parser.add_argument("-u", "--understand", action="store_true", help="Enable AI understanding")

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
# TODO: Review unreachable code - from ..mcp_server import main as mcp_main
# TODO: Review unreachable code - return mcp_main()

# TODO: Review unreachable code - # Handle keys
# TODO: Review unreachable code - elif args.command == "keys":
# TODO: Review unreachable code - from ..core.keys.cli import run_keys_command
# TODO: Review unreachable code - return run_keys_command(args)

# TODO: Review unreachable code - # Handle basic organization (debug mode)
# TODO: Review unreachable code - elif args.inbox or args.output:
# TODO: Review unreachable code - if not args.debug:
# TODO: Review unreachable code - logger.warning("⚠️  Direct CLI usage is deprecated! Use --debug flag for debugging.")
# TODO: Review unreachable code - logger.warning("For normal usage, configure Alice with Claude Desktop.")
# TODO: Review unreachable code - return 1

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
