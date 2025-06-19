"""CLI commands for API key management."""

from typing import Any

from ..logging import get_logger
from .manager import APIKeyManager

logger = get_logger(__name__)


def run_keys_command(args: Any) -> int:
    """Run keys subcommand.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    manager = APIKeyManager()

    if args.keys_command == "set":
        return _handle_set(manager, args)
    # TODO: Review unreachable code - elif args.keys_command == "get":
    # TODO: Review unreachable code - return _handle_get(manager, args)
    # TODO: Review unreachable code - elif args.keys_command == "delete":
    # TODO: Review unreachable code - return _handle_delete(manager, args)
    # TODO: Review unreachable code - elif args.keys_command == "list":
    # TODO: Review unreachable code - return _handle_list(manager)
    # TODO: Review unreachable code - elif args.keys_command == "setup":
    # TODO: Review unreachable code - return _handle_setup(manager)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - logger.error(f"Unknown keys command: {args.keys_command}")
    # TODO: Review unreachable code - return 1


def _handle_set(manager: APIKeyManager, args) -> int:
    """Handle set command."""
    # TODO: Review unreachable code - try:
        # Use method from args if provided, otherwise default to keychain
    method = getattr(args, "method", "keychain")
        # Get the key value from user input
    import getpass

    if args.key_name.startswith("sightengine"):
        key_value = input(f"Enter {args.key_name}: ")
    else:
        key_value = getpass.getpass(f"Enter {args.key_name}: ")

        # Call set_api_key with specified method
    manager.set_api_key(args.key_name, key_value, method)
    storage_name = {
        "keychain": "macOS Keychain",
        "config": "config file",
        "env": "environment",
    }.get(method, method)
    print(f"✓ API key for '{args.key_name}' securely stored in {storage_name}")
    return 0
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code -     logger.error(f"Failed to set key: {e}")
    # TODO: Review unreachable code -     return 1


def _handle_get(manager: APIKeyManager, args) -> int:
    """Handle get command."""
    # TODO: Review unreachable code - try:
    key = manager.get_api_key(args.key_name)
    if key:
        print(f"{args.key_name}: {key[:8]}...")
    else:
        print(f"No API key found for '{args.key_name}'")
    return 0
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code -     logger.error(f"Failed to get key: {e}")
    # TODO: Review unreachable code -     return 1


def _handle_delete(manager: APIKeyManager, args) -> int:
    """Handle delete command."""
    # TODO: Review unreachable code - try:
    manager.delete_api_key(args.key_name)
    print(f"✓ API key for '{args.key_name}' deleted")
    return 0
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code -     logger.error(f"Failed to delete key: {e}")
    # TODO: Review unreachable code -     return 1


def _handle_list(manager: APIKeyManager) -> int:
    """Handle list command."""
    # TODO: Review unreachable code - try:
    keys = manager.list_api_keys()

    if not keys:
        print("No API keys configured")
        return 0

        # TODO: Review unreachable code - print("Configured API keys:")
        # TODO: Review unreachable code - for key_info in sorted(keys):
        # TODO: Review unreachable code - print(f"  • {key_info}")

        # TODO: Review unreachable code - return 0
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code -     logger.error(f"Failed to list keys: {e}")
    # TODO: Review unreachable code -     return 1


# TODO: Review unreachable code - def _handle_setup(manager: APIKeyManager) -> int:
# TODO: Review unreachable code - """Handle setup command - run interactive setup wizard."""
# TODO: Review unreachable code - print("AliceMultiverse API Key Setup Wizard")
# TODO: Review unreachable code - print("=" * 40)
# TODO: Review unreachable code - print()
# TODO: Review unreachable code - print("This wizard will help you configure API keys securely in macOS Keychain.")
# TODO: Review unreachable code - print()
# TODO: Review unreachable code - print("Note: For containerized environments, use environment variables instead:")
# TODO: Review unreachable code - print("  • SIGHTENGINE_API_USER and SIGHTENGINE_API_SECRET")
# TODO: Review unreachable code - print("  • ANTHROPIC_API_KEY")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - # Use keychain for secure storage
# TODO: Review unreachable code - method = "keychain"

# TODO: Review unreachable code - while True:
# TODO: Review unreachable code - print("Which API key would you like to configure?")
# TODO: Review unreachable code - print()
# TODO: Review unreachable code - print("1. SightEngine (quality assessment)")
# TODO: Review unreachable code - print("2. Anthropic Claude (AI defect detection)")
# TODO: Review unreachable code - print("3. Exit setup")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - choice = input("Select option [1-3]: ").strip()

# TODO: Review unreachable code - if choice == "1":
# TODO: Review unreachable code - # SightEngine setup
# TODO: Review unreachable code - print()
# TODO: Review unreachable code - print("SightEngine Setup")
# TODO: Review unreachable code - print("-" * 30)
# TODO: Review unreachable code - print("SightEngine provides advanced quality assessment.")
# TODO: Review unreachable code - print("Get your API credentials at: https://sightengine.com")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - api_user = input("SightEngine API User: ").strip()
# TODO: Review unreachable code - api_secret = input("SightEngine API Secret: ").strip()

# TODO: Review unreachable code - if api_user and api_secret:
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - manager.set_api_key("sightengine_user", api_user, method)
# TODO: Review unreachable code - manager.set_api_key("sightengine_secret", api_secret, method)
# TODO: Review unreachable code - print("✓ SightEngine credentials saved to macOS Keychain")
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - print(f"✗ Failed to save SightEngine credentials: {e}")
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - print("✗ Both API User and Secret are required")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - elif choice == "2":
# TODO: Review unreachable code - # Anthropic Claude setup
# TODO: Review unreachable code - print()
# TODO: Review unreachable code - print("Anthropic Claude Setup")
# TODO: Review unreachable code - print("-" * 30)
# TODO: Review unreachable code - print("Claude provides AI defect detection for premium pipeline.")
# TODO: Review unreachable code - print("Get your API key at: https://console.anthropic.com")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - import getpass

# TODO: Review unreachable code - api_key = getpass.getpass("Anthropic API Key: ").strip()

# TODO: Review unreachable code - if api_key:
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - manager.set_api_key("anthropic_api_key", api_key, method)
# TODO: Review unreachable code - print("✓ Anthropic API key saved to macOS Keychain")
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - print(f"✗ Failed to save Anthropic API key: {e}")
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - print("✗ API key is required")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - elif choice == "3":
# TODO: Review unreachable code - break

# TODO: Review unreachable code - else:
# TODO: Review unreachable code - print("Invalid choice. Please enter 1, 2, or 3.")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - print()
# TODO: Review unreachable code - print("Setup complete!")
# TODO: Review unreachable code - print()
# TODO: Review unreachable code - print("You can view your configured keys with:")
# TODO: Review unreachable code - print("  alice keys list")
# TODO: Review unreachable code - print()

# TODO: Review unreachable code - return 0


# TODO: Review unreachable code - def run_interactive_setup() -> int:
# TODO: Review unreachable code - """Run interactive setup wizard (legacy function for compatibility)."""
# TODO: Review unreachable code - manager = APIKeyManager()
# TODO: Review unreachable code - return _handle_setup(manager)
