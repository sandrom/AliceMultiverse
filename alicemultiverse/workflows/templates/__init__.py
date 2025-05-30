"""Built-in workflow templates for common AI pipelines."""

from .image_enhancement import ImageEnhancementWorkflow
from .video_pipeline import VideoProductionWorkflow
from .style_transfer import StyleTransferWorkflow

__all__ = [
    "ImageEnhancementWorkflow",
    "VideoProductionWorkflow", 
    "StyleTransferWorkflow",
]