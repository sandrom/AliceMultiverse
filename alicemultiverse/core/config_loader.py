"""Configuration loader with defaults and environment variable support."""

import os
from pathlib import Path
from typing import Any

from .utils import load_yaml, safe_get


class ConfigLoader:
    """Loads configuration with defaults and environment overrides."""

    def __init__(self, defaults_path: Path | None = None):
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

        # Check loaded environment overrides
        override_value = safe_get(self._env_overrides, path)
        if override_value is not None:
            return override_value

        # Fall back to defaults
        return safe_get(self.defaults, path, default)

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

    def get_service_config(self, service_name: str) -> dict[str, Any]:
        """Get all configuration for a service.

        Args:
            service_name: Service name

        Returns:
            Service configuration dictionary
        """
        base_config = self.defaults.get("services", {}).get(service_name, {})

        # Apply environment overrides
        env_prefix = f"ALICE_SERVICE_{service_name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                base_config[config_key] = self._parse_env_value(value)

        return base_config

    def _load_env_overrides(self) -> dict[str, Any]:
        """Load all ALICE_ prefixed environment variables.

        Returns:
            Dictionary of overrides organized by path
        """
        overrides = {}

        for key, value in os.environ.items():
            if key.startswith("ALICE_"):
                # Convert ALICE_PROVIDERS_OPENAI_BASE_URL to providers.openai.base_url
                path = self._env_key_to_path(key)
                if path:
                    parsed_value = self._parse_env_value(value)
                    self._set_nested_value(overrides, path, parsed_value)

        return overrides

    def _path_to_env_key(self, path: str) -> str:
        """Convert config path to environment variable name.

        Args:
            path: Dot-separated path

        Returns:
            Environment variable name
        """
        # providers.openai.base_url -> ALICE_PROVIDERS_OPENAI_BASE_URL
        parts = path.split(".")
        return "ALICE_" + "_".join(p.upper() for p in parts)

    def _env_key_to_path(self, env_key: str) -> str | None:
        """Convert environment variable name to config path.

        Args:
            env_key: Environment variable name

        Returns:
            Dot-separated path or None
        """
        if not env_key.startswith("ALICE_"):
            return None

        # ALICE_PROVIDERS_OPENAI_BASE_URL -> providers.openai.base_url
        parts = env_key[6:].lower().split("_")

        # Handle special cases where underscore is part of the name
        if len(parts) >= 3 and parts[0] == "providers":
            # Reconstruct provider name and config key
            provider = parts[1]
            config_key = "_".join(parts[2:])
            return f"providers.{provider}.{config_key}"
        elif len(parts) >= 3 and parts[0] == "services":
            # Reconstruct service name and config key
            service = parts[1]
            config_key = "_".join(parts[2:])
            return f"services.{service}.{config_key}"
        else:
            # Simple case
            return ".".join(parts)

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Parsed value
        """
        # Handle booleans
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False

        # Handle numbers
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Handle paths with tilde expansion
        if value.startswith("~"):
            return str(Path(value).expanduser())

        # Return as string
        return value

    def _set_nested_value(self, data: dict[str, Any], path: str, value: Any) -> None:
        """Set a nested value in a dictionary.

        Args:
            data: Dictionary to modify
            path: Dot-separated path
            value: Value to set
        """
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


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


def get_config_value(path: str, default: Any = None) -> Any:
    """Get configuration value using global loader.

    Args:
        path: Dot-separated path
        default: Default value

    Returns:
        Configuration value
    """
    return get_config().get(path, default)
