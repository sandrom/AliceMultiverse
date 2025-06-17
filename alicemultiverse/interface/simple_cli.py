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


def main(argv: list[str] | None = None) -> int:
    """Simplified main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(message)s')

    try:
        # Handle MCP server
        if args.command == "mcp-server":
            logger.info("Starting MCP server...")
            from ..mcp_server import main as mcp_main
            return mcp_main()

        # Handle keys
        elif args.command == "keys":
            from ..core.keys.cli import run_keys_command
            return run_keys_command(args)

        # Handle basic organization (debug mode)
        elif args.inbox or args.output:
            if not args.debug:
                logger.warning("⚠️  Direct CLI usage is deprecated! Use --debug flag for debugging.")
                logger.warning("For normal usage, configure Alice with Claude Desktop.")
                return 1

            from ..organizer.media_organizer import MediaOrganizer
            config = load_config()

            # Override paths if provided
            if args.inbox:
                config.paths.inbox = Path(args.inbox)
            if args.output:
                config.paths.organized = Path(args.output)

            organizer = MediaOrganizer(
                config,
                dry_run=args.dry_run,
                watch_mode=args.watch,
                enable_understanding=args.understand
            )

            results = organizer.organize()
            logger.info(f"Organized {results.statistics['organized']} files")
            return 0

        else:
            parser.print_help()
            return 0

    except AliceMultiverseError as e:
        logger.error(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.debug)
        return 1


if __name__ == "__main__":
    sys.exit(main())
