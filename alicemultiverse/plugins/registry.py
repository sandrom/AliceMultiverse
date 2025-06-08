"""Plugin registry for managing loaded plugins."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import get_config
from .base import Plugin, PluginType
from .loader import PluginLoader

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for all plugins."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize registry (only once due to singleton)."""
        if not self._initialized:
            self.loader = PluginLoader()
            self.plugins: Dict[str, Plugin] = {}
            self.initialized_plugins: Dict[str, bool] = {}
            self._initialized = True
    
    async def initialize(self):
        """Initialize the plugin system."""
        # Add default plugin paths
        self._add_default_paths()
        
        # Load all plugins
        self.plugins = self.loader.load_all_plugins()
        
        # Initialize all plugins
        for name, plugin in self.plugins.items():
            try:
                success = await plugin.initialize()
                self.initialized_plugins[name] = success
                if success:
                    logger.info(f"Initialized plugin: {name}")
                else:
                    logger.warning(f"Failed to initialize plugin: {name}")
            except Exception as e:
                logger.error(f"Error initializing plugin {name}: {e}")
                self.initialized_plugins[name] = False
    
    def _add_default_paths(self):
        """Add default plugin search paths."""
        # User plugins directory
        user_plugins = Path.home() / ".alice" / "plugins"
        user_plugins.mkdir(parents=True, exist_ok=True)
        self.loader.add_plugin_path(user_plugins)
        
        # System plugins directory
        system_plugins = Path(__file__).parent / "builtin"
        if system_plugins.exists():
            self.loader.add_plugin_path(system_plugins)
        
        # Config-specified paths
        config = get_config()
        if config.get("plugins", {}).get("paths"):
            for path_str in config.plugins.paths:
                path = Path(path_str).expanduser()
                if path.exists():
                    self.loader.add_plugin_path(path)
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        Get an initialized plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance if found and initialized, None otherwise
        """
        if name in self.plugins and self.initialized_plugins.get(name, False):
            return self.plugins[name]
        return None
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """
        Get all initialized plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of initialized plugins of the specified type
        """
        return [
            plugin for name, plugin in self.plugins.items()
            if plugin.metadata.type == plugin_type 
            and self.initialized_plugins.get(name, False)
        ]
    
    def register_plugin(self, plugin: Plugin, initialize: bool = True) -> bool:
        """
        Register a plugin at runtime.
        
        Args:
            plugin: Plugin instance to register
            initialize: Whether to initialize the plugin
            
        Returns:
            True if registration successful
        """
        try:
            name = plugin.metadata.name
            
            # Check for conflicts
            if name in self.plugins:
                logger.warning(f"Overriding existing plugin: {name}")
            
            # Register plugin
            self.plugins[name] = plugin
            
            # Initialize if requested
            if initialize:
                success = asyncio.run(plugin.initialize())
                self.initialized_plugins[name] = success
                return success
            else:
                self.initialized_plugins[name] = False
                return True
                
        except Exception as e:
            logger.error(f"Error registering plugin: {e}")
            return False
    
    def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if unregistration successful
        """
        if name not in self.plugins:
            return False
        
        try:
            # Cleanup if initialized
            if self.initialized_plugins.get(name, False):
                asyncio.run(self.plugins[name].cleanup())
            
            # Remove from registry
            del self.plugins[name]
            del self.initialized_plugins[name]
            
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering plugin {name}: {e}")
            return False
    
    async def cleanup(self):
        """Clean up all plugins."""
        for name, plugin in self.plugins.items():
            if self.initialized_plugins.get(name, False):
                try:
                    await plugin.cleanup()
                    logger.info(f"Cleaned up plugin: {name}")
                except Exception as e:
                    logger.error(f"Error cleaning up plugin {name}: {e}")
    
    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        info = []
        for name, plugin in self.plugins.items():
            metadata = plugin.metadata
            info.append({
                "name": name,
                "version": metadata.version,
                "type": metadata.type.value,
                "description": metadata.description,
                "author": metadata.author,
                "initialized": self.initialized_plugins.get(name, False),
                "dependencies": metadata.dependencies
            })
        return info


# Convenience functions
_registry = None


def get_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


async def initialize_plugins():
    """Initialize the plugin system."""
    registry = get_registry()
    await registry.initialize()


def get_plugin(name: str) -> Optional[Plugin]:
    """Get a plugin by name."""
    registry = get_registry()
    return registry.get_plugin(name)


def get_plugins_by_type(plugin_type: PluginType) -> List[Plugin]:
    """Get all plugins of a specific type."""
    registry = get_registry()
    return registry.get_plugins_by_type(plugin_type)