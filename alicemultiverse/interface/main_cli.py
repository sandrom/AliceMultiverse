"""Command-line interface for AliceMultiverse - Refactored version."""

import argparse
import logging
import sys

from ..core.config_dataclass import Config, load_config
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


def parse_cli_overrides(args: list[str]) -> list[str]:
    """Parse CLI override arguments."""
    overrides = []
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            # Clean up the key
            key = key.strip().replace("--", "")
            # Handle different value types
            if value.lower() in ["true", "false"]:
                value = value.lower()
            elif value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string
            overrides.append(f"{key}={value}")
    return overrides


def apply_cli_args_to_config(config, args: argparse.Namespace) -> None:
    """Apply CLI arguments to configuration."""
    # Map CLI args to config paths
    mappings = {
        "inbox": "paths.inbox",
        "output": "paths.organized",
        "move": "processing.copy_mode",  # Note: inverted logic
        "dry_run": "processing.dry_run",
        "force_reindex": "processing.force_reindex",
        "quality": "processing.quality",
        "understand": "understanding.enabled",
        "providers": "understanding.providers",
        "watch": "processing.watch",
        "enhanced_metadata": "metadata.enhanced_extraction",
        "openai_api_key": "understanding.providers_config.openai.api_key",
        "anthropic_api_key": "understanding.providers_config.anthropic.api_key",
        "google_ai_api_key": "understanding.providers_config.google.api_key",
        "deepseek_api_key": "understanding.providers_config.deepseek.api_key",
        "cost_limit": "understanding.cost_limit",
        "detailed": "understanding.detailed",
        "verbose": "output.verbose",
        "debug": "output.debug",
        "quiet": "output.quiet",
        "json": "output.format",
        "log_file": "output.log_file",
        "no_color": "output.no_color",
    }

    for arg_name, config_path in mappings.items():
        arg_value = getattr(args, arg_name, None)
        if arg_value is not None:
            # Handle special cases
            if arg_name == "move" and arg_value:
                # --move means copy_mode = False
                arg_value = False
            elif arg_name == "json" and arg_value:
                arg_value = "json"
            elif arg_name == "providers" and isinstance(arg_value, str):
                arg_value = [p.strip() for p in arg_value.split(",")]

            # Set the config value using the dataclass set method
            try:
                config.set(config_path, arg_value)
            except AttributeError:
                # If the path doesn't exist, skip it
                logger.debug(f"Skipping unknown config path: {config_path}")


def check_dependencies() -> bool:
    """Check system dependencies."""
    print("Checking system dependencies...")

    dependencies = {
        "ffmpeg": "ffmpeg -version",
        "ffprobe": "ffprobe -version",
        "exiftool": "exiftool -ver",
    }

    all_ok = True
    for name, cmd in dependencies.items():
        try:
            import subprocess
            subprocess.run(cmd.split(), capture_output=True, check=True)
            print(f"✓ {name}: OK")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ {name}: NOT FOUND")
            all_ok = False

    return all_ok


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    try:
        parser = create_parser()
        args = parser.parse_args(argv)

        # Check dependencies if requested
        if hasattr(args, 'check_deps') and args.check_deps:
            return 0 if check_dependencies() else 1

        # Setup logging
        log_level = 'DEBUG' if getattr(args, 'debug', False) else 'INFO'
        setup_structured_logging(
            log_level=log_level,
            json_logs=False,  # Use human-readable format for CLI
            include_caller_info=getattr(args, 'debug', False)
        )

        # Load configuration
        config = load_config(getattr(args, 'config', None))

        # Apply CLI overrides
        if hasattr(args, 'cli_overrides') and args.cli_overrides:
            overrides = parse_cli_overrides(args.cli_overrides)
            from omegaconf import OmegaConf
            override_config = OmegaConf.from_dotlist(overrides)
            config = OmegaConf.merge(config, override_config)

        # Apply CLI arguments
        apply_cli_args_to_config(config, args)

        # Handle commands
        if args.command == "keys":
            return handle_keys_command(args, config)
        elif args.command == "setup":
            return handle_setup_command(args, config)
        elif args.command == "recreate":
            return handle_recreate_command(args, config)
        elif args.command == "interface":
            return handle_interface_command(args, config)
        elif args.command == "mcp-server":
            return handle_mcp_command(args, config)
        elif args.command == "migrate":
            return handle_migrate_command(args, config)
        elif args.command == "monitor":
            return handle_monitor_command(args, config)
        elif args.command == "storage":
            return handle_storage_command(args, config)
        elif args.command == "scenes":
            return handle_scenes_command(args, config)
        elif args.command == "dedup":
            return handle_dedup_command(args, config)
        elif args.command == "prompts":
            return handle_prompts_command(args, config)
        elif args.command == "index":
            return handle_index_command(args, config)
        elif args.command == "comparison":
            return handle_comparison_command(args, config)
        elif args.command == "transitions":
            return handle_transitions_command(args, config)
        else:
            # Default: organize command
            return handle_organize_command(args, config)

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except AliceMultiverseError as e:
        logger.error(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
