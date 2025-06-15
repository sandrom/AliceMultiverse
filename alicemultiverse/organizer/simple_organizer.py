"""Simplified media organizer using direct function calls instead of pipeline."""

import asyncio
import logging
from pathlib import Path

from omegaconf import DictConfig

from ..core.types import MediaType, OrganizeResult
from ..understanding.simple_analysis import analyze_image, should_analyze_image
from .media_organizer import MediaOrganizer

logger = logging.getLogger(__name__)


class SimpleMediaOrganizer(MediaOrganizer):
    """Simplified media organizer that uses direct function calls."""
    
    def __init__(self, config: DictConfig):
        """Initialize simple organizer.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        
        # Disable pipeline
        self.pipeline_stages = None
        self.pipeline_enabled = False
        
        # Extract understanding config
        self.understanding_enabled = getattr(config.processing, "understanding", False)
        self.understanding_provider = None
        self.understanding_detailed = False
        
        if self.understanding_enabled:
            # Try to get understanding config from pipeline
            if hasattr(config, "pipeline") and hasattr(config.pipeline, "understanding"):
                understanding_config = config.pipeline.understanding
                self.understanding_provider = getattr(understanding_config, "preferred_provider", None)
                self.understanding_detailed = getattr(understanding_config, "detailed", False)
    
    def _analyze_file(self, media_path: Path) -> dict:
        """Analyze a single media file and return enhanced metadata.
        
        This replaces the complex pipeline system with a simple function call.
        
        Args:
            media_path: Path to media file
            
        Returns:
            Analysis result as dictionary
        """
        # Call parent to get basic analysis
        analysis = super()._analyze_file(media_path)
        
        # Skip if not an image or understanding is disabled
        if not self.understanding_enabled or analysis["media_type"] != MediaType.IMAGE:
            return analysis
            
        # Check if we should analyze
        metadata = {
            "media_type": analysis["media_type"],
            "understanding_provider": analysis.get("understanding_provider"),
        }
        
        if not should_analyze_image(metadata):
            return analysis
            
        try:
            # Run async analysis in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            understanding_result = loop.run_until_complete(
                analyze_image(
                    media_path,
                    provider=self.understanding_provider,
                    detailed=self.understanding_detailed,
                    extract_tags=True,
                    generate_prompt=True,
                )
            )
            
            # Merge understanding results into analysis
            if understanding_result:
                analysis.update(understanding_result)
                
                # Track cost
                if "understanding_cost" in understanding_result:
                    self.pipeline_cost_total += understanding_result["understanding_cost"]
                    
                logger.info(
                    f"Analyzed {media_path.name} with {understanding_result.get('understanding_provider')} "
                    f"(${understanding_result.get('understanding_cost', 0):.4f})"
                )
                
        except Exception as e:
            logger.error(f"Image understanding failed for {media_path.name}: {e}")
            
        finally:
            # Clean up event loop
            try:
                loop.close()
            except Exception:
                pass
                
        return analysis