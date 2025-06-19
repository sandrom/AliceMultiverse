"""Command-line interface for AliceMultiverse - Refactored version."""

import argparse
import logging
import sys

from omegaconf import DictConfig

from ..core.config import load_config
from ..core.exceptions import AliceMultiverseError, ConfigurationError
from ..core.structured_logging import setup_structured_logging
from .cli_handlers import (
    handle_comparison_command,
    handle_dedup_command,
    handle_index_command,
    handle_interface_command,
    handle_keys_command,
    handle_mcp_command,
    handle_migrate_command,
    handle_monitor_command,
    handle_organize_command,
    handle_prompts_command,
    handle_recreate_command,
    handle_scenes_command,
    handle_setup_command,
    handle_storage_command,
    handle_transitions_command,
)
from .cli_parser import (
    add_comparison_subcommand,
    add_dedup_subcommand,
    add_index_subcommand,
    add_interface_subcommand,
    add_keys_subcommand,
    add_mcp_subcommand,
    add_migrate_subcommand,
    add_monitor_subcommand,
    add_organization_args,
    add_output_args,
    add_prompts_subcommand,
    add_recreate_subcommand,
    add_scenes_subcommand,
    add_setup_subcommand,
    add_storage_subcommand,
    add_technical_args,
    add_transitions_subcommand,
    add_understanding_args,
    create_base_parser,
)

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = create_base_parser()

    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add subcommands
    add_keys_subcommand(subparsers)
    add_setup_subcommand(subparsers)
    add_recreate_subcommand(subparsers)
    add_interface_subcommand(subparsers)
    add_mcp_subcommand(subparsers)
    add_migrate_subcommand(subparsers)
    add_monitor_subcommand(subparsers)
    add_storage_subcommand(subparsers)
    add_scenes_subcommand(subparsers)
    add_dedup_subcommand(subparsers)
    add_prompts_subcommand(subparsers)
    add_index_subcommand(subparsers)
    add_comparison_subcommand(subparsers)
    add_transitions_subcommand(subparsers)

    # Add main organization arguments
    add_organization_args(parser)
    add_understanding_args(parser)
    add_output_args(parser)
    add_technical_args(parser)

    return parser


# TODO: Review unreachable code - def parse_cli_overrides(args: list[str]) -> list[str]:
# TODO: Review unreachable code - """Parse CLI override arguments."""
# TODO: Review unreachable code - overrides = []
# TODO: Review unreachable code - for arg in args:
# TODO: Review unreachable code - if "=" in arg:
# TODO: Review unreachable code - key, value = arg.split("=", 1)
# TODO: Review unreachable code - # Clean up the key
# TODO: Review unreachable code - key = key.strip().replace("--", "")
# TODO: Review unreachable code - # Handle different value types
# TODO: Review unreachable code - if value.lower() in ["true", "false"]:
# TODO: Review unreachable code - value = value.lower()
# TODO: Review unreachable code - elif value.isdigit():
# TODO: Review unreachable code - value = int(value)
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - value = float(value)
# TODO: Review unreachable code - except ValueError:
# TODO: Review unreachable code - pass  # Keep as string
# TODO: Review unreachable code - overrides.append(f"{key}={value}")
# TODO: Review unreachable code - return overrides


# TODO: Review unreachable code - def apply_cli_args_to_config(config: DictConfig, args: argparse.Namespace) -> None:
# TODO: Review unreachable code - """Apply CLI arguments to configuration."""
# TODO: Review unreachable code - # Map CLI args to config paths
# TODO: Review unreachable code - mappings = {
# TODO: Review unreachable code - "inbox": "paths.inbox",
# TODO: Review unreachable code - "output": "paths.organized",
# TODO: Review unreachable code - "move": "behavior.move_files",
# TODO: Review unreachable code - "dry_run": "behavior.dry_run",
# TODO: Review unreachable code - "force_reindex": "behavior.force_reindex",
# TODO: Review unreachable code - "quality": "quality.enabled",
# TODO: Review unreachable code - "understand": "understanding.enabled",
# TODO: Review unreachable code - "providers": "understanding.providers",
# TODO: Review unreachable code - "watch": "watch.enabled",
# TODO: Review unreachable code - "enhanced_metadata": "metadata.enhanced_extraction",
# TODO: Review unreachable code - "openai_api_key": "understanding.providers_config.openai.api_key",
# TODO: Review unreachable code - "anthropic_api_key": "understanding.providers_config.anthropic.api_key",
# TODO: Review unreachable code - "google_ai_api_key": "understanding.providers_config.google.api_key",
# TODO: Review unreachable code - "deepseek_api_key": "understanding.providers_config.deepseek.api_key",
# TODO: Review unreachable code - "cost_limit": "understanding.cost_limit",
# TODO: Review unreachable code - "detailed": "understanding.detailed",
# TODO: Review unreachable code - "verbose": "output.verbose",
# TODO: Review unreachable code - "debug": "output.debug",
# TODO: Review unreachable code - "quiet": "output.quiet",
# TODO: Review unreachable code - "json": "output.format",
# TODO: Review unreachable code - "log_file": "output.log_file",
# TODO: Review unreachable code - "no_color": "output.no_color",
# TODO: Review unreachable code - }

# TODO: Review unreachable code - for arg_name, config_path in mappings.items():
# TODO: Review unreachable code - arg_value = getattr(args, arg_name, None)
# TODO: Review unreachable code - if arg_value is not None:
# TODO: Review unreachable code - # Handle special cases
# TODO: Review unreachable code - if arg_name == "json" and arg_value:
# TODO: Review unreachable code - arg_value = "json"
# TODO: Review unreachable code - elif arg_name == "providers" and isinstance(arg_value, str):
# TODO: Review unreachable code - arg_value = [p.strip() for p in arg_value.split(",")]

# TODO: Review unreachable code - # Set the config value
# TODO: Review unreachable code - parts = config_path.split(".")
# TODO: Review unreachable code - current = config
# TODO: Review unreachable code - for part in parts[:-1]:
# TODO: Review unreachable code - if part not in current:
# TODO: Review unreachable code - current[part] = {}
# TODO: Review unreachable code - current = current[part]
# TODO: Review unreachable code - current[parts[-1]] = arg_value


# TODO: Review unreachable code - def check_dependencies() -> bool:
# TODO: Review unreachable code - """Check system dependencies."""
# TODO: Review unreachable code - print("Checking system dependencies...")

# TODO: Review unreachable code - dependencies = {
# TODO: Review unreachable code - "ffmpeg": "ffmpeg -version",
# TODO: Review unreachable code - "ffprobe": "ffprobe -version",
# TODO: Review unreachable code - "exiftool": "exiftool -ver",
# TODO: Review unreachable code - }

# TODO: Review unreachable code - all_ok = True
# TODO: Review unreachable code - for name, cmd in dependencies.items():
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - import subprocess
# TODO: Review unreachable code - subprocess.run(cmd.split(), capture_output=True, check=True)
# TODO: Review unreachable code - print(f"✓ {name}: OK")
# TODO: Review unreachable code - except (subprocess.CalledProcessError, FileNotFoundError):
# TODO: Review unreachable code - print(f"✗ {name}: NOT FOUND")
# TODO: Review unreachable code - all_ok = False

# TODO: Review unreachable code - return all_ok


# TODO: Review unreachable code - def main(argv: list[str] | None = None) -> int:
# TODO: Review unreachable code - """Main entry point."""
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - parser = create_parser()
# TODO: Review unreachable code - args = parser.parse_args(argv)

# TODO: Review unreachable code - # Check dependencies if requested
# TODO: Review unreachable code - if args.check_deps:
# TODO: Review unreachable code - return 0 if check_dependencies() else 1

# TODO: Review unreachable code - # Setup logging
# TODO: Review unreachable code - setup_structured_logging(
# TODO: Review unreachable code - debug=args.debug,
# TODO: Review unreachable code - log_file=args.log_file,
# TODO: Review unreachable code - no_color=args.no_color,
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Load configuration
# TODO: Review unreachable code - config = load_config(args.config)

# TODO: Review unreachable code - # Apply CLI overrides
# TODO: Review unreachable code - if args.cli_overrides:
# TODO: Review unreachable code - overrides = parse_cli_overrides(args.cli_overrides)
# TODO: Review unreachable code - from omegaconf import OmegaConf
# TODO: Review unreachable code - override_config = OmegaConf.from_dotlist(overrides)
# TODO: Review unreachable code - config = OmegaConf.merge(config, override_config)

# TODO: Review unreachable code - # Apply CLI arguments
# TODO: Review unreachable code - apply_cli_args_to_config(config, args)

# TODO: Review unreachable code - # Handle commands
# TODO: Review unreachable code - if args.command == "keys":
# TODO: Review unreachable code - return handle_keys_command(args, config)
# TODO: Review unreachable code - elif args.command == "setup":
# TODO: Review unreachable code - return handle_setup_command(args, config)
# TODO: Review unreachable code - elif args.command == "recreate":
# TODO: Review unreachable code - return handle_recreate_command(args, config)
# TODO: Review unreachable code - elif args.command == "interface":
# TODO: Review unreachable code - return handle_interface_command(args, config)
# TODO: Review unreachable code - elif args.command == "mcp-server":
# TODO: Review unreachable code - return handle_mcp_command(args, config)
# TODO: Review unreachable code - elif args.command == "migrate":
# TODO: Review unreachable code - return handle_migrate_command(args, config)
# TODO: Review unreachable code - elif args.command == "monitor":
# TODO: Review unreachable code - return handle_monitor_command(args, config)
# TODO: Review unreachable code - elif args.command == "storage":
# TODO: Review unreachable code - return handle_storage_command(args, config)
# TODO: Review unreachable code - elif args.command == "scenes":
# TODO: Review unreachable code - return handle_scenes_command(args, config)
# TODO: Review unreachable code - elif args.command == "dedup":
# TODO: Review unreachable code - return handle_dedup_command(args, config)
# TODO: Review unreachable code - elif args.command == "prompts":
# TODO: Review unreachable code - return handle_prompts_command(args, config)
# TODO: Review unreachable code - elif args.command == "index":
# TODO: Review unreachable code - return handle_index_command(args, config)
# TODO: Review unreachable code - elif args.command == "comparison":
# TODO: Review unreachable code - return handle_comparison_command(args, config)
# TODO: Review unreachable code - elif args.command == "transitions":
# TODO: Review unreachable code - return handle_transitions_command(args, config)
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - # Default: organize command
# TODO: Review unreachable code - return handle_organize_command(args, config)

# TODO: Review unreachable code - except ConfigurationError as e:
# TODO: Review unreachable code - logger.error(f"Configuration error: {e}")
# TODO: Review unreachable code - return 1
# TODO: Review unreachable code - except AliceMultiverseError as e:
# TODO: Review unreachable code - logger.error(f"Error: {e}")
# TODO: Review unreachable code - return 1
# TODO: Review unreachable code - except KeyboardInterrupt:
# TODO: Review unreachable code - logger.info("Interrupted by user")
# TODO: Review unreachable code - return 130
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.exception(f"Unexpected error: {e}")
# TODO: Review unreachable code - return 1


# TODO: Review unreachable code - if __name__ == "__main__":
# TODO: Review unreachable code - sys.exit(main())
