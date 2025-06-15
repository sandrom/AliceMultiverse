"""Command registry for debug CLI commands.

This module registers all the sub-commands for debugging purposes.
Production usage should be through AI assistants (MCP server).
"""

import argparse


def register_debug_commands(parser: argparse.ArgumentParser) -> None:
    """Register all debug commands to the parser.
    
    Args:
        parser: The main argument parser
    """
    # Create debug subparser
    debug_parser = parser.add_subparsers(dest="debug_command", help="Debug commands")
    
    # Deduplication commands
    try:
        from ..assets.deduplication.cli import register_dedup_commands
        dedup_parser = debug_parser.add_parser("dedup", help="Deduplication and similarity search")
        register_dedup_commands(dedup_parser)
    except ImportError:
        pass
    
    # Comparison commands
    try:
        from ..comparison.cli import register_comparison_commands
        comparison_parser = debug_parser.add_parser("compare", help="Model comparison system")
        register_comparison_commands(comparison_parser)
    except ImportError:
        pass
    
    # Prompts commands
    try:
        from ..prompts.cli import prompts_cli
        debug_parser.add_parser("prompts", help="Prompt management")
        # Convert Click commands to argparse
        # This is complex - for now just note it exists
    except ImportError:
        pass
    
    # Scene detection commands
    try:
        from ..scene_detection.cli import register_scene_commands
        scene_parser = debug_parser.add_parser("scenes", help="Scene detection and analysis")
        register_scene_commands(scene_parser)
    except ImportError:
        pass
    
    # Storage commands
    try:
        from ..storage.cli import register_storage_commands
        storage_parser = debug_parser.add_parser("storage", help="Multi-location storage management")
        register_storage_commands(storage_parser)
    except ImportError:
        pass
    
    # Transitions commands
    try:
        from ..workflows.transitions.cli import register_transition_commands
        transitions_parser = debug_parser.add_parser("transitions", help="Video transition analysis")
        register_transition_commands(transitions_parser)
    except ImportError:
        pass


def list_available_commands() -> list[str]:
    """List all available debug commands.
    
    Returns:
        List of command names
    """
    commands = []
    
    # Check which modules are available
    try:
        import alicemultiverse.assets.deduplication.cli
        commands.append("dedup")
    except ImportError:
        pass
    
    try:
        import alicemultiverse.comparison.cli
        commands.append("compare")
    except ImportError:
        pass
    
    try:
        import alicemultiverse.prompts.cli
        commands.append("prompts")
    except ImportError:
        pass
    
    try:
        import alicemultiverse.scene_detection.cli
        commands.append("scenes")
    except ImportError:
        pass
    
    try:
        import alicemultiverse.storage.cli
        commands.append("storage")
    except ImportError:
        pass
    
    try:
        import alicemultiverse.workflows.transitions.cli
        commands.append("transitions")
    except ImportError:
        pass
    
    return commands