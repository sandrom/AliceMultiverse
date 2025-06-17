"""Command-line interface for AliceMultiverse - Refactored version."""

import argparse
import logging
import sys
from pathlib import Path

from omegaconf import DictConfig

from ..core.config import load_config
from ..core.exceptions import AliceMultiverseError, ConfigurationError
from ..core.structured_logging import setup_structured_logging
from ..version import __version__
from .cli_parser import (
    create_base_parser,
    add_keys_subcommand,
    add_setup_subcommand,
    add_recreate_subcommand,
    add_interface_subcommand,
    add_mcp_subcommand,
    add_migrate_subcommand,
    add_monitor_subcommand,
    add_storage_subcommand,
    add_scenes_subcommand,
    add_dedup_subcommand,
    add_prompts_subcommand,
    add_index_subcommand,
    add_comparison_subcommand,
    add_transitions_subcommand,
    add_organization_args,
    add_understanding_args,
    add_output_args,
    add_technical_args,
)
from .cli_handlers import (
    handle_keys_command,
    handle_setup_command,
    handle_recreate_command,
    handle_interface_command,
    handle_mcp_command,
    handle_migrate_command,
    handle_monitor_command,
    handle_storage_command,
    handle_scenes_command,
    handle_dedup_command,
    handle_prompts_command,
    handle_organize_command,
    handle_index_command,
    handle_comparison_command,
    handle_transitions_command,
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


def apply_cli_args_to_config(config: DictConfig, args: argparse.Namespace) -> None:
    """Apply CLI arguments to configuration."""
    # Map CLI args to config paths
    mappings = {
        "inbox": "paths.inbox",
        "output": "paths.organized",
        "move": "behavior.move_files",
        "dry_run": "behavior.dry_run",
        "force_reindex": "behavior.force_reindex",
        "quality": "quality.enabled",
        "understand": "understanding.enabled",
        "providers": "understanding.providers",
        "watch": "watch.enabled",
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
            if arg_name == "json" and arg_value:
                arg_value = "json"
            elif arg_name == "providers" and isinstance(arg_value, str):
                arg_value = [p.strip() for p in arg_value.split(",")]

            # Set the config value
            parts = config_path.split(".")
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = arg_value


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
        if args.check_deps:
            return 0 if check_dependencies() else 1

        # Setup logging
        setup_structured_logging(
            debug=args.debug,
            log_file=args.log_file,
            no_color=args.no_color,
        )

        # Load configuration
        config = load_config(args.config)

        # Apply CLI overrides
        if args.cli_overrides:
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