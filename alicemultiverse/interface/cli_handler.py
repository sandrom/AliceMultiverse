"""CLI handler for the Alice interface command."""

import json
import logging
from argparse import Namespace
from pathlib import Path
from typing import Dict, Any

from ..core.logging import setup_logging
from .alice_interface import AliceInterface
from .models import SearchRequest, OrganizeRequest, TagRequest
from ..metadata.models import AssetRole

logger = logging.getLogger(__name__)


def run_interface_command(args: Namespace) -> int:
    """Handle the interface subcommand.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    # Setup logging
    setup_logging(level="INFO")
    
    if args.demo:
        return run_demo()
    else:
        # Interactive mode could be added here later
        logger.info("Alice Interface")
        logger.info("==============")
        logger.info("")
        logger.info("The Alice interface provides structured functions for AI assistants to interact with the media organization system.")
        logger.info("")
        logger.info("Run with --demo to see example AI interactions.")
        logger.info("")
        logger.info("In practice, AI assistants would call these functions programmatically:")
        logger.info("  - search_assets: Find assets by tags, description, or metadata")
        logger.info("  - organize_media: Process and organize media files")
        logger.info("  - tag_assets: Add semantic tags to assets")
        logger.info("  - get_asset_info: Get detailed metadata for an asset")
        logger.info("  - find_similar_assets: Find visually or conceptually similar assets")
        logger.info("  - assess_quality: Run quality assessment on assets")
        return 0


def run_demo() -> int:
    """Run a demonstration of AI interaction with Alice."""
    logger.info("Alice Interface Demo")
    logger.info("===================")
    logger.info("")
    logger.info("This demo shows how an AI assistant would interact with Alice.")
    logger.info("")
    
    # Initialize interface
    alice = AliceInterface()
    
    # Demo 1: Search for cyberpunk portraits
    logger.info("1. AI Assistant: 'Find cyberpunk style portraits'")
    request = SearchRequest(
        style_tags=["cyberpunk"],
        subject_tags=["portrait"],
        limit=5
    )
    response = alice.search_assets(request)
    _print_response("Search Results", response)
    
    # Demo 2: Organize new media
    logger.info("\n2. AI Assistant: 'Organize the files in my downloads folder'")
    request = OrganizeRequest(
        source_path="~/Downloads",
        quality_assessment=True,
        enhanced_metadata=True
    )
    response = alice.organize_media(request)
    _print_response("Organization Results", response)
    
    # Demo 3: Tag assets
    logger.info("\n3. AI Assistant: 'Tag these assets as hero shots for the cyberpunk project'")
    if response.get('data') and 'processed_files' in response['data']:
        # Get first few processed assets
        asset_ids = [f['asset_id'] for f in response['data']['processed_files'][:3] 
                     if 'asset_id' in f]
        if asset_ids:
            request = TagRequest(
                asset_ids=asset_ids,
                style_tags=["hero-shot"],
                role=AssetRole.HERO
            )
            response = alice.tag_assets(request)
            _print_response("Tagging Results", response)
    
    # Demo 4: Find similar assets
    logger.info("\n4. AI Assistant: 'Find more images like this one'")
    # In a real scenario, the AI would have an asset_id from previous interactions
    logger.info("   (Searching for similar assets to a reference image)")
    # This would normally use a real asset_id
    response = alice.find_similar_assets("example_asset_id", threshold=0.8)
    _print_response("Similar Assets", response)
    
    # Demo 5: Natural language search
    logger.info("\n5. AI Assistant: 'Show me dark moody landscapes from last week'")
    request = SearchRequest(
        description="dark moody landscapes from last week"
    )
    response = alice.search_assets(request)
    _print_response("Natural Language Search", response)
    
    logger.info("\n" + "="*60)
    logger.info("Demo complete!")
    logger.info("")
    logger.info("In a real AI integration, these function calls would be made")
    logger.info("programmatically by the AI assistant based on user requests.")
    logger.info("")
    logger.info("The AI never sees file paths or technical details - it works")
    logger.info("purely with creative concepts and asset IDs.")
    
    return 0


def _print_response(title: str, response: Any) -> None:
    """Pretty print an Alice response."""
    logger.info(f"\n   Alice Response - {title}:")
    logger.info(f"   Success: {response.get('success', False)}")
    
    if 'message' in response:
        logger.info(f"   Message: {response['message']}")
    
    if 'data' in response and response['data']:
        # Format the data nicely
        formatted = json.dumps(response['data'], indent=4)
        for line in formatted.split('\n'):
            logger.info(f"   {line}")
    
    if 'error' in response and response['error']:
        logger.error(f"   Error: {response['error']}")