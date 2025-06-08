"""Plugin system for extending AliceMultiverse functionality."""

from .base import Plugin, PluginType, PluginMetadata
from .loader import PluginLoader
from .registry import PluginRegistry

__all__ = [
    "Plugin",
    "PluginType", 
    "PluginMetadata",
    "PluginLoader",
    "PluginRegistry"
]