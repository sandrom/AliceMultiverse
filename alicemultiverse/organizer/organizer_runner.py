"""
Media Organizer Runner

Entry point for executing media organization with support for different organizer
variants (standard vs enhanced metadata) and pipeline configurations. Handles
configuration updates and API key management.
"""

import logging

from omegaconf import DictConfig

from .enhanced_organizer import EnhancedMediaOrganizer

logger = logging.getLogger(__name__)


def run_organizer(
    config: DictConfig,
    pipeline: str | None = None,  # Deprecated - kept for compatibility
    stages: str | None = None,  # Deprecated
    cost_limit: float | None = None,
    sightengine_key: str | None = None,
    claude_key: str | None = None,
) -> bool:
    """Run the media organizer.

    Args:
        config: Configuration object
        pipeline: DEPRECATED - use understanding in config instead
        stages: DEPRECATED - pipeline stages no longer used
        cost_limit: Maximum cost limit for understanding
        sightengine_key: SightEngine API credentials (format: 'user,secret')
        claude_key: Anthropic/Claude API key

    Returns:
        True if successful, False otherwise
    """
    try:
        # Update config with understanding settings if provided
        if cost_limit is not None:
            if not hasattr(config, "understanding"):
                config.understanding = {}
            if not hasattr(config.understanding, "cost_limits"):
                config.understanding.cost_limits = {}
            config.understanding.cost_limits.total = cost_limit

        # Set API keys in config if provided
        if sightengine_key:
            user, secret = sightengine_key.split(",", 1)
            config.processing.sightengine_user = user
            config.processing.sightengine_secret = secret
        if claude_key:
            config.processing.claude_api_key = claude_key

        # Always use EnhancedMediaOrganizer (includes all functionality)
        organizer = EnhancedMediaOrganizer(config)
        if config.get("enhanced_metadata", False):
            logger.info("Enhanced metadata features enabled")
        
        # Note: Pipeline has been removed - use understanding flag instead

        return organizer.organize()

    except KeyboardInterrupt:
        # Let KeyboardInterrupt propagate to CLI for proper exit code
        raise
    except Exception as e:
        logger.error(f"Organizer failed: {e}")
        return False
