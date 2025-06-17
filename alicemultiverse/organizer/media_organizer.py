"""Media organizer - Compatibility layer for the refactored modular organizer.

This module maintains backward compatibility while the implementation
has been refactored into modular components in the components/ directory.
"""

from .components.organizer import MediaOrganizer

__all__ = ["MediaOrganizer"]
