"""Plugin loader for discovering and loading plugins."""

import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import Plugin, PluginType

logger = logging.getLogger(__name__)


class PluginLoader:
    """Loads plugins from various sources."""
    
    def __init__(self):
        """Initialize plugin loader."""
        self.loaded_plugins: Dict[str, Plugin] = {}
        self.plugin_paths: List[Path] = []
    
    def add_plugin_path(self, path: Path):
        """Add a directory to search for plugins."""
        if path.exists() and path.is_dir():
            self.plugin_paths.append(path)
            # Add to Python path for imports
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
        else:
            logger.warning(f"Plugin path does not exist: {path}")
    
    def load_plugin_from_file(self, file_path: Path) -> Optional[Plugin]:
        """
        Load a plugin from a Python file.
        
        Args:
            file_path: Path to plugin file
            
        Returns:
            Loaded plugin instance or None
        """
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location(
                f"plugin_{file_path.stem}",
                file_path
            )
            if spec is None or spec.loader is None:
                logger.error(f"Could not load spec for {file_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Find plugin classes
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin and
                    not inspect.isabstract(obj)):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                logger.warning(f"No plugin class found in {file_path}")
                return None
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            logger.info(f"Loaded plugin: {plugin_instance.metadata.name} v{plugin_instance.metadata.version}")
            
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {e}")
            return None
    
    def load_plugin_from_module(self, module_name: str) -> Optional[Plugin]:
        """
        Load a plugin from an installed module.
        
        Args:
            module_name: Module name (e.g., 'alice_plugin_example')
            
        Returns:
            Loaded plugin instance or None
        """
        try:
            # Import module
            module = importlib.import_module(module_name)
            
            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin and
                    not inspect.isabstract(obj)):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                logger.warning(f"No plugin class found in module {module_name}")
                return None
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            logger.info(f"Loaded plugin: {plugin_instance.metadata.name} v{plugin_instance.metadata.version}")
            
            return plugin_instance
            
        except ImportError as e:
            logger.error(f"Could not import module {module_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading plugin from module {module_name}: {e}")
            return None
    
    def discover_plugins(self) -> List[Plugin]:
        """
        Discover all plugins in plugin paths.
        
        Returns:
            List of discovered plugins
        """
        discovered = []
        
        for plugin_path in self.plugin_paths:
            # Look for Python files
            for file_path in plugin_path.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue
                
                plugin = self.load_plugin_from_file(file_path)
                if plugin:
                    discovered.append(plugin)
            
            # Look for plugin packages (directories with __init__.py)
            for dir_path in plugin_path.iterdir():
                if dir_path.is_dir() and (dir_path / "__init__.py").exists():
                    plugin_file = dir_path / "plugin.py"
                    if plugin_file.exists():
                        plugin = self.load_plugin_from_file(plugin_file)
                        if plugin:
                            discovered.append(plugin)
        
        return discovered
    
    def load_builtin_plugins(self) -> List[Plugin]:
        """
        Load built-in plugins.
        
        Returns:
            List of built-in plugins
        """
        builtin_modules = [
            "alicemultiverse.plugins.builtin.upscale_effect",
            "alicemultiverse.plugins.builtin.style_transfer_effect",
            "alicemultiverse.plugins.builtin.csv_exporter",
            "alicemultiverse.plugins.builtin.markdown_exporter"
        ]
        
        plugins = []
        for module_name in builtin_modules:
            plugin = self.load_plugin_from_module(module_name)
            if plugin:
                plugins.append(plugin)
        
        return plugins
    
    def load_all_plugins(self, include_builtin: bool = True) -> Dict[str, Plugin]:
        """
        Load all available plugins.
        
        Args:
            include_builtin: Whether to include built-in plugins
            
        Returns:
            Dictionary of plugin_name -> plugin_instance
        """
        all_plugins = {}
        
        # Load built-in plugins
        if include_builtin:
            for plugin in self.load_builtin_plugins():
                all_plugins[plugin.metadata.name] = plugin
        
        # Discover and load external plugins
        for plugin in self.discover_plugins():
            # External plugins can override built-in ones
            all_plugins[plugin.metadata.name] = plugin
        
        self.loaded_plugins = all_plugins
        return all_plugins
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """
        Get all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugins of the specified type
        """
        return [
            plugin for plugin in self.loaded_plugins.values()
            if plugin.metadata.type == plugin_type
        ]
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        Get a specific plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None
        """
        return self.loaded_plugins.get(name)