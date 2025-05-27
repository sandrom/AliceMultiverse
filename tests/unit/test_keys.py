"""Unit tests for API key management module."""

import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from alicemultiverse.core.keys.cli import run_keys_command
from alicemultiverse.core.keys.manager import APIKeyManager


class TestAPIKeyManager:
    """Test APIKeyManager class."""

    @pytest.fixture
    def manager(self, temp_dir):
        """Create APIKeyManager instance with temp directory."""
        config_dir = temp_dir / ".alicemultiverse"
        return APIKeyManager(config_dir=config_dir)

    @pytest.mark.unit
    def test_initialization_creates_config_dir(self, temp_dir):
        """Test that initialization creates config directory."""
        config_dir = temp_dir / ".alicemultiverse"
        manager = APIKeyManager(config_dir=config_dir)

        assert config_dir.exists()
        assert config_dir.is_dir()

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "key_name,env_var",
        [
            ("sightengine_user", "SIGHTENGINE_API_USER"),
            ("sightengine_secret", "SIGHTENGINE_API_SECRET"),
            ("claude", "CLAUDE_API_KEY"),
            ("openai", "OPENAI_API_KEY"),
        ],
    )
    def test_get_api_key_from_env(self, manager, key_name, env_var):
        """Test getting API key from environment variable."""
        test_value = "test-api-key-123"

        with patch.dict(os.environ, {env_var: test_value}):
            result = manager.get_api_key(key_name)

        assert result == test_value

    @pytest.mark.unit
    @patch("keyring.get_password")
    def test_get_api_key_from_keychain(self, mock_get_password, manager):
        """Test getting API key from keychain."""
        test_value = "keychain-api-key"
        mock_get_password.return_value = test_value

        result = manager.get_api_key("claude")

        assert result == test_value
        mock_get_password.assert_called_once_with("AliceMultiverse", "claude")

    @pytest.mark.unit
    def test_get_api_key_from_config_file(self, manager, temp_dir):
        """Test getting API key from config file."""
        # Create config file
        config_file = temp_dir / ".alicemultiverse" / "config.json"
        config_data = {"claude": "config-api-key"}
        config_file.write_text(json.dumps(config_data))

        with patch("keyring.get_password", return_value=None):
            result = manager.get_api_key("claude")

        assert result == "config-api-key"

    @pytest.mark.unit
    @patch("getpass.getpass")
    def test_get_api_key_with_prompt(self, mock_getpass, manager):
        """Test getting API key with interactive prompt."""
        mock_getpass.return_value = "prompted-key"

        with patch("keyring.get_password", return_value=None):
            result = manager.get_api_key("claude", prompt="Enter key: ")

        assert result == "prompted-key"
        mock_getpass.assert_called_once_with("Enter key: ")

    @pytest.mark.unit
    def test_get_sightengine_credentials(self, manager):
        """Test getting SightEngine credentials in correct format."""
        with patch.object(manager, "get_api_key") as mock_get:
            mock_get.side_effect = lambda k: "user123" if k == "sightengine_user" else "secret456"

            result = manager.get_sightengine_credentials()

        assert result == "user123,secret456"

    @pytest.mark.unit
    @patch("keyring.set_password")
    def test_set_api_key_keychain(self, mock_set_password, manager):
        """Test setting API key in keychain."""
        manager.set_api_key("claude", "test-key", method="keychain")

        mock_set_password.assert_called_once_with("AliceMultiverse", "claude", "test-key")

    @pytest.mark.unit
    def test_set_api_key_config(self, manager, temp_dir):
        """Test setting API key in config file."""
        config_file = temp_dir / ".alicemultiverse" / "config.json"

        manager.set_api_key("claude", "test-key", method="config")

        assert config_file.exists()
        with open(config_file) as f:
            config = json.load(f)
        assert config["claude"] == "test-key"

        # Check file permissions (should be 0o600)
        assert oct(config_file.stat().st_mode)[-3:] == "600"

    @pytest.mark.unit
    @patch("builtins.open", new_callable=mock_open)
    def test_set_api_key_env(self, mock_file, manager):
        """Test setting API key in shell config."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            manager.set_api_key("claude", "test-key", method="env")

        # Check that it tries to append to .zshrc
        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_called()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        assert "export CLAUDE_API_KEY='test-key'" in written_content

    @pytest.mark.unit
    @patch("keyring.delete_password")
    def test_delete_api_key_keychain(self, mock_delete, manager):
        """Test deleting API key from keychain."""
        manager.delete_api_key("claude")

        mock_delete.assert_called_once_with("AliceMultiverse", "claude")

    @pytest.mark.unit
    def test_delete_api_key_config(self, manager, temp_dir):
        """Test deleting API key from config file."""
        # Create config with multiple keys
        config_file = temp_dir / ".alicemultiverse" / "config.json"
        config_data = {"claude": "key1", "openai": "key2"}
        config_file.write_text(json.dumps(config_data))

        manager.delete_api_key("claude")

        # Check claude is removed but openai remains
        with open(config_file) as f:
            config = json.load(f)
        assert "claude" not in config
        assert config["openai"] == "key2"

    @pytest.mark.unit
    @patch("keyring.get_password")
    def test_list_api_keys(self, mock_get_password, manager, temp_dir):
        """Test listing all stored API keys."""
        # Setup environment
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            # Setup config file
            config_file = temp_dir / ".alicemultiverse" / "config.json"
            config_file.write_text(json.dumps({"openai": "config-key"}))

            # Setup keychain
            mock_get_password.side_effect = lambda s, k: "keychain-key" if k == "claude" else None

            keys = manager.list_api_keys()

        assert "anthropic_api_key (environment)" in keys  # from ANTHROPIC_API_KEY
        assert "openai (config file)" in keys
        assert "claude (keychain)" in keys


class TestKeysCliCommands:
    """Test CLI commands for key management."""

    @pytest.mark.unit
    @patch("alicemultiverse.core.keys.cli.APIKeyManager")
    @patch("builtins.input")
    @patch("getpass.getpass")
    def test_run_keys_set_command(self, mock_getpass, mock_input, mock_manager_class):
        """Test 'keys set' command."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_input.return_value = "test-user"
        mock_getpass.return_value = "test-secret"

        # Create args mock
        args = MagicMock()
        args.keys_command = "set"
        args.key_name = "sightengine_user"
        args.method = "keychain"

        result = run_keys_command(args)

        assert result == 0
        mock_manager.set_api_key.assert_called_once_with(
            "sightengine_user", "test-user", "keychain"
        )

    @pytest.mark.unit
    @patch("alicemultiverse.core.keys.cli.APIKeyManager")
    @patch("builtins.print")
    def test_run_keys_get_command(self, mock_print, mock_manager_class):
        """Test 'keys get' command."""
        mock_manager = MagicMock()
        mock_manager.get_api_key.return_value = "sk-ant-test-key-123"
        mock_manager_class.return_value = mock_manager

        args = MagicMock()
        args.keys_command = "get"
        args.key_name = "claude"

        result = run_keys_command(args)

        assert result == 0
        mock_print.assert_called_with("claude: sk-ant-t...")

    @pytest.mark.unit
    @patch("alicemultiverse.core.keys.cli.APIKeyManager")
    @patch("builtins.input")
    def test_run_keys_delete_command(self, mock_input, mock_manager_class):
        """Test 'keys delete' command."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_input.return_value = "y"

        args = MagicMock()
        args.keys_command = "delete"
        args.key_name = "claude"

        result = run_keys_command(args)

        assert result == 0
        mock_manager.delete_api_key.assert_called_once_with("claude")

    @pytest.mark.unit
    @patch("alicemultiverse.core.keys.cli.APIKeyManager")
    @patch("builtins.print")
    def test_run_keys_list_command(self, mock_print, mock_manager_class):
        """Test 'keys list' command."""
        mock_manager = MagicMock()
        mock_manager.list_api_keys.return_value = ["claude (keychain)", "openai (config file)"]
        mock_manager_class.return_value = mock_manager

        args = MagicMock()
        args.keys_command = "list"

        result = run_keys_command(args)

        assert result == 0
        # Check that keys were printed
        assert any("claude (keychain)" in str(call) for call in mock_print.call_args_list)
        assert any("openai (config file)" in str(call) for call in mock_print.call_args_list)
