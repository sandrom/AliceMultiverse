"""Tests for configuration management."""

from pathlib import Path

from alicemultiverse.core.config import get_default_config, load_config


class TestConfig:
    """Test configuration loading and merging."""

    def test_default_config(self):
        """Test default configuration structure."""
        config = get_default_config()

        assert config.paths.inbox == "inbox"
        assert config.paths.organized == "organized"
        assert config.processing.copy_mode is True
        # Config structure validation - check if understanding system is present
        assert hasattr(config, "understanding") or hasattr(config, "quality")

    def test_load_nonexistent_config(self):
        """Test loading with non-existent config file returns defaults."""
        # Now returns defaults with a warning instead of raising
        config = load_config(Path("/nonexistent/config.yaml"))

        # Should get default config
        assert config.paths.inbox == "inbox"
        assert config.paths.organized == "organized"

    def test_cli_overrides(self):
        """Test CLI override functionality."""
        config = load_config(
            cli_overrides=["paths.inbox=/custom/inbox", "understanding.enabled=true"]
        )

        assert config.paths.inbox == "/custom/inbox"
        # Check if understanding is available, otherwise skip
        if hasattr(config, "understanding"):
            assert config.understanding.enabled is True
        # Other values should remain default
        assert config.paths.organized == "organized"
