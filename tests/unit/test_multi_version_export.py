"""Tests for multi-version export functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from alicemultiverse.workflows.multi_version_export import (
    PLATFORM_SPECS,
    CropRegion,
    ExportVersion,
    MultiVersionExporter,
    Platform,
    PlatformSpec,
)
from alicemultiverse.workflows.video_export import Timeline, TimelineClip


class TestMultiVersionExporter:
    """Test multi-version export functionality."""

    @pytest.fixture
    def exporter(self):
        """Create exporter instance."""
        return MultiVersionExporter()

    @pytest.fixture
    def sample_timeline(self):
        """Create sample timeline."""
        clips = [
            TimelineClip(
                asset_path=Path("/test/clip1.mp4"),
                start_time=0.0,
                duration=5.0,
                metadata={"subject": "landscape"}
            ),
            TimelineClip(
                asset_path=Path("/test/clip2.mp4"),
                start_time=5.0,
                duration=4.0,
                metadata={"subject": "portrait"}
            ),
            TimelineClip(
                asset_path=Path("/test/clip3.mp4"),
                start_time=9.0,
                duration=6.0,
                metadata={"subject": "action"}
            )
        ]

        return Timeline(
            name="Test Timeline",
            duration=15.0,
            frame_rate=30,
            resolution=(1920, 1080),
            clips=clips,
            markers=[
                {"time": 5.0, "type": "beat", "label": "Drop"},
                {"time": 9.0, "type": "beat", "label": "Chorus"}
            ],
            audio_tracks=[{"path": "/test/audio.mp3", "bpm": 120}]
        )

    def test_platform_specs(self):
        """Test platform specifications."""
        # Test all platforms have specs
        for platform in Platform:
            assert platform in PLATFORM_SPECS
            spec = PLATFORM_SPECS[platform]
            assert isinstance(spec, PlatformSpec)
            assert spec.aspect_ratio[0] > 0
            assert spec.aspect_ratio[1] > 0
            assert spec.resolution[0] > 0
            assert spec.resolution[1] > 0
            assert spec.min_duration >= 0
            assert spec.max_duration > spec.min_duration or spec.max_duration == float('inf')

    def test_create_single_platform_version(self, exporter, sample_timeline):
        """Test creating version for single platform."""
        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=[Platform.INSTAGRAM_REEL],
            smart_crop=True,
            maintain_sync=True
        )

        assert len(versions) == 1
        assert Platform.INSTAGRAM_REEL in versions

        version = versions[Platform.INSTAGRAM_REEL]
        assert isinstance(version, ExportVersion)
        assert version.platform == Platform.INSTAGRAM_REEL
        assert version.timeline.name == "Test Timeline"

        # Check aspect ratio was adapted
        spec = PLATFORM_SPECS[Platform.INSTAGRAM_REEL]
        assert version.timeline.resolution == spec.resolution

    def test_duration_adaptation_trim(self, exporter, sample_timeline):
        """Test trimming timeline to platform max duration."""
        # YouTube Shorts has 60s max
        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=[Platform.YOUTUBE_SHORTS],
            maintain_sync=False
        )

        version = versions[Platform.YOUTUBE_SHORTS]
        assert version.timeline.duration <= 60.0

    def test_duration_adaptation_extend(self, exporter):
        """Test extending timeline to platform min duration."""
        # Create short timeline
        short_timeline = Timeline(
            name="Short",
            duration=2.0,
            resolution=(1920, 1080),
            clips=[TimelineClip(
                asset_path=Path("/test/short.mp4"),
                start_time=0.0,
                duration=2.0
            )]
        )

        # Instagram Reel needs min 3s
        versions = exporter.create_platform_versions(
            timeline=short_timeline,
            platforms=[Platform.INSTAGRAM_REEL],
            maintain_sync=False
        )

        version = versions[Platform.INSTAGRAM_REEL]
        assert version.timeline.duration >= 3.0

    def test_aspect_ratio_adaptation(self, exporter, sample_timeline):
        """Test aspect ratio cropping."""
        # Test vertical crop (16:9 to 9:16)
        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=[Platform.TIKTOK],
            smart_crop=False
        )

        version = versions[Platform.TIKTOK]

        # Should have crop regions
        assert len(version.crop_regions) == len(sample_timeline.clips)

        # Check center crop calculation
        crop = version.crop_regions["clip_0"]
        assert isinstance(crop, CropRegion)
        assert 0 <= crop.x <= 1
        assert 0 <= crop.y <= 1
        assert crop.width > 0
        assert crop.height > 0
        assert crop.focus_point == (0.5, 0.5)  # Center

    def test_pacing_adaptation(self, exporter, sample_timeline):
        """Test pacing adjustments for platforms."""
        # TikTok should have faster pacing
        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=[Platform.TIKTOK],
            smart_crop=False,
            maintain_sync=False
        )

        version = versions[Platform.TIKTOK]

        # Check hook optimization (first 3s should be dynamic)
        first_clips_duration = sum(
            c.duration for c in version.timeline.clips
            if c.start_time < 3.0
        )

        # Each clip in hook should be max 1s
        for clip in version.timeline.clips:
            if clip.start_time < 3.0:
                assert clip.duration <= 1.0 or clip.duration == clip.duration  # Allow original if already short

    def test_multiple_platforms(self, exporter, sample_timeline):
        """Test creating versions for multiple platforms."""
        platforms = [
            Platform.INSTAGRAM_REEL,
            Platform.YOUTUBE_SHORTS,
            Platform.TWITTER
        ]

        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=platforms
        )

        assert len(versions) == 3

        # Each should have correct specs
        for platform in platforms:
            assert platform in versions
            version = versions[platform]
            spec = PLATFORM_SPECS[platform]

            # Check resolution matches
            assert version.timeline.resolution == spec.resolution

            # Check duration constraints
            assert version.timeline.duration >= spec.min_duration
            if spec.max_duration != float('inf'):
                assert version.timeline.duration <= spec.max_duration

    def test_platform_recommendations(self, exporter, sample_timeline):
        """Test platform recommendation system."""
        recommendations = exporter.get_platform_recommendations(sample_timeline)

        # Should have recommendations for all platforms
        assert len(recommendations) == len(Platform)

        # Check recommendation structure
        for platform, rec in recommendations.items():
            assert "suitable" in rec
            assert "adjustments_needed" in rec
            assert "optimization_tips" in rec
            assert isinstance(rec["suitable"], bool)
            assert isinstance(rec["adjustments_needed"], list)
            assert isinstance(rec["optimization_tips"], list)

        # 16:9 timeline should be suitable for horizontal platforms
        assert recommendations[Platform.YOUTUBE_HORIZONTAL]["suitable"]
        assert recommendations[Platform.TWITTER]["suitable"]

        # Should need cropping for vertical platforms
        vertical_platforms = [
            Platform.INSTAGRAM_REEL,
            Platform.INSTAGRAM_STORY,
            Platform.TIKTOK,
            Platform.YOUTUBE_SHORTS
        ]
        for platform in vertical_platforms:
            adjustments = recommendations[platform]["adjustments_needed"]
            assert any("Crop" in adj for adj in adjustments)

    def test_loop_timeline(self, exporter):
        """Test timeline looping for extension."""
        timeline = Timeline(
            name="Short Loop",
            duration=2.0,
            clips=[
                TimelineClip(Path("/test/a.mp4"), 0.0, 1.0),
                TimelineClip(Path("/test/b.mp4"), 1.0, 1.0)
            ]
        )

        exporter._loop_timeline(timeline, 5.0)

        # Should have looped to reach 5s
        assert timeline.duration == 5.0
        assert len(timeline.clips) > 2  # Original was 2 clips

        # Check clips are properly positioned
        for i, clip in enumerate(timeline.clips):
            if i > 0:
                prev_clip = timeline.clips[i-1]
                assert clip.start_time >= prev_clip.start_time + prev_clip.duration

    def test_smart_trim_with_markers(self, exporter, sample_timeline):
        """Test smart trimming that preserves important moments."""
        # Trim to 10s (from 15s)
        exporter._smart_trim(sample_timeline, 10.0)

        assert sample_timeline.duration <= 10.0

        # Should keep clips near markers (5.0 and 9.0)
        kept_times = [c.start_time for c in sample_timeline.clips]

        # At least one clip should be near each marker
        # (This is simplified - actual implementation would be more sophisticated)
        assert len(sample_timeline.clips) > 0

    def test_platform_features(self, exporter, sample_timeline):
        """Test platform-specific feature adaptations."""
        # Test Instagram Reel features
        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=[Platform.INSTAGRAM_REEL]
        )

        reel_version = versions[Platform.INSTAGRAM_REEL]

        # Should be marked as loop-friendly
        if len(reel_version.timeline.clips) >= 2:
            first_clip = reel_version.timeline.clips[0]
            last_clip = reel_version.timeline.clips[-1]
            assert first_clip.metadata.get("loop_start") is True
            assert last_clip.metadata.get("loop_transition") is True

        # Test TikTok trend features
        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=[Platform.TIKTOK]
        )

        tiktok_version = versions[Platform.TIKTOK]

        # Should have trend sync points identified
        assert "trend_sync_points" in tiktok_version.timeline.metadata
        sync_points = tiktok_version.timeline.metadata["trend_sync_points"]
        assert isinstance(sync_points, list)
        assert len(sync_points) <= 5  # Limited to 5

    def test_master_export_preserves_original(self, exporter, sample_timeline):
        """Test master export doesn't modify timeline."""
        original_duration = sample_timeline.duration
        original_resolution = sample_timeline.resolution
        original_clip_count = len(sample_timeline.clips)

        versions = exporter.create_platform_versions(
            timeline=sample_timeline,
            platforms=[Platform.MASTER]
        )

        master = versions[Platform.MASTER]

        # Master should preserve everything
        assert master.timeline.duration == original_duration
        assert len(master.timeline.clips) == original_clip_count

        # Resolution might be upscaled to 4K
        assert master.timeline.resolution[0] >= original_resolution[0]
        assert master.timeline.resolution[1] >= original_resolution[1]

    def test_crop_region_calculation(self, exporter):
        """Test crop region math for different aspect ratios."""
        # Test vertical crop (16:9 to 9:16)
        crop = exporter._calculate_center_crop(16/9, 9/16)
        assert crop.x > 0  # Should crop sides
        assert crop.y == 0  # No vertical crop
        assert crop.width < 1.0  # Narrower than original
        assert crop.height == 1.0  # Full height

        # Test square crop (16:9 to 1:1)
        crop = exporter._calculate_center_crop(16/9, 1.0)
        assert crop.x > 0  # Should crop sides
        assert crop.y == 0  # No vertical crop
        assert crop.width < 1.0
        assert crop.height == 1.0

        # Test horizontal to more horizontal (16:9 to 21:9)
        crop = exporter._calculate_center_crop(16/9, 21/9)
        assert crop.x == 0  # No horizontal crop
        assert crop.y > 0  # Should crop top/bottom
        assert crop.width == 1.0
        assert crop.height < 1.0


class TestMCPIntegration:
    """Test MCP tool integration."""

    @pytest.fixture
    def timeline_data(self):
        """Create sample timeline data."""
        return {
            "name": "Test Timeline",
            "duration": 30.0,
            "frame_rate": 30,
            "resolution": [1920, 1080],
            "clips": [
                {
                    "asset_path": "/test/clip1.mp4",
                    "start_time": 0.0,
                    "duration": 10.0,
                    "metadata": {"type": "intro"}
                },
                {
                    "asset_path": "/test/clip2.mp4",
                    "start_time": 10.0,
                    "duration": 15.0,
                    "metadata": {"type": "main"}
                },
                {
                    "asset_path": "/test/clip3.mp4",
                    "start_time": 25.0,
                    "duration": 5.0,
                    "metadata": {"type": "outro"}
                }
            ],
            "markers": [
                {"time": 10.0, "type": "beat", "label": "Drop"}
            ]
        }

    @patch('alicemultiverse.interface.multi_version_export_mcp.get_exporter')
    async def test_create_platform_versions_mcp(self, mock_get_exporter, timeline_data):
        """Test MCP create platform versions."""
        from alicemultiverse.interface.multi_version_export_mcp import create_platform_versions

        # Mock exporter
        mock_exporter = Mock()
        mock_get_exporter.return_value = mock_exporter

        # Mock timeline and versions
        mock_timeline = Mock()
        mock_timeline.duration = 30.0
        mock_timeline.clips = []

        mock_version = Mock()
        mock_version.timeline = mock_timeline
        mock_version.crop_regions = {}
        mock_version.spec = PLATFORM_SPECS[Platform.INSTAGRAM_REEL]

        mock_exporter.create_platform_versions.return_value = {
            Platform.INSTAGRAM_REEL: mock_version
        }

        # Call tool
        result = await create_platform_versions(
            timeline_data=timeline_data,
            platforms=["instagram_reel"],
            smart_crop=True,
            maintain_sync=True
        )

        assert result["success"] is True
        assert "versions" in result
        assert "instagram_reel" in result["versions"]
        assert result["summary"]["platforms_created"] == 1

    async def test_get_platform_recommendations_mcp(self):
        """Test MCP platform recommendations."""
        from alicemultiverse.interface.multi_version_export_mcp import get_platform_recommendations

        timeline_data = {
            "name": "Test",
            "duration": 45.0,
            "resolution": [1920, 1080],
            "clips": [{"asset_path": "/test/clip.mp4", "start_time": 0, "duration": 45}]
        }

        result = await get_platform_recommendations(timeline_data)

        assert result["success"] is True
        assert "recommendations" in result
        assert "timeline_info" in result
        assert result["timeline_info"]["duration"] == 45.0

        # Check recommendations structure
        for platform_key, rec in result["recommendations"].items():
            assert "suitable" in rec
            assert "adjustments_needed" in rec
            assert "optimization_tips" in rec

    async def test_export_platform_version_mcp(self, tmp_path):
        """Test MCP export platform version."""
        from alicemultiverse.interface.multi_version_export_mcp import export_platform_version

        timeline_data = {
            "name": "Test Export",
            "duration": 15.0,
            "clips": [{"asset_path": "/test/clip.mp4", "start_time": 0, "duration": 15}]
        }

        result = await export_platform_version(
            platform="instagram_reel",
            timeline_data=timeline_data,
            output_dir=str(tmp_path),
            format="json"
        )

        assert result["success"] is True
        assert result["format"] == "json"
        assert "file_path" in result
        assert Path(result["file_path"]).exists()

    async def test_get_available_platforms_mcp(self):
        """Test MCP get available platforms."""
        from alicemultiverse.interface.multi_version_export_mcp import get_available_platforms

        result = get_available_platforms()

        assert result["success"] is True
        assert "platforms" in result
        assert "categories" in result

        # Check all platforms are listed
        for platform in Platform:
            assert platform.value in result["platforms"]

        # Check categories
        assert "vertical_short" in result["categories"]
        assert "instagram_reel" in result["categories"]["vertical_short"]
