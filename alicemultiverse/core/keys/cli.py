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
    elif args.keys_command == "get":
        return _handle_get(manager, args)
    elif args.keys_command == "delete":
        return _handle_delete(manager, args)
    elif args.keys_command == "list":
        return _handle_list(manager)
    elif args.keys_command == "setup":
        return _handle_setup(manager)
    else:
        logger.error(f"Unknown keys command: {args.keys_command}")
        return 1


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

    print("Configured API keys:")
    for key_info in sorted(keys):
        print(f"  • {key_info}")

    return 0
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code -     logger.error(f"Failed to list keys: {e}")
    # TODO: Review unreachable code -     return 1


def _handle_setup(manager: APIKeyManager) -> int:
    """Handle setup command - run interactive setup wizard."""
    print("AliceMultiverse API Key Setup Wizard")
    print("=" * 40)
    print()
    print("This wizard will help you configure API keys securely in macOS Keychain.")
    print()
    print("Note: For containerized environments, use environment variables instead:")
    print("  • SIGHTENGINE_API_USER and SIGHTENGINE_API_SECRET")
    print("  • ANTHROPIC_API_KEY")
    print()

    # Use keychain for secure storage
    method = "keychain"

    while True:
        print("Which API key would you like to configure?")
        print()
        print("1. SightEngine (quality assessment)")
        print("2. Anthropic Claude (AI defect detection)")
        print("3. Exit setup")
        print()

        choice = input("Select option [1-3]: ").strip()

        if choice == "1":
            # SightEngine setup
            print()
            print("SightEngine Setup")
            print("-" * 30)
            print("SightEngine provides advanced quality assessment.")
            print("Get your API credentials at: https://sightengine.com")
            print()

            api_user = input("SightEngine API User: ").strip()
            api_secret = input("SightEngine API Secret: ").strip()

            if api_user and api_secret:
                try:
                    manager.set_api_key("sightengine_user", api_user, method)
                    manager.set_api_key("sightengine_secret", api_secret, method)
                    print("✓ SightEngine credentials saved to macOS Keychain")
                except Exception as e:
                    print(f"✗ Failed to save SightEngine credentials: {e}")
            else:
                print("✗ Both API User and Secret are required")
            print()

        elif choice == "2":
            # Anthropic Claude setup
            print()
            print("Anthropic Claude Setup")
            print("-" * 30)
            print("Claude provides AI defect detection for premium pipeline.")
            print("Get your API key at: https://console.anthropic.com")
            print()

            import getpass

            api_key = getpass.getpass("Anthropic API Key: ").strip()

            if api_key:
                try:
                    manager.set_api_key("anthropic_api_key", api_key, method)
                    print("✓ Anthropic API key saved to macOS Keychain")
                except Exception as e:
                    print(f"✗ Failed to save Anthropic API key: {e}")
            else:
                print("✗ API key is required")
            print()

        elif choice == "3":
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
            print()

    print()
    print("Setup complete!")
    print()
    print("You can view your configured keys with:")
    print("  alice keys list")
    print()

    return 0


def run_interactive_setup() -> int:
    """Run interactive setup wizard (legacy function for compatibility)."""
    manager = APIKeyManager()
    return _handle_setup(manager)
