"""Video creation workflow - Compatibility layer for the refactored modular workflow.

This module maintains backward compatibility while the implementation
has been refactored into modular components in the video_creation/ directory.
"""

from .video_creation import (
    CameraMotion,
    DaVinciResolveTimeline,
    ShotDescription,
    TransitionType,
    VideoCreationWorkflow,
    VideoStoryboard,
)

__all__ = [
    "CameraMotion",
    "TransitionType",
    "ShotDescription",
    "VideoStoryboard",
    "DaVinciResolveTimeline",
    "VideoCreationWorkflow",
]
