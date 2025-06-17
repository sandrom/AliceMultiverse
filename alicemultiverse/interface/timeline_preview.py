"""Timeline preview interface - Compatibility layer for the refactored modular interface.

This module maintains backward compatibility while the implementation
has been refactored into modular components in the timeline_preview/ directory.
"""

from .timeline_preview import (
    PreviewSession,
    TimelinePreviewRequest,
    TimelinePreviewServer,
    TimelineUpdateRequest,
    create_preview_server,
)

__all__ = [
    "TimelinePreviewRequest",
    "TimelineUpdateRequest",
    "PreviewSession",
    "TimelinePreviewServer",
    "create_preview_server",
]
