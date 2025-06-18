"""Main video creation workflow class."""

import logging
from typing import Any

from ...storage.unified_duckdb import DuckDBSearch
from .analysis import AnalysisMixin
from .export import ExportMixin
from .kling_integration import KlingIntegrationMixin
from .prompt_generation import PromptGenerationMixin

logger = logging.getLogger(__name__)


class VideoCreationWorkflow(
    AnalysisMixin,
    PromptGenerationMixin,
    KlingIntegrationMixin,
    ExportMixin
):
    """Workflow for creating videos from AI-generated images.

    This workflow helps create engaging video content by:
    1. Analyzing selected images to generate video prompts
    2. Suggesting camera movements and transitions
    3. Managing storyboards and shot lists
    4. Integrating with Kling for video generation
    5. Using Flux Kontext for keyframe preparation
    6. Exporting to DaVinci Resolve with timeline

    Example:
        ```python
        # Initialize workflow
        workflow = VideoCreationWorkflow(search_db)

        # Generate storyboard from images
        storyboard = await workflow.generate_video_prompts(
            image_hashes=["abc123", "def456", "ghi789"],
            style="cinematic",
            target_duration=30
        )

        # Create Kling requests
        kling_requests = workflow.create_kling_requests(storyboard)

        # After video generation, export to DaVinci
        timeline_path = workflow.export_to_davinci_resolve(
            storyboard,
            video_files={0: Path("shot1.mp4"), 1: Path("shot2.mp4")}
        )
        ```
    """

    def __init__(self, search_db: DuckDBSearch, understanding_provider: Any | None = None):
        """Initialize video creation workflow.

        Args:
            search_db: Database for searching assets
            understanding_provider: Optional AI provider for prompt enhancement
        """
        self.search_db = search_db
        self.understanding_provider = understanding_provider

        logger.info("VideoCreationWorkflow initialized")
