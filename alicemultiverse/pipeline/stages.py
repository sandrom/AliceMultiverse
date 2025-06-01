"""Pipeline stages for media analysis."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..core.types import MediaType

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """Abstract base class for pipeline stages."""

    @abstractmethod
    def name(self) -> str:
        """Return the name of this stage."""
        pass

    @abstractmethod
    def process(self, image_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process an image through this stage.

        Args:
            image_path: Path to the image
            metadata: Current metadata for the image

        Returns:
            Updated metadata with stage results
        """
        pass

    @abstractmethod
    def should_process(self, metadata: dict[str, Any]) -> bool:
        """Check if this stage should process the image.

        Args:
            metadata: Current metadata for the image

        Returns:
            True if the stage should process this image
        """
        pass

    @abstractmethod
    def get_cost(self) -> float:
        """Get the cost per image for this stage."""
        pass


# Quality assessment stages have been replaced with image understanding stages
# See alicemultiverse.understanding.pipeline_stages for new functionality




