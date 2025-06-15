"""Built-in workflow templates for common AI pipelines."""

from .image_enhancement import ImageEnhancementWorkflow
from .music_video import CinematicMusicVideoTemplate, MusicVideoTemplate, QuickMusicVideoTemplate
from .social_media import (
    InstagramReelTemplate,
    LinkedInVideoTemplate,
    PlatformSpec,
    SocialMediaTemplate,
    SocialPlatform,
    TikTokTemplate,
)
from .story_arc import (
    DocumentaryStoryTemplate,
    EmotionalJourneyTemplate,
    StoryArcTemplate,
    StoryStructure,
)
from .style_transfer import StyleTransferWorkflow
from .video_pipeline import VideoProductionWorkflow

__all__ = [
    "CinematicMusicVideoTemplate",
    "DocumentaryStoryTemplate",
    "EmotionalJourneyTemplate",
    "ImageEnhancementWorkflow",
    "InstagramReelTemplate",
    "LinkedInVideoTemplate",
    "MusicVideoTemplate",
    "PlatformSpec",
    "QuickMusicVideoTemplate",
    "SocialMediaTemplate",
    "SocialPlatform",
    "StoryArcTemplate",
    "StoryStructure",
    "StyleTransferWorkflow",
    "TikTokTemplate",
    "VideoProductionWorkflow",
]
