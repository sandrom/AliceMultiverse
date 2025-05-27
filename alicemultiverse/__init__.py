"""
AliceMultiverse - AI Assistant Interface & Creative Workflow Hub

An extensible interface connecting AI assistants (Claude, ChatGPT) with local 
development environments and creative tools. Provides media organization, 
workflow automation, and project management capabilities.
"""

__version__ = "2.0.0"
__author__ = "AliceMultiverse Contributors"
__email__ = "contact@alicemultiverse.ai"

from .core.config import load_config
from .organizer.media_organizer import MediaOrganizer

__all__ = [
    "load_config",
    "MediaOrganizer",
]