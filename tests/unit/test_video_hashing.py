"""Test video content hashing functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from alicemultiverse.assets.hashing import hash_video_content
from alicemultiverse.assets.video_hashing import (
    extract_keyframes,
    extract_video_info,
    hash_video_keyframes,
)


class TestVideoHashing:
    """Test video hashing functions."""

    def test_extract_video_info_missing_ffprobe(self):
        """Test handling when ffprobe is not available."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = extract_video_info(Path("test.mp4"))
            assert result is None

    def test_extract_video_info_invalid_json(self):
        """Test handling of invalid JSON from ffprobe."""
        mock_result = MagicMock()
        mock_result.stdout = "invalid json"

        with patch('subprocess.run', return_value=mock_result):
            result = extract_video_info(Path("test.mp4"))
            assert result is None

    def test_extract_video_info_success(self):
        """Test successful video info extraction."""
        mock_result = MagicMock()
        mock_result.stdout = '''{
            "format": {"duration": "60.0"},
            "streams": [
                {"codec_type": "video", "width": 1920, "height": 1080}
            ]
        }'''

        with patch('subprocess.run', return_value=mock_result):
            result = extract_video_info(Path("test.mp4"))
            assert result is not None
            assert result["format"]["duration"] == "60.0"
            assert result["streams"][0]["width"] == 1920

    def test_extract_keyframes_no_video_stream(self):
        """Test handling video with no video stream."""
        mock_info = {
            "format": {"duration": "60.0"},
            "streams": [{"codec_type": "audio"}]
        }

        with patch('alicemultiverse.assets.video_hashing.extract_video_info', return_value=mock_info):
            keyframes = extract_keyframes(Path("test.mp4"))
            assert keyframes == []

    def test_extract_keyframes_success(self):
        """Test successful keyframe extraction."""
        mock_info = {
            "format": {"duration": "10.0"},
            "streams": [{"codec_type": "video"}]
        }

        # Mock frame data
        mock_frame_data = b"fake_jpeg_data"
        mock_result = MagicMock()
        mock_result.stdout = mock_frame_data

        with patch('alicemultiverse.assets.video_hashing.extract_video_info', return_value=mock_info):
            with patch('subprocess.run', return_value=mock_result):
                keyframes = extract_keyframes(Path("test.mp4"), max_frames=3)
                assert len(keyframes) == 3
                assert all(frame == mock_frame_data for frame in keyframes)

    def test_hash_video_keyframes_no_frames(self):
        """Test hashing when no keyframes can be extracted."""
        with patch('alicemultiverse.assets.video_hashing.extract_keyframes', return_value=[]):
            # Mock file reading with side_effect for multiple reads
            mock_file = MagicMock()
            mock_file.read.side_effect = [b"file_content", b""]  # Return content then EOF

            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = mock_file

                hash_result = hash_video_keyframes(Path("test.mp4"))
                assert len(hash_result) == 64  # SHA-256 hash length

    def test_hash_video_keyframes_with_frames(self):
        """Test hashing with extracted keyframes."""
        mock_frames = [b"frame1", b"frame2", b"frame3"]
        mock_info = {
            "streams": [{
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "codec_name": "h264"
            }]
        }

        with patch('alicemultiverse.assets.video_hashing.extract_keyframes', return_value=mock_frames):
            with patch('alicemultiverse.assets.video_hashing.extract_video_info', return_value=mock_info):
                hash_result = hash_video_keyframes(Path("test.mp4"))
                assert len(hash_result) == 64  # SHA-256 hash length

                # Hash should be deterministic
                hash_result2 = hash_video_keyframes(Path("test.mp4"))
                assert hash_result == hash_result2

    def test_hash_video_content_integration(self):
        """Test the main hash_video_content function."""
        mock_frames = [b"frame1", b"frame2"]
        mock_info = {
            "streams": [{
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "codec_name": "h264"
            }]
        }

        with patch('alicemultiverse.assets.video_hashing.extract_keyframes', return_value=mock_frames):
            with patch('alicemultiverse.assets.video_hashing.extract_video_info', return_value=mock_info):
                hash_result = hash_video_content(Path("test.mp4"))
                assert len(hash_result) == 64  # SHA-256 hash length

    def test_hash_video_content_fallback(self):
        """Test fallback to file hashing when video hashing fails."""
        with patch('alicemultiverse.assets.video_hashing.extract_keyframes', side_effect=Exception("Test error")):
            # Mock file reading with side_effect for multiple reads
            mock_file = MagicMock()
            mock_file.read.side_effect = [b"file_content", b""]  # Return content then EOF

            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = mock_file

                hash_result = hash_video_content(Path("test.mp4"))
                assert len(hash_result) == 64  # SHA-256 hash length
