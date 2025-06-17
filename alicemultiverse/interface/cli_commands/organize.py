"""Media organization command arguments."""

import argparse


def add_organize_arguments(parser: argparse.ArgumentParser) -> None:
    """Add media organization arguments to the parser."""
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
