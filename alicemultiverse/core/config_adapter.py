"""Adapter to transition from OmegaConf to dataclass config."""

import logging
from pathlib import Path
from typing import Any

# Try to import dataclass config first, fall back to OmegaConf
try:
    from .config_dataclass import Config, DictConfig
    from .config_dataclass import load_config as load_dataclass_config

    USE_DATACLASS = True
except ImportError:
    USE_DATACLASS = False

    from .config import DictConfig
    from .config import load_config as load_omegaconf_config

logger = logging.getLogger(__name__)


def load_config(config_path: Path | None = None, cli_overrides: list[str] | None = None) -> Any:
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
__all__ = ["DictConfig", "get_default_config", "load_config"]
