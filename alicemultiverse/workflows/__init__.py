"""Multi-modal workflow support for AliceMultiverse.

This module provides workflow templates for chaining AI operations like:
- Image generation → upscaling → variation
- Video generation → audio addition → enhancement
- Style transfer pipelines
- Multi-provider optimization
"""

# Re-export submodules for backward compatibility
from . import composition, transitions, variations
from .base import (
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTemplate,
)
from .executor import WorkflowExecutor

# Registry removed - import workflows directly instead
from .video_creation import (
    CameraMotion,
    ShotDescription,
    TransitionType,
    VideoCreationWorkflow,
    VideoStoryboard,
)

__all__ = [
    # Base classes
    "WorkflowTemplate",
    "WorkflowStep",
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowStatus",
    # Executor
    "WorkflowExecutor",
    # Registry removed - use direct imports
    # Video creation
    "VideoCreationWorkflow",
    "VideoStoryboard",
    "ShotDescription",
    "CameraMotion",
    "TransitionType",
    # Submodules
    "composition",
    "transitions",
    "variations",
]
