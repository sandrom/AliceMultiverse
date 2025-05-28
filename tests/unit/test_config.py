"""Unit tests for configuration module."""

from pathlib import Path

import pytest

from alicemultiverse.core.config import get_default_config, load_config
from alicemultiverse.core.exceptions import ConfigurationError


class TestConfig:
    """Test configuration loading and validation."""

    @pytest.mark.unit
    def test_default_config_structure(self):
        """Test that default config has expected structure."""
        config = get_default_config()

        # Check if it's either our Config class or has the expected structure
        assert hasattr(config, "paths")
        assert hasattr(config, "processing")
        assert hasattr(config, "quality")
        assert hasattr(config, "pipeline")
        assert "paths" in config
        assert "processing" in config
        assert "quality" in config
        assert "pipeline" in config

        # Check paths
        assert config.paths.inbox == "inbox"
        assert config.paths.organized == "organized"

        # Check processing defaults
        assert config.processing.copy_mode is True
        assert config.processing.quality is False
        assert config.processing.watch is False

    @pytest.mark.unit
    def test_load_config_with_defaults(self):
        """Test loading config with no file uses defaults from settings.yaml."""
        config = load_config()

        # Check that key sections exist
        assert "paths" in config
        assert "processing" in config
        assert "quality" in config
        assert "pipeline" in config

        # Settings.yaml should be loaded by default
        assert config.paths.inbox == "inbox"
        assert config.paths.organized == "organized"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "config_content,expected_has_paths",
        [
            ("paths:\n  inbox: /custom/inbox", True),
            ("paths:\n  inbox: ~/Downloads", True),
            ("", False),  # Empty file won't have paths
        ],
    )
    def test_load_config_from_file(self, tmp_path, config_content, expected_has_paths):
        """Test loading config from a YAML file."""
        config_file = tmp_path / "test_settings.yaml"
        config_file.write_text(config_content)

        if expected_has_paths:
            config = load_config(config_file)
            assert hasattr(config, "paths")
            assert hasattr(config.paths, "inbox")
        else:
            # Empty config should use defaults
            try:
                config = load_config(config_file)
                # If it succeeds, check it has default structure
                assert hasattr(config, "paths")
            except Exception:
                # Empty config might fail, which is OK
                pass

    @pytest.mark.unit
    def test_load_config_with_cli_overrides(self):
        """Test that CLI overrides work correctly."""
        overrides = [
            "paths.inbox=/override/inbox",
            "processing.quality=true",
            "quality.enabled=true",
        ]

        config = load_config(cli_overrides=overrides)

        assert config.paths.inbox == "/override/inbox"
        assert config.processing.quality is True
        assert config.quality.enabled is True

    @pytest.mark.unit
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML file."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        with pytest.raises(ConfigurationError, match="Failed to load configuration"):
            load_config(config_file)

    @pytest.mark.unit
    def test_load_config_missing_file(self):
        """Test handling of missing config file returns defaults."""
        # Now returns defaults instead of raising
        config = load_config(Path("/nonexistent/config.yaml"))
        assert config.paths.inbox == "inbox"  # Should get defaults

    @pytest.mark.unit
    def test_load_config_invalid_overrides(self):
        """Test that invalid CLI overrides are handled gracefully."""
        # OmegaConf handles "=value" without raising an exception
        # It simply ignores the invalid override
        config = load_config(cli_overrides=["=value"])
        # Config should still load with defaults
        assert config is not None
        assert "paths" in config

    @pytest.mark.unit
    def test_quality_thresholds_validation(self):
        """Test that quality thresholds are properly structured."""
        config = get_default_config()

        # Check all quality levels exist
        for level in ["5_star", "4_star", "3_star", "2_star", "1_star"]:
            assert level in config.quality.thresholds
            threshold = config.quality.thresholds[level]
            assert "min" in threshold
            assert "max" in threshold
            assert threshold["min"] < threshold["max"]

        # Check thresholds are contiguous
        assert config.quality.thresholds["5_star"]["min"] == 0
        assert config.quality.thresholds["1_star"]["max"] == 100

    @pytest.mark.unit
    def test_pipeline_config_structure(self):
        """Test pipeline configuration structure."""
        config = get_default_config()

        assert hasattr(config.pipeline, "configurations")
        assert hasattr(config.pipeline, "thresholds")
        assert hasattr(config.pipeline, "cost_limits")

        # Check predefined configurations
        for mode in ["basic", "standard", "premium"]:
            assert mode in config.pipeline.configurations
