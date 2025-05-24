"""Integration tests for full workflow scenarios."""

import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from alicemultiverse.interface.main_cli import main
from alicemultiverse.core.metadata_cache import MetadataCache
from alicemultiverse.organizer.media_organizer import MediaOrganizer


class TestFullWorkflow:
    """Test complete workflows from end to end."""
    
    @pytest.mark.integration
    def test_basic_organization_workflow(self, temp_dir, sample_media_files):
        """Test basic file organization without quality assessment."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        
        # Run organization
        result = main([
            "--inbox", str(inbox),
            "--output", str(organized),
            "--dry-run"
        ])
        
        assert result == 0
        # In dry-run, files shouldn't be moved
        assert all(f.exists() for f in sample_media_files.values())
    
    @pytest.mark.integration
    @patch('alicemultiverse.organizer.media_organizer.brisque_available')
    @patch('alicemultiverse.organizer.media_organizer.BRISQUEAssessor')
    def test_quality_assessment_workflow(self, mock_brisque_class, mock_is_available, temp_dir, sample_media_files):
        """Test organization with quality assessment."""
        # Mock BRISQUE availability
        mock_is_available.return_value = True
        
        # Create mock BRISQUE assessor instance
        mock_assessor = MagicMock()
        mock_assessor.assess_quality.return_value = (30.0, 4)  # 4-star quality
        mock_brisque_class.return_value = mock_assessor
        
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        
        # Run with quality assessment
        result = main([
            "--inbox", str(inbox),
            "--output", str(organized),
            "--quality",
            "--dry-run"
        ])
        
        assert result == 0
        # BRISQUE should be called for image files
        assert mock_assessor.assess_quality.call_count >= 3  # We have 3 test images
    
    @pytest.mark.integration
    def test_metadata_caching_workflow(self, temp_dir, sample_media_files):
        """Test that metadata is properly cached and reused."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        cache_dir = temp_dir / ".metadata"
        
        # First run
        with patch('alicemultiverse.organizer.media_organizer.MetadataCache') as mock_cache_class:
            mock_cache = mock_cache_class.return_value
            mock_cache.has_metadata.return_value = False
            mock_cache.get_metadata.return_value = None
            mock_cache.load.return_value = None
            mock_cache.get_stats.return_value = {
                'cache_hits': 0,
                'cache_misses': 5,
                'hit_rate': 0.0,
                'total_processed': 5,
                'time_saved': 0.0
            }
            
            result = main([
                "--inbox", str(inbox),
                "--output", str(organized),
                "--dry-run"
            ])
            
            assert result == 0
            # Cache should be checked and set
            assert mock_cache.get_metadata.called
            assert mock_cache.set_metadata.called
    
    @pytest.mark.integration
    @pytest.mark.slow
    @patch('alicemultiverse.cli.load_config')
    def test_watch_mode_workflow(self, mock_load_config, omega_config, temp_dir):
        """Test watch mode functionality."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        inbox.mkdir(exist_ok=True)
        
        # Setup config
        mock_load_config.return_value = omega_config
        
        # Run in watch mode with immediate exit
        with patch('time.sleep') as mock_sleep:
            # Make sleep raise KeyboardInterrupt to exit watch loop
            mock_sleep.side_effect = KeyboardInterrupt()
            
            result = main([
                "--inbox", str(inbox),
                "--output", str(organized),
                "--watch"
            ])
            
            assert result == 130  # KeyboardInterrupt exit code
    
    @pytest.mark.integration
    def test_pipeline_workflow(self, temp_dir, sample_media_files):
        """Test multi-stage pipeline workflow."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        
        # Mock the quality assessment
        with patch('alicemultiverse.quality.brisque.calculate_brisque_score') as mock_brisque:
            mock_brisque.return_value = 20.0  # 5-star quality
            
            result = main([
                "--inbox", str(inbox),
                "--output", str(organized),
                "--pipeline", "basic",
                "--dry-run"
            ])
            
            assert result == 0
    
    @pytest.mark.integration
    def test_cli_override_workflow(self, temp_dir):
        """Test that CLI overrides work properly."""
        inbox = temp_dir / "inbox"
        organized = temp_dir / "organized"
        inbox.mkdir(exist_ok=True)
        
        # Test with various overrides
        result = main([
            "--inbox", str(inbox),
            "--output", str(organized),
            "--paths.inbox=" + str(inbox),  # Override via OmegaConf syntax
            "--processing.copy_mode=false",
            "--quality.thresholds.3_star.max=70",
            "--dry-run"
        ])
        
        assert result == 0
    
    @pytest.mark.integration
    def test_error_handling_workflow(self, temp_dir):
        """Test error handling in various scenarios."""
        # Test with non-existent inbox
        result = main([
            "--inbox", str(temp_dir / "nonexistent"),
            "--output", str(temp_dir / "organized")
        ])
        
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
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            ffprobe_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            ffprobe_available = False
        
        if not ffprobe_available:
            pytest.skip("ffprobe not available")
        
        result = main([
            "--inbox", str(inbox),
            "--output", str(organized),
            "--dry-run"
        ])
        
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
        assert "AliceMultiverse - AI Media Organization System" in captured.out
        assert "Examples:" in captured.out
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
        assert "1.6.0" in captured.out
    
    @pytest.mark.integration
    def test_check_deps_command(self, capsys):
        """Test dependency checking."""
        result = main(["--check-deps"])
        
        captured = capsys.readouterr()
        # Should show status of dependencies
        assert "ffprobe" in captured.out
        assert "BRISQUE" in captured.out


class TestAPIKeyIntegration:
    """Test API key management integration."""
    
    @pytest.mark.integration
    @patch('alicemultiverse.keys.manager.APIKeyManager.list_api_keys')
    def test_keys_list_integration(self, mock_list, capsys):
        """Test 'alice keys list' command."""
        mock_list.return_value = ["claude (keychain)", "openai (environment)"]
        
        result = main(["keys", "list"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert "claude (keychain)" in captured.out
        assert "openai (environment)" in captured.out
    
    @pytest.mark.integration
    @patch('getpass.getpass')
    @patch('alicemultiverse.keys.manager.APIKeyManager.set_api_key')
    def test_keys_set_integration(self, mock_set, mock_getpass):
        """Test 'alice keys set' command."""
        mock_getpass.return_value = "test-api-key"
        
        result = main(["keys", "set", "anthropic_api_key", "--method", "config"])
        
        assert result == 0
        mock_set.assert_called_once_with("anthropic_api_key", "test-api-key", "config")