"""
AliceMultiverse - AI Media Organization System

A comprehensive media organization system for AI-generated content with 
intelligent quality assessment and automated sorting.
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