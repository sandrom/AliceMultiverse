"""Command-line parser creation for AliceMultiverse."""

import argparse

from ..version import __version__


def create_base_parser() -> argparse.ArgumentParser:
    """Create the base argument parser with description."""
    parser = argparse.ArgumentParser(
        description="""AliceMultiverse Debug CLI - For Development and Debugging Only

⚠️  DEPRECATION WARNING: Direct CLI usage is deprecated!
Alice is now an AI-native service designed to be used through AI assistants.

For normal usage, configure Alice with Claude Desktop or another AI assistant.
See: https://github.com/yourusername/AliceMultiverse/docs/integrations/claude-desktop.md

This CLI is maintained only for debugging and development purposes.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Debug Examples:
  %(prog)s --check-deps              # Check system dependencies
  %(prog)s --dry-run --verbose       # Debug organization logic
  %(prog)s keys setup                # Configure API keys
  %(prog)s mcp-server                # Start MCP server

For normal usage, use Alice through an AI assistant instead.
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    return parser


def add_keys_subcommand(subparsers):
    """Add keys management subcommand."""
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


def add_organization_args(parser):
    """Add media organization arguments."""
    # Directory arguments
    parser.add_argument(
        "-i",
        "--inbox",
        "--input",
        dest="inbox",
        help="Input directory containing media to organize",
    )

    parser.add_argument(
        "-o", "--output", "--organized", dest="output", help="Output directory for organized media"
    )

    parser.add_argument(
        "-c", "--config", help="Path to configuration file (default: settings.yaml)"
    )

    # Processing options
    parser.add_argument(
        "-m", "--move", action="store_true", help="Move files instead of copying them"
    )

    parser.add_argument(
        "-n",
        "--dry-run",
        "--preview",
        dest="dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )

    parser.add_argument(
        "-f",
        "--force",
        "--force-reindex",
        dest="force_reindex",
        action="store_true",
        help="Bypass cache and force re-analysis of all files",
    )

    parser.add_argument(
        "-Q",
        "--quality",
        "--assess-quality",
        dest="quality",
        action="store_true",
        help="Enable BRISQUE quality assessment for images",
    )

    parser.add_argument(
        "-u",
        "--understand",
        "--understanding",
        dest="understand",
        action="store_true",
        help="Enable AI understanding to analyze and tag images (costs apply)",
    )

    parser.add_argument(
        "--providers",
        help="AI providers to use for understanding (comma-separated: google,deepseek,anthropic,openai)",
    )

    parser.add_argument(
        "-w",
        "--watch",
        "--monitor",
        dest="watch",
        action="store_true",
        help="Watch mode: continuously monitor for new files",
    )

    parser.add_argument(
        "--enhanced-metadata",
        action="store_true",
        help="Enable enhanced metadata extraction for AI navigation (experimental)",
    )


def add_understanding_args(parser):
    """Add understanding-related arguments."""
    parser.add_argument(
        "--openai-key", help="OpenAI API key (overrides config)", dest="openai_api_key"
    )
    parser.add_argument(
        "--anthropic-key", help="Anthropic API key (overrides config)", dest="anthropic_api_key"
    )
    parser.add_argument(
        "--google-key", help="Google AI API key (overrides config)", dest="google_ai_api_key"
    )
    parser.add_argument(
        "--deepseek-key", help="DeepSeek API key (overrides config)", dest="deepseek_api_key"
    )
    parser.add_argument(
        "--cost-limit",
        type=float,
        help="Maximum cost limit for understanding operations (in USD)",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Request more detailed analysis from AI providers",
    )


def add_output_args(parser):
    """Add output-related arguments."""
    # Output options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output with detailed logging"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with development warnings"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress non-error output"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--log-file", help="Write logs to file"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )


def add_technical_args(parser):
    """Add technical/system arguments."""
    # System checks
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check system dependencies and exit",
    )

    # Config overrides
    parser.add_argument(
        "cli_overrides",
        nargs="*",
        help="Configuration overrides in the format key=value (e.g., paths.inbox=/custom/path)",
    )

    # Force CLI option
    parser.add_argument("--force-cli", action="store_true", help="Force CLI usage without deprecation warning")


def add_setup_subcommand(subparsers):
    """Add setup subcommand."""
    setup_parser = subparsers.add_parser(
        "setup",
        help="Run first-time setup wizard"
    )
    setup_parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="Reconfigure even if already set up"
    )


def add_recreate_subcommand(subparsers):
    """Add recreate subcommand."""
    recreate_parser = subparsers.add_parser("recreate", help="Recreate AI generations")
    recreate_subparsers = recreate_parser.add_subparsers(
        dest="recreate_command", help="Recreate commands"
    )

    # Recreate - inspect
    recreate_inspect = recreate_subparsers.add_parser("inspect", help="Inspect generation metadata")
    recreate_inspect.add_argument("file", help="Image file to inspect")

    # Recreate - recreate
    recreate_recreate = recreate_subparsers.add_parser("recreate", help="Recreate a generation")
    recreate_recreate.add_argument("file", help="Image file to recreate")
    recreate_recreate.add_argument("-p", "--provider", help="Provider to use")
    recreate_recreate.add_argument("-o", "--output", help="Output directory")
    recreate_recreate.add_argument("-v", "--variations", type=int, default=1, help="Number of variations")

    # Recreate - catalog
    recreate_catalog = recreate_subparsers.add_parser("catalog", help="Catalog generations in directory")
    recreate_catalog.add_argument("directory", help="Directory to catalog")
    recreate_catalog.add_argument("-o", "--output", help="Output catalog file")


def add_interface_subcommand(subparsers):
    """Add interface subcommand."""
    interface_parser = subparsers.add_parser(
        "interface",
        help="Start Alice web interface (AI-native server mode)"
    )
    interface_parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to"
    )
    interface_parser.add_argument(
        "--port", type=int, default=8080, help="Port to bind to"
    )


def add_mcp_subcommand(subparsers):
    """Add MCP server subcommand."""
    mcp_parser = subparsers.add_parser("mcp-server", help="Start MCP server for AI integration")
    mcp_parser.add_argument("--transport", default="stdio", help="Transport method")
    mcp_parser.add_argument("--host", help="Host for network transport")
    mcp_parser.add_argument("--port", type=int, help="Port for network transport")


def add_migrate_subcommand(subparsers):
    """Add migration subcommand."""
    migrate_parser = subparsers.add_parser("migrate", help="Migration tools")
    migrate_subparsers = migrate_parser.add_subparsers(
        dest="migrate_command", help="Migration commands"
    )

    # Migrate - from-legacy
    migrate_legacy = migrate_subparsers.add_parser("from-legacy", help="Migrate from legacy structure")
    migrate_legacy.add_argument("source", help="Legacy organized directory")
    migrate_legacy.add_argument("target", help="New organized directory")
    migrate_legacy.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")


def add_monitor_subcommand(subparsers):
    """Add monitor subcommand."""
    monitor_parser = subparsers.add_parser("monitor", help="Monitor AliceMultiverse operations")
    monitor_subparsers = monitor_parser.add_subparsers(
        dest="monitor_command", help="Monitor commands"
    )

    # Monitor - events
    monitor_events = monitor_subparsers.add_parser("events", help="Monitor real-time events")
    monitor_events.add_argument("-f", "--follow", action="store_true", help="Follow events continuously")
    monitor_events.add_argument("--filter", help="Filter events by type")
    monitor_events.add_argument("--format", choices=["json", "pretty"], default="pretty")

    # Monitor - metrics
    monitor_metrics = monitor_subparsers.add_parser("metrics", help="Show metrics")
    monitor_metrics.add_argument("--interval", type=int, help="Update interval in seconds")


def add_storage_subcommand(subparsers):
    """Add storage subcommand."""
    storage_parser = subparsers.add_parser("storage", help="Storage operations")
    storage_subparsers = storage_parser.add_subparsers(
        dest="storage_command", help="Storage commands"
    )

    # Storage - scan
    storage_scan = storage_subparsers.add_parser("scan", help="Scan directories for assets")
    storage_scan.add_argument("directories", nargs="+", help="Directories to scan")
    storage_scan.add_argument("-r", "--recursive", action="store_true", help="Scan recursively")

    # Storage - index
    storage_index = storage_subparsers.add_parser("index", help="Manage search index")
    storage_index.add_argument("action", choices=["rebuild", "update", "optimize"])


def add_scenes_subcommand(subparsers):
    """Add scenes subcommand."""
    scenes_parser = subparsers.add_parser("scenes", help="Scene detection and analysis")
    scenes_subparsers = scenes_parser.add_subparsers(
        dest="scenes_command", help="Scene commands"
    )

    # Scenes - detect
    scenes_detect = scenes_subparsers.add_parser("detect", help="Detect scenes in video")
    scenes_detect.add_argument("video", help="Video file to analyze")
    scenes_detect.add_argument("-o", "--output", help="Output JSON file")
    scenes_detect.add_argument("-t", "--threshold", type=float, default=30.0, help="Scene change threshold")

    # Scenes - shotlist
    scenes_shotlist = scenes_subparsers.add_parser("shotlist", help="Generate shot list from scenes")
    scenes_shotlist.add_argument("scenes_file", help="Scenes JSON file")
    scenes_shotlist.add_argument("-o", "--output", required=True, help="Output file")
    scenes_shotlist.add_argument("-f", "--format", choices=["json", "csv", "markdown"], default="json")

    # Scenes - extract
    scenes_extract = scenes_subparsers.add_parser("extract", help="Extract frames from scenes")
    scenes_extract.add_argument("video", help="Video file")
    scenes_extract.add_argument("-o", "--output", help="Output directory")
    scenes_extract.add_argument("--scenes-file", help="Use existing scenes JSON")


def add_dedup_subcommand(subparsers):
    """Add deduplication subcommand."""
    dedup_parser = subparsers.add_parser("dedup", help="Advanced deduplication with perceptual hashing")
    dedup_subparsers = dedup_parser.add_subparsers(
        dest="dedup_command", help="Deduplication commands"
    )

    # Dedup - find
    dedup_find = dedup_subparsers.add_parser("find", help="Find duplicate and similar images")
    dedup_find.add_argument("directory", help="Directory to scan")
    dedup_find.add_argument("-t", "--threshold", type=float, default=0.9, help="Similarity threshold")

    # Dedup - remove
    dedup_remove = dedup_subparsers.add_parser("remove", help="Remove duplicate images")
    dedup_remove.add_argument("report", help="JSON report from find command")
    dedup_remove.add_argument("-s", "--strategy", choices=["safe", "aggressive"], default="safe")


def add_prompts_subcommand(subparsers):
    """Add prompts management subcommand."""
    prompts_parser = subparsers.add_parser("prompts", help="Manage AI prompts and their effectiveness")
    prompts_subparsers = prompts_parser.add_subparsers(
        dest="prompts_command", help="Prompt management commands"
    )

    # Prompts - add
    prompts_add = prompts_subparsers.add_parser("add", help="Add a new prompt")
    prompts_add.add_argument("-t", "--text", required=True, help="The prompt text")
    prompts_add.add_argument("-c", "--category", required=True, help="Prompt category")

    # Prompts - search
    prompts_search = prompts_subparsers.add_parser("search", help="Search for prompts")
    prompts_search.add_argument("-q", "--query", help="Search query")


def add_index_subcommand(subparsers):
    """Add index subcommand."""
    index_parser = subparsers.add_parser("index", help="Manage search index")
    index_subparsers = index_parser.add_subparsers(
        dest="index_command", help="Index management commands"
    )

    # Index - rebuild
    index_rebuild = index_subparsers.add_parser("rebuild", help="Rebuild search index from files")
    index_rebuild.add_argument(
        "paths", nargs="+", help="Paths to scan for media files"
    )
    index_rebuild.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    # Index - update
    index_update = index_subparsers.add_parser("update", help="Update index with new/modified files")
    index_update.add_argument(
        "path", help="Path to scan for updates"
    )

    # Index - verify
    index_subparsers.add_parser("verify", help="Verify index integrity")

    # Index - stats
    index_subparsers.add_parser("stats", help="Show index statistics")


def add_comparison_subcommand(subparsers):
    """Add comparison subcommand."""
    comparison_parser = subparsers.add_parser("comparison", help="Model comparison system")
    comparison_subparsers = comparison_parser.add_subparsers(
        dest="comparison_command", help="Comparison commands"
    )

    # Comparison - server
    comparison_server = comparison_subparsers.add_parser("server", help="Start web interface")
    comparison_server.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    comparison_server.add_argument(
        "--port", type=int, default=8000, help="Port to listen on (default: 8000)"
    )
    comparison_server.add_argument(
        "--populate-test-data", action="store_true", help="Populate with test data (development only)"
    )

    # Comparison - populate
    comparison_populate = comparison_subparsers.add_parser("populate", help="Populate with images")
    comparison_populate.add_argument("directory", help="Directory to scan")
    comparison_populate.add_argument("-r", "--recursive", action="store_true", help="Search recursively")
    comparison_populate.add_argument("-l", "--limit", type=int, help="Maximum number to add")

    # Comparison - populate-default
    comparison_populate_default = comparison_subparsers.add_parser("populate-default", help="Populate from default dirs")
    comparison_populate_default.add_argument("-l", "--limit", type=int, help="Maximum number to add")

    # Comparison - stats
    comparison_subparsers.add_parser("stats", help="Show model rankings")

    # Comparison - reset
    comparison_subparsers.add_parser("reset", help="Reset all comparison data")


def add_transitions_subcommand(subparsers):
    """Add transitions subcommand."""
    transitions_parser = subparsers.add_parser("transitions", help="Analyze scene transitions")
    transitions_subparsers = transitions_parser.add_subparsers(
        dest="transitions_command", help="Transition analysis commands"
    )

    # Transitions - analyze
    transitions_analyze = transitions_subparsers.add_parser("analyze", help="Analyze transitions between images")
    transitions_analyze.add_argument("images", nargs="+", help="Image files to analyze (in sequence order)")
    transitions_analyze.add_argument("-o", "--output", help="Output JSON file for results")
    transitions_analyze.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # Transitions - motion
    transitions_motion = transitions_subparsers.add_parser("motion", help="Analyze motion in a single image")
    transitions_motion.add_argument("image", help="Image file to analyze")
    transitions_motion.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
