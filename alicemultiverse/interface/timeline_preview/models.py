"""Data models for timeline preview interface."""

from pydantic import BaseModel


class TimelinePreviewRequest(BaseModel):
    """Request to preview a timeline."""
    timeline_id: str
    format: str = "web"  # web, edl, xml, capcut


class TimelineUpdateRequest(BaseModel):
    """Request to update timeline."""
    timeline_id: str
    clips: list[dict]  # List of clip updates
    operation: str  # reorder, trim, add_transition, etc.