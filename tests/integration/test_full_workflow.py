"""Integration tests for full workflow scenarios."""

import subprocess
from unittest.mock import patch

import pytest

from alicemultiverse.interface.main_cli import main


class TestFullWorkflow:
    """Test complete workflows from end to end."""

    @pytest.mark.integration
    def test_basic_organization_workflow(self, temp_dir, sample_media_files):
        """Test basic file organization without quality assessment."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"

        # Run organization
        result = main(["--inbox", str(inbox), "--output", str(organized), "--dry-run"])

        assert result == 0
        # In dry-run, files shouldn't be moved
        assert all(f.exists() for f in sample_media_files.values())

    @pytest.mark.integration
    def test_understanding_workflow(self, temp_dir, sample_media_files):
        """Test organization with understanding system."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"

        # Run with understanding enabled (if available)
        result = main(["--inbox", str(inbox), "--output", str(organized), "--understanding", "--dry-run"])

        assert result == 0

    @pytest.mark.integration
    def test_metadata_caching_workflow(self, temp_dir, sample_media_files):
        """Test that metadata is properly cached and reused."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        cache_dir = temp_dir / ".metadata"

        # First run
        with patch("alicemultiverse.organizer.media_organizer.MetadataCache") as mock_cache_class:
            mock_cache = mock_cache_class.return_value
            mock_cache.has_metadata.return_value = False
            mock_cache.get_metadata.return_value = None
            mock_cache.load.return_value = None
            mock_cache.get_stats.return_value = {
                "cache_hits": 0,
                "cache_misses": 5,
                "hit_rate": 0.0,
                "total_processed": 5,
                "time_saved": 0.0,
            }

            result = main(["--inbox", str(inbox), "--output", str(organized), "--dry-run"])

            assert result == 0
            # Cache should be checked and set
            assert mock_cache.get_metadata.called
            assert mock_cache.set_metadata.called

    @pytest.mark.integration
    @pytest.mark.slow
    @patch("alicemultiverse.core.config_dataclass.load_config")
    def test_watch_mode_workflow(self, mock_load_config, omega_config, temp_dir):
        """Test watch mode functionality."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        inbox.mkdir(exist_ok=True)

        # Setup config
        mock_load_config.return_value = omega_config

        # Run in watch mode with immediate exit
        with patch("time.sleep") as mock_sleep:
            # Make sleep raise KeyboardInterrupt to exit watch loop
            mock_sleep.side_effect = KeyboardInterrupt()

            result = main(["--inbox", str(inbox), "--output", str(organized), "--watch"])

            assert result == 130  # KeyboardInterrupt exit code

    @pytest.mark.integration
    def test_pipeline_workflow(self, temp_dir, sample_media_files):
        """Test multi-stage pipeline workflow."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"

        # Test basic pipeline without mocking
        result = main(
            [
                "--inbox",
                str(inbox),
                "--output",
                str(organized),
                "--pipeline",
                "basic",
                "--dry-run",
            ]
        )

        assert result == 0

    @pytest.mark.integration
    def test_cli_override_workflow(self, temp_dir):
        """Test that CLI overrides work properly."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        inbox.mkdir(exist_ok=True)

        # Test with various overrides
        result = main(
            [
                "--inbox",
                str(inbox),
                "--output",
                str(organized),
                "--paths.inbox=" + str(inbox),  # Override via OmegaConf syntax
                "--processing.copy_mode=false",
                "--understanding.enabled=true",
                "--dry-run",
            ]
        )

        assert result == 0

    @pytest.mark.integration
    def test_error_handling_workflow(self, temp_dir):
        """Test error handling in various scenarios."""
        # Test with non-existent inbox
        result = main(
            ["--inbox", str(temp_dir / "nonexistent"), "--output", str(temp_dir / "organized")]
        )

        assert result == 1  # Configuration error

    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_video_processing_workflow(self, temp_dir):
        """Test processing of video files."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        inbox.mkdir(exist_ok=True)

        # Create a test video file
        video_file = inbox / "test.mp4"
        video_file.write_bytes(b"fake video data")

        # Check if ffprobe is available
        try:
            subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
            ffprobe_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            ffprobe_available = False

        if not ffprobe_available:
            pytest.skip("ffprobe not available")

        result = main(["--inbox", str(inbox), "--output", str(organized), "--dry-run"])

        assert result == 0


class TestCommandLineInterface:
    """Test command-line interface behavior."""

    @pytest.mark.integration
    def test_help_output(self, capsys):
        """Test that help output is properly formatted."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()

        # Check key sections are present
        assert "AliceMultiverse" in captured.out
        assert any(word in captured.out for word in ["Examples:", "Debug Examples:"])
        assert "--inbox" in captured.out
        assert "--quality" in captured.out
        assert "keys" in captured.out

    @pytest.mark.integration
    def test_version_output(self, capsys):
        """Test version output."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "1.7.1" in captured.out

    @pytest.mark.integration
    def test_check_deps_command(self, capsys):
        """Test dependency checking."""
        result = main(["--check-deps"])

        captured = capsys.readouterr()
        # Should show status of dependencies
        assert "ffprobe" in captured.out
        assert "Understanding system" in captured.out


class TestAPIKeyIntegration:
    """Test API key management integration."""

    @pytest.mark.integration
    @patch("alicemultiverse.core.keys.manager.APIKeyManager.list_api_keys")
    def test_keys_list_integration(self, mock_list, capsys):
        """Test 'alice keys list' command."""
        mock_list.return_value = ["claude (keychain)", "openai (environment)"]

        result = main(["keys", "list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "claude (keychain)" in captured.out
        assert "openai (environment)" in captured.out

    @pytest.mark.integration
    @patch("getpass.getpass")
    @patch("alicemultiverse.core.keys.manager.APIKeyManager.set_api_key")
    def test_keys_set_integration(self, mock_set, mock_getpass):
        """Test 'alice keys set' command."""
        mock_getpass.return_value = "test-api-key"

        result = main(["keys", "set", "anthropic_api_key", "--method", "config"])

        assert result == 0
        mock_set.assert_called_once_with("anthropic_api_key", "test-api-key", "config")
