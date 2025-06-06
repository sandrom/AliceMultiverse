"""Built-in workflow templates for common AI pipelines."""

from .image_enhancement import ImageEnhancementWorkflow
from .video_pipeline import VideoProductionWorkflow
from .style_transfer import StyleTransferWorkflow
from .music_video import (
    MusicVideoTemplate,
    QuickMusicVideoTemplate,
    CinematicMusicVideoTemplate
)

__all__ = [
    "ImageEnhancementWorkflow",
    "VideoProductionWorkflow", 
    "StyleTransferWorkflow",
    "MusicVideoTemplate",
    "QuickMusicVideoTemplate",
    "CinematicMusicVideoTemplate",
]