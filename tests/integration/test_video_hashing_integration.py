"""Integration test for video hashing with real video files."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from alicemultiverse.assets.hashing import hash_video_content
from alicemultiverse.assets.video_hashing import extract_video_info, hash_video_keyframes


class TestVideoHashingIntegration:
    """Integration tests for video hashing."""

    @pytest.fixture
    def test_video(self):
        """Create a simple test video using ffmpeg."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test_video.mp4"

            # Create a simple 3-second test video with color bars
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", "testsrc=duration=3:size=320x240:rate=10",
                "-pix_fmt", "yuv420p",
                "-y",
                str(video_path)
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                yield video_path
            except subprocess.CalledProcessError:
                pytest.skip("ffmpeg not available for integration test")
            except FileNotFoundError:
                pytest.skip("ffmpeg not installed")

    def test_video_info_extraction(self, test_video):
        """Test extracting info from a real video."""
        info = extract_video_info(test_video)

        assert info is not None
        assert "format" in info
        assert "streams" in info

        # Check video stream exists
        video_streams = [s for s in info["streams"] if s.get("codec_type") == "video"]
        assert len(video_streams) > 0

        # Check basic properties
        video_stream = video_streams[0]
        assert video_stream["width"] == 320
        assert video_stream["height"] == 240

    def test_video_keyframe_hashing(self, test_video):
        """Test hashing a real video file using keyframes."""
        hash1 = hash_video_keyframes(test_video, max_frames=5)
        hash2 = hash_video_keyframes(test_video, max_frames=5)

        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256

        # Different number of keyframes should produce different hash
        hash3 = hash_video_keyframes(test_video, max_frames=3)
        assert hash1 != hash3

    def test_video_content_hash_consistency(self, test_video):
        """Test that hash_video_content produces consistent results."""
        hash1 = hash_video_content(test_video)
        hash2 = hash_video_content(test_video)

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_different_videos_different_hashes(self, test_video):
        """Test that different videos produce different hashes."""
        # Create another video with different pattern
        with tempfile.TemporaryDirectory() as tmpdir:
            video2_path = Path(tmpdir) / "test_video2.mp4"

            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", "smptebars=duration=3:size=320x240:rate=10",  # Different test pattern
                "-pix_fmt", "yuv420p",
                "-y",
                str(video2_path)
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True)

                hash1 = hash_video_content(test_video)
                hash2 = hash_video_content(video2_path)

                assert hash1 != hash2
            except (subprocess.CalledProcessError, FileNotFoundError):
                pytest.skip("Could not create second test video")
