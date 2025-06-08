"""Plugin configuration manager for loading and saving plugin configs."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import json

logger = logging.getLogger(__name__)


class PluginConfigManager:
    """Manages plugin configuration files."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config manager.
        
        Args:
            config_dir: Directory to store plugin configs
        """
        self.config_dir = config_dir or Path.home() / ".alice" / "plugins" / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Load configuration for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration dict
        """
        # Try YAML first, then JSON
        yaml_path = self.config_dir / f"{plugin_name}.yaml"
        json_path = self.config_dir / f"{plugin_name}.json"
        
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                logger.info(f"Loaded config for {plugin_name} from {yaml_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading YAML config: {e}")
        
        if json_path.exists():
            try:
                with open(json_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded config for {plugin_name} from {json_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading JSON config: {e}")
        
        # No config file found
        logger.debug(f"No config file found for {plugin_name}")
        return {}
    
    def save_config(self, plugin_name: str, config: Dict[str, Any], format: str = "yaml"):
        """
        Save configuration for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: Configuration dict
            format: File format ("yaml" or "json")
        """
        if format == "yaml":
            config_path = self.config_dir / f"{plugin_name}.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
        else:
            config_path = self.config_dir / f"{plugin_name}.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        logger.info(f"Saved config for {plugin_name} to {config_path}")
    
    def delete_config(self, plugin_name: str):
        """Delete configuration for a plugin."""
        yaml_path = self.config_dir / f"{plugin_name}.yaml"
        json_path = self.config_dir / f"{plugin_name}.json"
        
        if yaml_path.exists():
            yaml_path.unlink()
            logger.info(f"Deleted config file: {yaml_path}")
        
        if json_path.exists():
            json_path.unlink()
            logger.info(f"Deleted config file: {json_path}")
    
    def list_configs(self) -> Dict[str, Path]:
        """
        List all plugin configuration files.
        
        Returns:
            Dict mapping plugin names to config file paths
        """
        configs = {}
        
        # Find all YAML and JSON files
        for pattern in ["*.yaml", "*.json"]:
            for config_file in self.config_dir.glob(pattern):
                plugin_name = config_file.stem
                # Prefer YAML over JSON if both exist
                if plugin_name not in configs or config_file.suffix == ".yaml":
                    configs[plugin_name] = config_file
        
        return configs
    
    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration against schema.
        
        Args:
            config: Configuration to validate
            schema: Schema definition
            
        Returns:
            True if valid, False otherwise
        """
        for key, spec in schema.items():
            if spec.get("required", False) and key not in config:
                logger.error(f"Missing required config key: {key}")
                return False
            
            if key in config:
                value = config[key]
                
                # Check type
                expected_type = spec.get("type")
                if expected_type:
                    type_map = {
                        "string": str,
                        "integer": int,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict
                    }
                    expected = type_map.get(expected_type)
                    if expected and not isinstance(value, expected):
                        logger.error(f"Invalid type for {key}: expected {expected_type}, got {type(value).__name__}")
                        return False
                
                # Check enum values
                if "enum" in spec and value not in spec["enum"]:
                    logger.error(f"Invalid value for {key}: {value} not in {spec['enum']}")
                    return False
                
                # Check numeric constraints
                if isinstance(value, (int, float)):
                    if "minimum" in spec and value < spec["minimum"]:
                        logger.error(f"Value for {key} below minimum: {value} < {spec['minimum']}")
                        return False
                    if "maximum" in spec and value > spec["maximum"]:
                        logger.error(f"Value for {key} above maximum: {value} > {spec['maximum']}")
                        return False
        
        return True
    
    def get_default_config(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate default configuration from schema.
        
        Args:
            schema: Schema definition
            
        Returns:
            Default configuration dict
        """
        config = {}
        
        for key, spec in schema.items():
            if "default" in spec:
                config[key] = spec["default"]
            elif spec.get("required", False):
                # Provide sensible defaults for required fields
                type_defaults = {
                    "string": "",
                    "integer": 0,
                    "number": 0.0,
                    "boolean": False,
                    "array": [],
                    "object": {}
                }
                config[key] = type_defaults.get(spec.get("type"), None)
        
        return config