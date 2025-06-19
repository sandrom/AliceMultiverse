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


# TODO: Review unreachable code - def add_keys_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add keys management subcommand."""
# TODO: Review unreachable code - keys_parser = subparsers.add_parser("keys", help="Manage API keys")
# TODO: Review unreachable code - keys_subparsers = keys_parser.add_subparsers(
# TODO: Review unreachable code - dest="keys_command", help="Key management commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Keys - set
# TODO: Review unreachable code - keys_set = keys_subparsers.add_parser("set", help="Set an API key")
# TODO: Review unreachable code - keys_set.add_argument(
# TODO: Review unreachable code - "key_name",
# TODO: Review unreachable code - choices=["sightengine_user", "sightengine_secret", "anthropic_api_key"],
# TODO: Review unreachable code - help="API key to set",
# TODO: Review unreachable code - )
# TODO: Review unreachable code - keys_set.add_argument(
# TODO: Review unreachable code - "--method",
# TODO: Review unreachable code - choices=["keychain", "config", "env"],
# TODO: Review unreachable code - default="keychain",
# TODO: Review unreachable code - help="Storage method (default: keychain on macOS)",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Keys - get
# TODO: Review unreachable code - keys_get = keys_subparsers.add_parser("get", help="Get an API key")
# TODO: Review unreachable code - keys_get.add_argument(
# TODO: Review unreachable code - "key_name",
# TODO: Review unreachable code - choices=["sightengine_user", "sightengine_secret", "anthropic_api_key"],
# TODO: Review unreachable code - help="API key to get",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Keys - delete
# TODO: Review unreachable code - keys_delete = keys_subparsers.add_parser("delete", help="Delete an API key")
# TODO: Review unreachable code - keys_delete.add_argument(
# TODO: Review unreachable code - "key_name",
# TODO: Review unreachable code - choices=["sightengine_user", "sightengine_secret", "anthropic_api_key"],
# TODO: Review unreachable code - help="API key to delete",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Keys - list
# TODO: Review unreachable code - keys_subparsers.add_parser("list", help="List stored API keys")

# TODO: Review unreachable code - # Keys - setup
# TODO: Review unreachable code - keys_subparsers.add_parser("setup", help="Interactive setup wizard")


# TODO: Review unreachable code - def add_organization_args(parser) -> None:
# TODO: Review unreachable code - """Add media organization arguments."""
# TODO: Review unreachable code - # Directory arguments
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-i",
# TODO: Review unreachable code - "--inbox",
# TODO: Review unreachable code - "--input",
# TODO: Review unreachable code - dest="inbox",
# TODO: Review unreachable code - help="Input directory containing media to organize",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-o", "--output", "--organized", dest="output", help="Output directory for organized media"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-c", "--config", help="Path to configuration file (default: settings.yaml)"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Processing options
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-m", "--move", action="store_true", help="Move files instead of copying them"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-n",
# TODO: Review unreachable code - "--dry-run",
# TODO: Review unreachable code - "--preview",
# TODO: Review unreachable code - dest="dry_run",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Show what would be done without actually doing it",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-f",
# TODO: Review unreachable code - "--force",
# TODO: Review unreachable code - "--force-reindex",
# TODO: Review unreachable code - dest="force_reindex",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Bypass cache and force re-analysis of all files",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-Q",
# TODO: Review unreachable code - "--quality",
# TODO: Review unreachable code - "--assess-quality",
# TODO: Review unreachable code - dest="quality",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Enable BRISQUE quality assessment for images",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-u",
# TODO: Review unreachable code - "--understand",
# TODO: Review unreachable code - "--understanding",
# TODO: Review unreachable code - dest="understand",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Enable AI understanding to analyze and tag images (costs apply)",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--providers",
# TODO: Review unreachable code - help="AI providers to use for understanding (comma-separated: google,deepseek,anthropic,openai)",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-w",
# TODO: Review unreachable code - "--watch",
# TODO: Review unreachable code - "--monitor",
# TODO: Review unreachable code - dest="watch",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Watch mode: continuously monitor for new files",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--enhanced-metadata",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Enable enhanced metadata extraction for AI navigation (experimental)",
# TODO: Review unreachable code - )


# TODO: Review unreachable code - def add_understanding_args(parser) -> None:
# TODO: Review unreachable code - """Add understanding-related arguments."""
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--openai-key", help="OpenAI API key (overrides config)", dest="openai_api_key"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--anthropic-key", help="Anthropic API key (overrides config)", dest="anthropic_api_key"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--google-key", help="Google AI API key (overrides config)", dest="google_ai_api_key"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--deepseek-key", help="DeepSeek API key (overrides config)", dest="deepseek_api_key"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--cost-limit",
# TODO: Review unreachable code - type=float,
# TODO: Review unreachable code - help="Maximum cost limit for understanding operations (in USD)",
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--detailed",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Request more detailed analysis from AI providers",
# TODO: Review unreachable code - )


# TODO: Review unreachable code - def add_output_args(parser) -> None:
# TODO: Review unreachable code - """Add output-related arguments."""
# TODO: Review unreachable code - # Output options
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-v", "--verbose", action="store_true", help="Enable verbose output with detailed logging"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--debug", action="store_true", help="Enable debug mode with development warnings"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "-q", "--quiet", action="store_true", help="Suppress non-error output"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--json", action="store_true", help="Output results in JSON format"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--log-file", help="Write logs to file"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--no-color", action="store_true", help="Disable colored output"
# TODO: Review unreachable code - )


# TODO: Review unreachable code - def add_technical_args(parser) -> None:
# TODO: Review unreachable code - """Add technical/system arguments."""
# TODO: Review unreachable code - # System checks
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "--check-deps",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Check system dependencies and exit",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Config overrides
# TODO: Review unreachable code - parser.add_argument(
# TODO: Review unreachable code - "cli_overrides",
# TODO: Review unreachable code - nargs="*",
# TODO: Review unreachable code - help="Configuration overrides in the format key=value (e.g., paths.inbox=/custom/path)",
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Force CLI option
# TODO: Review unreachable code - parser.add_argument("--force-cli", action="store_true", help="Force CLI usage without deprecation warning")


# TODO: Review unreachable code - def add_setup_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add setup subcommand."""
# TODO: Review unreachable code - setup_parser = subparsers.add_parser(
# TODO: Review unreachable code - "setup",
# TODO: Review unreachable code - help="Run first-time setup wizard"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - setup_parser.add_argument(
# TODO: Review unreachable code - "--reconfigure",
# TODO: Review unreachable code - action="store_true",
# TODO: Review unreachable code - help="Reconfigure even if already set up"
# TODO: Review unreachable code - )


# TODO: Review unreachable code - def add_recreate_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add recreate subcommand."""
# TODO: Review unreachable code - recreate_parser = subparsers.add_parser("recreate", help="Recreate AI generations")
# TODO: Review unreachable code - recreate_subparsers = recreate_parser.add_subparsers(
# TODO: Review unreachable code - dest="recreate_command", help="Recreate commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Recreate - inspect
# TODO: Review unreachable code - recreate_inspect = recreate_subparsers.add_parser("inspect", help="Inspect generation metadata")
# TODO: Review unreachable code - recreate_inspect.add_argument("file", help="Image file to inspect")

# TODO: Review unreachable code - # Recreate - recreate
# TODO: Review unreachable code - recreate_recreate = recreate_subparsers.add_parser("recreate", help="Recreate a generation")
# TODO: Review unreachable code - recreate_recreate.add_argument("file", help="Image file to recreate")
# TODO: Review unreachable code - recreate_recreate.add_argument("-p", "--provider", help="Provider to use")
# TODO: Review unreachable code - recreate_recreate.add_argument("-o", "--output", help="Output directory")
# TODO: Review unreachable code - recreate_recreate.add_argument("-v", "--variations", type=int, default=1, help="Number of variations")

# TODO: Review unreachable code - # Recreate - catalog
# TODO: Review unreachable code - recreate_catalog = recreate_subparsers.add_parser("catalog", help="Catalog generations in directory")
# TODO: Review unreachable code - recreate_catalog.add_argument("directory", help="Directory to catalog")
# TODO: Review unreachable code - recreate_catalog.add_argument("-o", "--output", help="Output catalog file")


# TODO: Review unreachable code - def add_interface_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add interface subcommand."""
# TODO: Review unreachable code - interface_parser = subparsers.add_parser(
# TODO: Review unreachable code - "interface",
# TODO: Review unreachable code - help="Start Alice web interface (AI-native server mode)"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - interface_parser.add_argument(
# TODO: Review unreachable code - "--host", default="127.0.0.1", help="Host to bind to"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - interface_parser.add_argument(
# TODO: Review unreachable code - "--port", type=int, default=8080, help="Port to bind to"
# TODO: Review unreachable code - )


# TODO: Review unreachable code - def add_mcp_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add MCP server subcommand."""
# TODO: Review unreachable code - mcp_parser = subparsers.add_parser("mcp-server", help="Start MCP server for AI integration")
# TODO: Review unreachable code - mcp_parser.add_argument("--transport", default="stdio", help="Transport method")
# TODO: Review unreachable code - mcp_parser.add_argument("--host", help="Host for network transport")
# TODO: Review unreachable code - mcp_parser.add_argument("--port", type=int, help="Port for network transport")


# TODO: Review unreachable code - def add_migrate_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add migration subcommand."""
# TODO: Review unreachable code - migrate_parser = subparsers.add_parser("migrate", help="Migration tools")
# TODO: Review unreachable code - migrate_subparsers = migrate_parser.add_subparsers(
# TODO: Review unreachable code - dest="migrate_command", help="Migration commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Migrate - from-legacy
# TODO: Review unreachable code - migrate_legacy = migrate_subparsers.add_parser("from-legacy", help="Migrate from legacy structure")
# TODO: Review unreachable code - migrate_legacy.add_argument("source", help="Legacy organized directory")
# TODO: Review unreachable code - migrate_legacy.add_argument("target", help="New organized directory")
# TODO: Review unreachable code - migrate_legacy.add_argument("-n", "--dry-run", action="store_true", help="Show what would be done")


# TODO: Review unreachable code - def add_monitor_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add monitor subcommand."""
# TODO: Review unreachable code - monitor_parser = subparsers.add_parser("monitor", help="Monitor AliceMultiverse operations")
# TODO: Review unreachable code - monitor_subparsers = monitor_parser.add_subparsers(
# TODO: Review unreachable code - dest="monitor_command", help="Monitor commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Monitor - events
# TODO: Review unreachable code - monitor_events = monitor_subparsers.add_parser("events", help="Monitor real-time events")
# TODO: Review unreachable code - monitor_events.add_argument("-f", "--follow", action="store_true", help="Follow events continuously")
# TODO: Review unreachable code - monitor_events.add_argument("--filter", help="Filter events by type")
# TODO: Review unreachable code - monitor_events.add_argument("--format", choices=["json", "pretty"], default="pretty")

# TODO: Review unreachable code - # Monitor - metrics
# TODO: Review unreachable code - monitor_metrics = monitor_subparsers.add_parser("metrics", help="Show metrics")
# TODO: Review unreachable code - monitor_metrics.add_argument("--interval", type=int, help="Update interval in seconds")


# TODO: Review unreachable code - def add_storage_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add storage subcommand."""
# TODO: Review unreachable code - storage_parser = subparsers.add_parser("storage", help="Storage operations")
# TODO: Review unreachable code - storage_subparsers = storage_parser.add_subparsers(
# TODO: Review unreachable code - dest="storage_command", help="Storage commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Storage - scan
# TODO: Review unreachable code - storage_scan = storage_subparsers.add_parser("scan", help="Scan directories for assets")
# TODO: Review unreachable code - storage_scan.add_argument("directories", nargs="+", help="Directories to scan")
# TODO: Review unreachable code - storage_scan.add_argument("-r", "--recursive", action="store_true", help="Scan recursively")

# TODO: Review unreachable code - # Storage - index
# TODO: Review unreachable code - storage_index = storage_subparsers.add_parser("index", help="Manage search index")
# TODO: Review unreachable code - storage_index.add_argument("action", choices=["rebuild", "update", "optimize"])


# TODO: Review unreachable code - def add_scenes_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add scenes subcommand."""
# TODO: Review unreachable code - scenes_parser = subparsers.add_parser("scenes", help="Scene detection and analysis")
# TODO: Review unreachable code - scenes_subparsers = scenes_parser.add_subparsers(
# TODO: Review unreachable code - dest="scenes_command", help="Scene commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Scenes - detect
# TODO: Review unreachable code - scenes_detect = scenes_subparsers.add_parser("detect", help="Detect scenes in video")
# TODO: Review unreachable code - scenes_detect.add_argument("video", help="Video file to analyze")
# TODO: Review unreachable code - scenes_detect.add_argument("-o", "--output", help="Output JSON file")
# TODO: Review unreachable code - scenes_detect.add_argument("-t", "--threshold", type=float, default=30.0, help="Scene change threshold")

# TODO: Review unreachable code - # Scenes - shotlist
# TODO: Review unreachable code - scenes_shotlist = scenes_subparsers.add_parser("shotlist", help="Generate shot list from scenes")
# TODO: Review unreachable code - scenes_shotlist.add_argument("scenes_file", help="Scenes JSON file")
# TODO: Review unreachable code - scenes_shotlist.add_argument("-o", "--output", required=True, help="Output file")
# TODO: Review unreachable code - scenes_shotlist.add_argument("-f", "--format", choices=["json", "csv", "markdown"], default="json")

# TODO: Review unreachable code - # Scenes - extract
# TODO: Review unreachable code - scenes_extract = scenes_subparsers.add_parser("extract", help="Extract frames from scenes")
# TODO: Review unreachable code - scenes_extract.add_argument("video", help="Video file")
# TODO: Review unreachable code - scenes_extract.add_argument("-o", "--output", help="Output directory")
# TODO: Review unreachable code - scenes_extract.add_argument("--scenes-file", help="Use existing scenes JSON")


# TODO: Review unreachable code - def add_dedup_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add deduplication subcommand."""
# TODO: Review unreachable code - dedup_parser = subparsers.add_parser("dedup", help="Advanced deduplication with perceptual hashing")
# TODO: Review unreachable code - dedup_subparsers = dedup_parser.add_subparsers(
# TODO: Review unreachable code - dest="dedup_command", help="Deduplication commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Dedup - find
# TODO: Review unreachable code - dedup_find = dedup_subparsers.add_parser("find", help="Find duplicate and similar images")
# TODO: Review unreachable code - dedup_find.add_argument("directory", help="Directory to scan")
# TODO: Review unreachable code - dedup_find.add_argument("-t", "--threshold", type=float, default=0.9, help="Similarity threshold")

# TODO: Review unreachable code - # Dedup - remove
# TODO: Review unreachable code - dedup_remove = dedup_subparsers.add_parser("remove", help="Remove duplicate images")
# TODO: Review unreachable code - dedup_remove.add_argument("report", help="JSON report from find command")
# TODO: Review unreachable code - dedup_remove.add_argument("-s", "--strategy", choices=["safe", "aggressive"], default="safe")


# TODO: Review unreachable code - def add_prompts_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add prompts management subcommand."""
# TODO: Review unreachable code - prompts_parser = subparsers.add_parser("prompts", help="Manage AI prompts and their effectiveness")
# TODO: Review unreachable code - prompts_subparsers = prompts_parser.add_subparsers(
# TODO: Review unreachable code - dest="prompts_command", help="Prompt management commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Prompts - add
# TODO: Review unreachable code - prompts_add = prompts_subparsers.add_parser("add", help="Add a new prompt")
# TODO: Review unreachable code - prompts_add.add_argument("-t", "--text", required=True, help="The prompt text")
# TODO: Review unreachable code - prompts_add.add_argument("-c", "--category", required=True, help="Prompt category")

# TODO: Review unreachable code - # Prompts - search
# TODO: Review unreachable code - prompts_search = prompts_subparsers.add_parser("search", help="Search for prompts")
# TODO: Review unreachable code - prompts_search.add_argument("-q", "--query", help="Search query")


# TODO: Review unreachable code - def add_index_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add index subcommand."""
# TODO: Review unreachable code - index_parser = subparsers.add_parser("index", help="Manage search index")
# TODO: Review unreachable code - index_subparsers = index_parser.add_subparsers(
# TODO: Review unreachable code - dest="index_command", help="Index management commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Index - rebuild
# TODO: Review unreachable code - index_rebuild = index_subparsers.add_parser("rebuild", help="Rebuild search index from files")
# TODO: Review unreachable code - index_rebuild.add_argument(
# TODO: Review unreachable code - "paths", nargs="+", help="Paths to scan for media files"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - index_rebuild.add_argument(
# TODO: Review unreachable code - "--no-progress", action="store_true", help="Disable progress bar"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Index - update
# TODO: Review unreachable code - index_update = index_subparsers.add_parser("update", help="Update index with new/modified files")
# TODO: Review unreachable code - index_update.add_argument(
# TODO: Review unreachable code - "path", help="Path to scan for updates"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Index - verify
# TODO: Review unreachable code - index_subparsers.add_parser("verify", help="Verify index integrity")

# TODO: Review unreachable code - # Index - stats
# TODO: Review unreachable code - index_subparsers.add_parser("stats", help="Show index statistics")


# TODO: Review unreachable code - def add_comparison_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add comparison subcommand."""
# TODO: Review unreachable code - comparison_parser = subparsers.add_parser("comparison", help="Model comparison system")
# TODO: Review unreachable code - comparison_subparsers = comparison_parser.add_subparsers(
# TODO: Review unreachable code - dest="comparison_command", help="Comparison commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Comparison - server
# TODO: Review unreachable code - comparison_server = comparison_subparsers.add_parser("server", help="Start web interface")
# TODO: Review unreachable code - comparison_server.add_argument(
# TODO: Review unreachable code - "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - comparison_server.add_argument(
# TODO: Review unreachable code - "--port", type=int, default=8000, help="Port to listen on (default: 8000)"
# TODO: Review unreachable code - )
# TODO: Review unreachable code - comparison_server.add_argument(
# TODO: Review unreachable code - "--populate-test-data", action="store_true", help="Populate with test data (development only)"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Comparison - populate
# TODO: Review unreachable code - comparison_populate = comparison_subparsers.add_parser("populate", help="Populate with images")
# TODO: Review unreachable code - comparison_populate.add_argument("directory", help="Directory to scan")
# TODO: Review unreachable code - comparison_populate.add_argument("-r", "--recursive", action="store_true", help="Search recursively")
# TODO: Review unreachable code - comparison_populate.add_argument("-l", "--limit", type=int, help="Maximum number to add")

# TODO: Review unreachable code - # Comparison - populate-default
# TODO: Review unreachable code - comparison_populate_default = comparison_subparsers.add_parser("populate-default", help="Populate from default dirs")
# TODO: Review unreachable code - comparison_populate_default.add_argument("-l", "--limit", type=int, help="Maximum number to add")

# TODO: Review unreachable code - # Comparison - stats
# TODO: Review unreachable code - comparison_subparsers.add_parser("stats", help="Show model rankings")

# TODO: Review unreachable code - # Comparison - reset
# TODO: Review unreachable code - comparison_subparsers.add_parser("reset", help="Reset all comparison data")


# TODO: Review unreachable code - def add_transitions_subcommand(subparsers) -> None:
# TODO: Review unreachable code - """Add transitions subcommand."""
# TODO: Review unreachable code - transitions_parser = subparsers.add_parser("transitions", help="Analyze scene transitions")
# TODO: Review unreachable code - transitions_subparsers = transitions_parser.add_subparsers(
# TODO: Review unreachable code - dest="transitions_command", help="Transition analysis commands"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - # Transitions - analyze
# TODO: Review unreachable code - transitions_analyze = transitions_subparsers.add_parser("analyze", help="Analyze transitions between images")
# TODO: Review unreachable code - transitions_analyze.add_argument("images", nargs="+", help="Image files to analyze (in sequence order)")
# TODO: Review unreachable code - transitions_analyze.add_argument("-o", "--output", help="Output JSON file for results")
# TODO: Review unreachable code - transitions_analyze.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

# TODO: Review unreachable code - # Transitions - motion
# TODO: Review unreachable code - transitions_motion = transitions_subparsers.add_parser("motion", help="Analyze motion in a single image")
# TODO: Review unreachable code - transitions_motion.add_argument("image", help="Image file to analyze")
# TODO: Review unreachable code - transitions_motion.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
