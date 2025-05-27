"""Configuration management for AliceMultiverse.

This module now uses the dataclass-based configuration.
For backward compatibility, it re-exports from config_dataclass.
"""

# Re-export from the dataclass implementation
from .config_dataclass import (
    Config as DictConfig,  # Alias for backward compatibility
)
from .config_dataclass import (
    get_default_config,
    load_config,
)

__all__ = ["DictConfig", "get_default_config", "load_config"]
