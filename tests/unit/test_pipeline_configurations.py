"""Test different pipeline configurations."""

from unittest.mock import Mock, patch

import pytest
from omegaconf import OmegaConf

from alicemultiverse.pipeline.pipeline_organizer import PipelineOrganizer


class TestPipelineConfigurations:
    """Test various pipeline configurations."""

    @pytest.mark.unit
    def test_pipeline_stage_combinations(self, sample_config):
        """Test that different pipeline modes create the correct stages."""
        test_cases = [
            # (mode, expected_stages)
            ("basic", ["brisque"]),
            ("brisque", ["brisque"]),
            ("standard", ["brisque", "sightengine"]),
            ("brisque-sightengine", ["brisque", "sightengine"]),
            ("brisque-claude", ["brisque", "claude"]),
            ("premium", ["brisque", "sightengine", "claude"]),
            ("full", ["brisque", "sightengine", "claude"]),
            ("brisque-sightengine-claude", ["brisque", "sightengine", "claude"]),
        ]

        for mode, expected_stages in test_cases:
            sample_config["pipeline"]["mode"] = mode
            config = OmegaConf.create(sample_config)

            with patch("alicemultiverse.pipeline.pipeline_organizer.APIKeyManager") as mock_keys:
                mock_key_manager = Mock()
                mock_key_manager.get_api_key.side_effect = lambda k: "test-key"
                mock_keys.return_value = mock_key_manager

                organizer = PipelineOrganizer(config)

                # Get actual stage names
                actual_stages = [stage.name() for stage in organizer.pipeline_stages]

                assert (
                    actual_stages == expected_stages
                ), f"Mode '{mode}' should create stages {expected_stages}, got {actual_stages}"

    @pytest.mark.unit
    def test_brisque_claude_pipeline(self, sample_config):
        """Test BRISQUE + Claude pipeline (skipping SightEngine)."""
        sample_config["pipeline"]["mode"] = "brisque-claude"
        config = OmegaConf.create(sample_config)

        with patch("alicemultiverse.pipeline.pipeline_organizer.APIKeyManager") as mock_keys:
            mock_key_manager = Mock()
            mock_key_manager.get_api_key.side_effect = lambda k: "test-key"
            mock_keys.return_value = mock_key_manager

            organizer = PipelineOrganizer(config)

            # Should have exactly 2 stages
            assert len(organizer.pipeline_stages) == 2
            assert organizer.pipeline_stages[0].name() == "brisque"
            assert organizer.pipeline_stages[1].name() == "claude"

            # Verify costs
            assert organizer.pipeline_stages[0].get_cost() == 0.0  # BRISQUE is free
            assert organizer.pipeline_stages[1].get_cost() == 0.002  # Claude default cost

    @pytest.mark.unit
    def test_custom_pipeline_configuration(self, sample_config):
        """Test custom pipeline with specific stages."""
        sample_config["pipeline"]["mode"] = "custom"
        sample_config["pipeline"]["stages"] = ["brisque", "claude", "sightengine"]
        config = OmegaConf.create(sample_config)

        with patch("alicemultiverse.pipeline.pipeline_organizer.APIKeyManager") as mock_keys:
            mock_key_manager = Mock()
            mock_key_manager.get_api_key.side_effect = lambda k: "test-key"
            mock_keys.return_value = mock_key_manager

            organizer = PipelineOrganizer(config)

            # Should respect custom order
            assert len(organizer.pipeline_stages) == 3
            assert organizer.pipeline_stages[0].name() == "brisque"
            assert organizer.pipeline_stages[1].name() == "claude"
            assert organizer.pipeline_stages[2].name() == "sightengine"

    @pytest.mark.unit
    def test_unknown_pipeline_mode(self, sample_config):
        """Test that unknown pipeline mode results in no stages."""
        sample_config["pipeline"]["mode"] = "unknown-mode"
        config = OmegaConf.create(sample_config)

        with patch("alicemultiverse.pipeline.pipeline_organizer.APIKeyManager"):
            organizer = PipelineOrganizer(config)

            # Should have no stages
            assert len(organizer.pipeline_stages) == 0

    @pytest.mark.unit
    def test_pipeline_without_api_keys(self, sample_config):
        """Test that pipelines requiring API keys fail gracefully without them."""
        sample_config["pipeline"]["mode"] = "brisque-claude"
        config = OmegaConf.create(sample_config)

        with patch("alicemultiverse.pipeline.pipeline_organizer.APIKeyManager") as mock_keys:
            mock_key_manager = Mock()
            # Return None for API keys
            mock_key_manager.get_api_key.return_value = None
            mock_keys.return_value = mock_key_manager

            organizer = PipelineOrganizer(config)

            # Should only have BRISQUE stage (Claude requires API key)
            assert len(organizer.pipeline_stages) == 1
            assert organizer.pipeline_stages[0].name() == "brisque"

    @pytest.mark.unit
    def test_pipeline_cost_estimation(self, sample_config):
        """Test cost estimation for different pipelines."""
        test_cases = [
            ("basic", 0.0),  # BRISQUE only
            ("brisque-sightengine", 0.001),  # BRISQUE + SightEngine
            ("brisque-claude", 0.002),  # BRISQUE + Claude
            ("premium", 0.003),  # All three
        ]

        for mode, expected_cost in test_cases:
            sample_config["pipeline"]["mode"] = mode
            config = OmegaConf.create(sample_config)

            with patch("alicemultiverse.pipeline.pipeline_organizer.APIKeyManager") as mock_keys:
                mock_key_manager = Mock()
                mock_key_manager.get_api_key.side_effect = lambda k: "test-key"
                mock_keys.return_value = mock_key_manager

                organizer = PipelineOrganizer(config)

                # Calculate total cost
                total_cost = sum(stage.get_cost() for stage in organizer.pipeline_stages)

                assert total_cost == pytest.approx(
                    expected_cost
                ), f"Pipeline '{mode}' should cost ${expected_cost}, got ${total_cost}"
