"""Secure API Key Manager for AliceMultiverse."""

import getpass
import json
import os
from pathlib import Path

import keyring

from ..logging import get_logger

logger = get_logger(__name__)


class APIKeyManager:
    """Manage API keys securely using multiple methods."""

    SERVICE_NAME = "AliceMultiverse"

    # Define all available API keys
    API_KEYS = {
        "sightengine_user": "SightEngine API User",
        "sightengine_secret": "SightEngine API Secret",
        "anthropic_api_key": "Anthropic Claude API Key",
        "claude": "Anthropic Claude API Key (legacy)",
        "openai": "OpenAI API Key (for GPT-4V)",
        "gpt4v": "GPT-4V API Key (alias for openai)",
    }

    def __init__(self, config_dir: Path | None = None):
        # Set config file path
        if config_dir:
            self.CONFIG_FILE = config_dir / "config.json"
        else:
            self.CONFIG_FILE = Path.home() / ".alicemultiverse" / "config.json"

        # Ensure config directory exists
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def get_api_key(self, key_name: str, prompt: str | None = None) -> str | None:
        """
        Get API key using fallback methods:
        1. Command line argument (if provided)
        2. Environment variable
        3. macOS Keychain
        4. Config file (~/.alicemultiverse/config.json)
        5. Interactive prompt (if allowed)
        """
        # 1. Environment variable
        # Handle different naming conventions
        if key_name == "sightengine_user":
            env_var = "SIGHTENGINE_API_USER"
        elif key_name == "sightengine_secret":
            env_var = "SIGHTENGINE_API_SECRET"
        elif key_name == "anthropic_api_key":
            env_var = "ANTHROPIC_API_KEY"
        else:
            env_var = f"{key_name.upper().replace('-', '_')}_API_KEY"

        if os.getenv(env_var):
            return os.getenv(env_var)

        # 2. macOS Keychain
        try:
            value = keyring.get_password(self.SERVICE_NAME, key_name)
            if value:
                return value
        except Exception as e:
            logger.debug(f"Unable to access keychain for {key_name}: {e}")

        # 3. Config file
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    config = json.load(f)
                if key_name in config:
                    return config[key_name]
            except Exception as e:
                logger.debug(f"Unable to read config file for {key_name}: {e}")

        # 4. Interactive prompt (if provided)
        if prompt:
            return getpass.getpass(prompt)

        return None

    def get_sightengine_credentials(self) -> str | None:
        """Get SightEngine credentials as 'user,secret' format."""
        user = self.get_api_key("sightengine_user")
        secret = self.get_api_key("sightengine_secret")

        if user and secret:
            return f"{user},{secret}"
        return None

    def set_api_key(self, key_name: str, value: str, method: str = "keychain") -> None:
        """Store API key using specified method."""
        if method == "keychain":
            keyring.set_password(self.SERVICE_NAME, key_name, value)
            logger.info(f"Stored {key_name} in macOS Keychain")

        elif method == "config":
            config = {}
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE) as f:
                    config = json.load(f)

            config[key_name] = value

            with open(self.CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)

            # Set restrictive permissions
            os.chmod(self.CONFIG_FILE, 0o600)
            logger.info(f"Stored {key_name} in {self.CONFIG_FILE}")

        elif method == "env":
            env_var = f"{key_name.upper().replace('-', '_')}_API_KEY"
            shell = os.environ.get("SHELL", "/bin/zsh")

            if shell is not None and "zsh" in shell:
                rc_file = Path.home() / ".zshrc"
            elif shell is not None and "bash" in shell:
                rc_file = Path.home() / ".bashrc"
            else:
                rc_file = Path.home() / ".profile"

            # Add to shell config
            with open(rc_file, "a") as f:
                f.write("\n# AliceMultiverse API Keys\n")
                f.write(f"export {env_var}='{value}'\n")

            logger.info(f"Added {env_var} to {rc_file}")
            logger.info(f"Run 'source {rc_file}' or restart terminal to use")

    def delete_api_key(self, key_name: str) -> None:
        """Delete API key from all storage methods."""
        # Keychain
        try:
            keyring.delete_password(self.SERVICE_NAME, key_name)
            logger.info(f"Deleted {key_name} from macOS Keychain")
        except Exception as e:
            logger.debug(f"Key {key_name} not found in keychain or unable to delete: {e}")

        # Config file
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    config = json.load(f)
                if key_name in config:
                    del config[key_name]
                    with open(self.CONFIG_FILE, "w") as f:
                        json.dump(config, f, indent=2)
                    logger.info(f"Deleted {key_name} from config file")
            except Exception as e:
                logger.debug(f"Unable to delete {key_name} from config file: {e}")

    def list_api_keys(self) -> list[str]:
        """List all stored API keys (without showing values)."""
        keys: set[str] = set()

        # Check environment
        env_mappings = {
            "SIGHTENGINE_API_USER": "sightengine_user",
            "SIGHTENGINE_API_SECRET": "sightengine_secret",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "OPENAI_API_KEY": "openai",
        }

        for env_var, key_name in env_mappings.items():
            if os.getenv(env_var):
                keys.add(f"{key_name} (environment)")

        # Also check for generic _API_KEY pattern
        for env_var in os.environ:
            if env_var.endswith("_API_KEY") and env_var not in env_mappings:
                keys.add(f"{env_var} (environment)")

        # Check config file
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    config = json.load(f)
                    for key in config:
                        keys.add(f"{key} (config file)")
            except Exception as e:
                logger.debug(f"Unable to read config file: {e}")

        # Check keychain (check all known keys)
        for key_name in self.API_KEYS.keys():
            try:
                if keyring.get_password(self.SERVICE_NAME, key_name):
                    keys.add(f"{key_name} (keychain)")
            except Exception as e:
                logger.debug(f"Unable to check keychain for {key_name}: {e}")

        return sorted(keys)
