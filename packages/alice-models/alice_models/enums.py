"""Enumerations used across AliceMultiverse."""

from enum import Enum, IntEnum


class MediaType(str, Enum):
    """Types of media files."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class QualityRating(IntEnum):
    """Star rating for quality assessment."""

    ONE_STAR = 1
    TWO_STAR = 2
    THREE_STAR = 3
    FOUR_STAR = 4
    FIVE_STAR = 5


class WorkflowState(str, Enum):
    """States of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStatus(str, Enum):
    """Status of asset processing."""

    UNPROCESSED = "unprocessed"
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SourceType(str, Enum):
    """AI generation sources."""

    STABLE_DIFFUSION = "stable-diffusion"
    MIDJOURNEY = "midjourney"
    DALLE = "dalle"
    CLAUDE = "claude"
    COMFYUI = "comfyui"
    AUTOMATIC1111 = "automatic1111"
    LEONARDO = "leonardo"
    PLAYGROUND = "playground"
    IDEOGRAM = "ideogram"
    FLUX = "flux"
    UNKNOWN = "unknown"
