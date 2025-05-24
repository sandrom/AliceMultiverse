"""
Media Organizer Runner

Entry point for executing media organization with support for different organizer
variants (standard vs enhanced metadata) and pipeline configurations. Handles
configuration updates and API key management.
"""

import logging
from typing import Optional
from pathlib import Path

from omegaconf import DictConfig

from .media_organizer import MediaOrganizer
from .enhanced_organizer import EnhancedMediaOrganizer

logger = logging.getLogger(__name__)


def run_organizer(config: DictConfig, 
                  pipeline: Optional[str] = None,
                  stages: Optional[str] = None,
                  cost_limit: Optional[float] = None,
                  sightengine_key: Optional[str] = None,
                  claude_key: Optional[str] = None) -> bool:
    """Run the media organizer.
    
    Args:
        config: Configuration object
        pipeline: Pipeline mode (basic, standard, premium, custom)
        stages: Custom pipeline stages (comma-separated)
        cost_limit: Maximum cost limit for pipeline processing
        sightengine_key: SightEngine API credentials (format: 'user,secret')
        claude_key: Anthropic/Claude API key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Update config with pipeline settings if provided
        if pipeline:
            config.processing.pipeline = pipeline
        if cost_limit is not None:
            if not hasattr(config, 'pipeline'):
                config.pipeline = {}
            config.pipeline.cost_limit = cost_limit
        
        # Set API keys in config if provided
        if sightengine_key:
            user, secret = sightengine_key.split(',', 1)
            config.processing.sightengine_user = user
            config.processing.sightengine_secret = secret
        if claude_key:
            config.processing.claude_api_key = claude_key
            
        # Create organizer - use enhanced if requested
        if config.get('enhanced_metadata', False):
            organizer = EnhancedMediaOrganizer(config)
            logger.info("Using enhanced metadata organizer")
        else:
            organizer = MediaOrganizer(config)
            if pipeline:
                logger.info(f"Using pipeline mode: {pipeline}")
        
        return organizer.organize()
        
    except KeyboardInterrupt:
        # Let KeyboardInterrupt propagate to CLI for proper exit code
        raise
    except Exception as e:
        logger.error(f"Organizer failed: {e}")
        return False