"""Configuration management implementation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel


class ServiceConfig(BaseModel):
    """Base configuration for a service."""
    host: str = "0.0.0.0"
    port: int = 8000
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"


class Config:
    """Configuration manager for AliceMultiverse."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize with configuration dictionary."""
        self._config = OmegaConf.create(config_dict)
        OmegaConf.set_struct(self._config, False)  # Allow adding new keys
        
        # Merge with environment variables
        env_config = OmegaConf.from_dotlist(self._get_env_vars())
        self._config = OmegaConf.merge(self._config, env_config)
    
    def _get_env_vars(self) -> list:
        """Get environment variables with ALICE_ prefix."""
        env_vars = []
        for key, value in os.environ.items():
            if key.startswith("ALICE_"):
                # Convert ALICE_PATHS__INBOX to paths.inbox
                config_key = key[6:].lower().replace("__", ".")
                env_vars.append(f"{config_key}={value}")
        return env_vars
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return OmegaConf.select(self._config, key, default=default)
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to config values."""
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._config[name]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return OmegaConf.to_container(self._config, resolve=True)


# Global configuration instance
_config: Optional[Config] = None


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file."""
    global _config
    
    if config_path is None:
        # Look for config in standard locations
        locations = [
            Path("config.yaml"),
            Path("settings.yaml"),
            Path.home() / ".alicemultiverse" / "config.yaml",
        ]
        for loc in locations:
            if loc.exists():
                config_path = loc
                break
    
    if config_path and config_path.exists():
        config_dict = OmegaConf.to_container(OmegaConf.load(config_path))
    else:
        # Default configuration
        config_dict = {
            "paths": {
                "inbox": "./inbox",
                "organized": "./organized"
            },
            "services": {
                "alice_interface": {"port": 8000},
                "asset_processor": {"port": 8001},
                "quality_analyzer": {"port": 8002},
                "metadata_extractor": {"port": 8003}
            },
            "features": {
                "quality_assessment": True,
                "event_persistence": True
            }
        }
    
    _config = Config(config_dict)
    return _config


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config