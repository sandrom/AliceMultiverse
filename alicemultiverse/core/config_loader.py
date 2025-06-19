"""Configuration loader with defaults and environment variable support."""

import os
from pathlib import Path
from typing import Any

from .utils import load_yaml, safe_get


class ConfigLoader:
    """Loads configuration with defaults and environment overrides."""

    def __init__(self, defaults_path: Path | None = None) -> None:
        """Initialize configuration loader.

        Args:
            defaults_path: Path to defaults.yaml file
        """
        if defaults_path is None:
            defaults_path = Path(__file__).parent / "defaults.yaml"

        self.defaults = load_yaml(defaults_path, default={})
        self._env_overrides = self._load_env_overrides()

    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            path: Dot-separated path (e.g., "providers.openai.base_url")
            default: Default value if not found

        Returns:
            Configuration value with environment overrides applied
        """
        # Check environment override first
        env_key = self._path_to_env_key(path)
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)

        # TODO: Review unreachable code - # Check loaded environment overrides
        # TODO: Review unreachable code - override_value = safe_get(self._env_overrides, path)
        # TODO: Review unreachable code - if override_value is not None:
        # TODO: Review unreachable code - return override_value

        # TODO: Review unreachable code - # Fall back to defaults
        # TODO: Review unreachable code - return safe_get(self.defaults, path, default)

    def get_provider_config(self, provider_name: str) -> dict[str, Any]:
        """Get all configuration for a provider.

        Args:
            provider_name: Provider name

        Returns:
            Provider configuration dictionary
        """
        base_config = self.defaults.get("providers", {}).get(provider_name, {})

        # Apply environment overrides
        env_prefix = f"ALICE_PROVIDER_{provider_name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                base_config[config_key] = self._parse_env_value(value)

        return base_config

    # TODO: Review unreachable code - def get_service_config(self, service_name: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """Get all configuration for a service.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - service_name: Service name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Service configuration dictionary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - base_config = self.defaults.get("services", {}).get(service_name, {})

    # TODO: Review unreachable code - # Apply environment overrides
    # TODO: Review unreachable code - env_prefix = f"ALICE_SERVICE_{service_name.upper()}_"
    # TODO: Review unreachable code - for key, value in os.environ.items():
    # TODO: Review unreachable code - if key.startswith(env_prefix):
    # TODO: Review unreachable code - config_key = key[len(env_prefix):].lower()
    # TODO: Review unreachable code - base_config[config_key] = self._parse_env_value(value)

    # TODO: Review unreachable code - return base_config

    # TODO: Review unreachable code - def _load_env_overrides(self) -> dict[str, Any]:
    # TODO: Review unreachable code - """Load all ALICE_ prefixed environment variables.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary of overrides organized by path
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - overrides = {}

    # TODO: Review unreachable code - for key, value in os.environ.items():
    # TODO: Review unreachable code - if key.startswith("ALICE_"):
    # TODO: Review unreachable code - # Convert ALICE_PROVIDERS_OPENAI_BASE_URL to providers.openai.base_url
    # TODO: Review unreachable code - path = self._env_key_to_path(key)
    # TODO: Review unreachable code - if path:
    # TODO: Review unreachable code - parsed_value = self._parse_env_value(value)
    # TODO: Review unreachable code - self._set_nested_value(overrides, path, parsed_value)

    # TODO: Review unreachable code - return overrides

    # TODO: Review unreachable code - def _path_to_env_key(self, path: str) -> str:
    # TODO: Review unreachable code - """Convert config path to environment variable name.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - path: Dot-separated path

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Environment variable name
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # providers.openai.base_url -> ALICE_PROVIDERS_OPENAI_BASE_URL
    # TODO: Review unreachable code - parts = path.split(".")
    # TODO: Review unreachable code - return "ALICE_" + "_".join(p.upper() for p in parts)

    # TODO: Review unreachable code - def _env_key_to_path(self, env_key: str) -> str | None:
    # TODO: Review unreachable code - """Convert environment variable name to config path.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - env_key: Environment variable name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dot-separated path or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not env_key.startswith("ALICE_"):
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # ALICE_PROVIDERS_OPENAI_BASE_URL -> providers.openai.base_url
    # TODO: Review unreachable code - parts = env_key[6:].lower().split("_")

    # TODO: Review unreachable code - # Handle special cases where underscore is part of the name
    # TODO: Review unreachable code - if len(parts) >= 3 and parts[0] == "providers":
    # TODO: Review unreachable code - # Reconstruct provider name and config key
    # TODO: Review unreachable code - provider = parts[1]
    # TODO: Review unreachable code - config_key = "_".join(parts[2:])
    # TODO: Review unreachable code - return f"providers.{provider}.{config_key}"
    # TODO: Review unreachable code - elif len(parts) >= 3 and parts[0] == "services":
    # TODO: Review unreachable code - # Reconstruct service name and config key
    # TODO: Review unreachable code - service = parts[1]
    # TODO: Review unreachable code - config_key = "_".join(parts[2:])
    # TODO: Review unreachable code - return f"services.{service}.{config_key}"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Simple case
    # TODO: Review unreachable code - return ".".join(parts)

    # TODO: Review unreachable code - def _parse_env_value(self, value: str) -> Any:
    # TODO: Review unreachable code - """Parse environment variable value to appropriate type.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - value: String value from environment

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Parsed value
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Handle booleans
    # TODO: Review unreachable code - if value.lower() in ("true", "yes", "1", "on"):
    # TODO: Review unreachable code - return True
    # TODO: Review unreachable code - elif value.lower() in ("false", "no", "0", "off"):
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Handle numbers
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if "." in value:
    # TODO: Review unreachable code - return float(value)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - return int(value)
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - pass

    # TODO: Review unreachable code - # Handle paths with tilde expansion
    # TODO: Review unreachable code - if value.startswith("~"):
    # TODO: Review unreachable code - return str(Path(value).expanduser())

    # TODO: Review unreachable code - # Return as string
    # TODO: Review unreachable code - return value

    # TODO: Review unreachable code - def _set_nested_value(self, data: dict[str, Any], path: str, value: Any) -> None:
    # TODO: Review unreachable code - """Set a nested value in a dictionary.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - data: Dictionary to modify
    # TODO: Review unreachable code - path: Dot-separated path
    # TODO: Review unreachable code - value: Value to set
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - keys = path.split(".")
    # TODO: Review unreachable code - current = data

    # TODO: Review unreachable code - for key in keys[:-1]:
    # TODO: Review unreachable code - if key not in current:
    # TODO: Review unreachable code - current[key] = {}
    # TODO: Review unreachable code - current = current[key]

    # TODO: Review unreachable code - current[keys[-1]] = value


# Global configuration instance
_config_loader: ConfigLoader | None = None


def get_config() -> ConfigLoader:
    """Get global configuration loader instance.

    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


# TODO: Review unreachable code - def get_config_value(path: str, default: Any = None) -> Any:
# TODO: Review unreachable code - """Get configuration value using global loader.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - path: Dot-separated path
# TODO: Review unreachable code - default: Default value

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Configuration value
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return get_config().get(path, default)
