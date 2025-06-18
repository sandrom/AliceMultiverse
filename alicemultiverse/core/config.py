"""Configuration management for AliceMultiverse.

This module now uses the dataclass-based configuration.
For backward compatibility, it re-exports from config_dataclass.
"""

from pathlib import Path

# Re-export from the dataclass implementation
from .config_dataclass import (
    Config,
    Config as DictConfig,  # Alias for backward compatibility
    get_default_config,
    load_config,
)

# Load settings from the default location
_settings_path = Path(__file__).parent.parent.parent / "settings.yaml"
settings = load_config(_settings_path) if _settings_path.exists() else get_default_config()

__all__ = ["Config", "DictConfig", "get_default_config", "load_config", "settings"]
