"""Tests for configuration management."""

from pathlib import Path

import pytest

from alicemultiverse.core.config import get_default_config, load_config


class TestConfig:
    """Test configuration loading and merging."""

    def test_default_config(self):
        """Test default configuration structure."""
        config = get_default_config()

        assert config["paths"]["inbox"] == "inbox"
        assert config["paths"]["organized"] == "organized"
        assert config["processing"]["copy_mode"] is True
        assert config["quality"]["thresholds"]["3_star"]["min"] == 45
        assert config["quality"]["thresholds"]["3_star"]["max"] == 65

    def test_load_nonexistent_config(self):
        """Test loading with non-existent config file."""
        from alicemultiverse.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            load_config(Path("/nonexistent/config.yaml"))

    def test_cli_overrides(self):
        """Test CLI override functionality."""
        config = load_config(
            cli_overrides=["paths.inbox=/custom/inbox", "quality.thresholds.3_star.max=70"]
        )

        assert config.paths.inbox == "/custom/inbox"
        assert config.quality.thresholds["3_star"].max == 70
        # Other values should remain default
        assert config.paths.organized == "organized"
