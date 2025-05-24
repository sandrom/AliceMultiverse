"""Adapter to transition from OmegaConf to dataclass config."""

from pathlib import Path
from typing import Optional, List, Any
import logging

# Try to import dataclass config first, fall back to OmegaConf
try:
    from .config_dataclass import Config, load_config as load_dataclass_config, DictConfig
    USE_DATACLASS = True
except ImportError:
    USE_DATACLASS = False
    from .config import load_config as load_omegaconf_config, DictConfig
    from omegaconf import OmegaConf

logger = logging.getLogger(__name__)


def load_config(
    config_path: Optional[Path] = None,
    cli_overrides: Optional[List[str]] = None
) -> Any:
    """Load configuration using either dataclass or OmegaConf.
    
    This adapter allows gradual migration from OmegaConf to dataclasses.
    """
    if USE_DATACLASS:
        return load_dataclass_config(config_path, cli_overrides)
    else:
        return load_omegaconf_config(config_path, cli_overrides)


def get_default_config() -> Any:
    """Get default configuration."""
    if USE_DATACLASS:
        from .config_dataclass import get_default_config
        return get_default_config()
    else:
        from .config import get_default_config
        return get_default_config()


# Export the appropriate DictConfig class
__all__ = ['load_config', 'get_default_config', 'DictConfig']