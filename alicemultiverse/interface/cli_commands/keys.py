"""API key management commands."""

import argparse


def add_keys_commands(subparsers: argparse._SubParsersAction) -> None:
    """Add keys management commands to the parser."""
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
    keys_subparsers.add_parser("list", help="List stored API keys")

    # Keys - setup
    keys_subparsers.add_parser("setup", help="Interactive setup wizard")
