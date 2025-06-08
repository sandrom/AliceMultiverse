"""Built-in workflow templates for common AI pipelines."""

from .image_enhancement import ImageEnhancementWorkflow
from .video_pipeline import VideoProductionWorkflow
from .style_transfer import StyleTransferWorkflow
from .music_video import (
    MusicVideoTemplate,
    QuickMusicVideoTemplate,
    CinematicMusicVideoTemplate
)
from .story_arc import (
    StoryArcTemplate,
    DocumentaryStoryTemplate,
    EmotionalJourneyTemplate,
    StoryStructure
)
from .social_media import (
    SocialMediaTemplate,
    InstagramReelTemplate,
    TikTokTemplate,
    LinkedInVideoTemplate,
    SocialPlatform,
    PlatformSpec
)

__all__ = [
    "ImageEnhancementWorkflow",
    "VideoProductionWorkflow", 
    "StyleTransferWorkflow",
    "MusicVideoTemplate",
    "QuickMusicVideoTemplate",
    "CinematicMusicVideoTemplate",
    "StoryArcTemplate",
    "DocumentaryStoryTemplate",
    "EmotionalJourneyTemplate",
    "StoryStructure",
    "SocialMediaTemplate",
    "InstagramReelTemplate",
    "TikTokTemplate",
    "LinkedInVideoTemplate",
    "SocialPlatform",
    "PlatformSpec",
]