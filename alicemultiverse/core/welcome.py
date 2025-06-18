"""Welcome messages and first-time user guidance."""

from pathlib import Path

from .keys import APIKeyManager


def show_welcome_message() -> None:
    """Show welcome message for first-time users."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          Welcome to AliceMultiverse! 🎨                       ║
║                                                               ║
║     AI-Native Creative Asset Management System                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

AliceMultiverse helps you organize and understand your AI-generated
images through natural conversation with AI assistants.
""")


def check_setup_status() -> tuple[bool, str]:
    """Check if Alice is properly set up.

    Returns:
        (is_setup, message): Whether setup is complete and a status message
    """
    issues = []
    warnings = []

    # Check config
    if not Path("settings.yaml").exists():
        issues.append("No configuration file found")

    # Check API keys
    key_manager = APIKeyManager()
    has_key = False
    for provider in ["anthropic", "openai", "google", "deepseek"]:
        if key_manager.get_api_key(provider):
            has_key = True
            break

    if not has_key:
        warnings.append("No AI provider API keys configured (AI features disabled)")

    # Check directories
    if Path("settings.yaml").exists():
        try:
            from .config import load_config
            config = load_config()
            inbox = Path(config.paths.inbox)
            organized = Path(config.paths.organized)

            if not inbox.exists():
                warnings.append(f"Inbox directory doesn't exist: {inbox}")
            if not organized.exists():
                warnings.append(f"Organized directory doesn't exist: {organized}")
        except Exception:
            issues.append("Configuration file is invalid")

    # Determine status
    if issues:
        return False, "Setup incomplete"
    elif warnings:
        return True, "Setup complete with warnings"
    else:
        return True, "Ready to organize!"


def show_quick_start() -> None:
    """Show quick start guide for new users."""
    is_setup, status = check_setup_status()

    if not is_setup:
        print("""
❌ Setup Required
─────────────────
AliceMultiverse needs initial configuration.

Run: alice setup

This will help you:
• Configure API keys for AI understanding
• Set up your inbox and organized directories
• Test that everything works
""")
    else:
        print(f"""
✅ {status}
─────────────────

Quick Commands:
• alice setup         - Run setup wizard
• alice keys setup    - Configure API keys
• alice --help        - Show all options

AI Assistant Usage (Recommended):
• alice mcp-server    - Start for Claude Desktop
• Then ask Claude: "Help me organize my AI images"

Debug Mode (for testing):
• alice --debug --dry-run    - Preview what would happen
• alice --debug --understand - Run with AI analysis
""")

        # Show warnings if any
        _, status_msg = check_setup_status()
        if "warnings" in status_msg:
            print("\n⚠️  Warnings:")
            key_manager = APIKeyManager()
            if not any(key_manager.get_api_key(p) for p in ["anthropic", "openai", "google", "deepseek"]):
                print("  • No API keys configured - AI features disabled")
                print("    Run: alice keys setup")


def show_first_run_prompt() -> bool:
    """Show first-run prompt and return whether to continue.

    Returns:
        True if user wants to run setup, False to skip
    """
    show_welcome_message()

    is_setup, status = check_setup_status()

    if not is_setup:
        print("⚡ First-time setup required!\n")
        response = input("Would you like to run the setup wizard now? (Y/n): ").strip().lower()
        return response != 'n'
    else:
        show_quick_start()
        return False
