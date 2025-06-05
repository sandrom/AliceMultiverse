"""Integration tests for video export functionality."""

import pytest
import tempfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from datetime import datetime
import asyncio

from alicemultiverse.workflows.video_export import (
    Timeline, TimelineClip, VideoExportManager,
    DaVinciResolveExporter, CapCutExporter, ProxyGenerator
)


class TestVideoExport:
    """Test video export functionality."""
    
    @pytest.fixture
    def sample_timeline(self, tmp_path):
        """Create a sample timeline for testing."""
        timeline = Timeline(
            name="Test_Timeline",
            duration=10.0,
            frame_rate=30.0,
            resolution=(1920, 1080)
        )
        
        # Create fake image files
        for i in range(3):
            img_path = tmp_path / f"image_{i}.jpg"
            img_path.write_text(f"fake image {i}")
            
            clip = TimelineClip(
                asset_path=img_path,
                start_time=i * 3.0,
                duration=3.0,
                transition_in="crossfade" if i > 0 else None,
                transition_in_duration=0.5 if i > 0 else 0
            )
            timeline.clips.append(clip)
        
        # Add some markers
        timeline.markers = [
            {"time": 0.0, "name": "Start", "type": "section"},
            {"time": 5.0, "name": "Middle", "type": "beat"},
            {"time": 9.0, "name": "End", "type": "section"}
        ]
        
        return timeline
    
    def test_edl_export(self, sample_timeline, tmp_path):
        """Test EDL export functionality."""
        output_path = tmp_path / "test.edl"
        
        exporter = DaVinciResolveExporter()
        result = exporter.export_edl(sample_timeline, output_path)
        
        assert result is True
        assert output_path.exists()
        
        # Verify EDL content
        content = output_path.read_text()
        assert "TITLE: Test_Timeline" in content
        assert "FCM: NON-DROP FRAME" in content
        assert "001" in content  # First edit number
        assert "crossfade" in content.upper()  # Transition
        
    def test_xml_export(self, sample_timeline, tmp_path):
        """Test XML export functionality."""
        output_path = tmp_path / "test.xml"
        
        exporter = DaVinciResolveExporter()
        result = exporter.export_xml(sample_timeline, output_path)
        
        assert result is True
        assert output_path.exists()
        
        # Parse and verify XML
        tree = ET.parse(output_path)
        root = tree.getroot()
        
        assert root.tag == "fcpxml"
        assert root.get("version") == "1.8"
        
        # Check resources
        resources = root.find(".//resources")
        assert resources is not None
        assets = resources.findall(".//asset")
        assert len(assets) == 3  # 3 clips
        
        # Check sequence
        sequence = root.find(".//sequence")
        assert sequence is not None
        assert sequence.get("duration") == "10.0s"
        
        # Check clips
        clips = root.findall(".//clip")
        assert len(clips) == 3
    
    def test_capcut_export(self, sample_timeline, tmp_path):
        """Test CapCut JSON export."""
        output_path = tmp_path / "test_capcut.json"
        
        exporter = CapCutExporter()
        result = exporter.export_json(sample_timeline, output_path)
        
        assert result is True
        assert output_path.exists()
        
        # Load and verify JSON
        with open(output_path) as f:
            data = json.load(f)
        
        assert data["version"] == "1.0"
        assert data["project_name"] == "Test_Timeline"
        assert data["duration"] == 10000  # milliseconds
        assert data["fps"] == 30.0
        
        # Check materials
        assert len(data["materials"]) == 3
        
        # Check video tracks
        assert len(data["tracks"]["video"]) == 3
        clip = data["tracks"]["video"][0]
        assert "material_id" in clip
        assert clip["start_time"] == 0
        assert clip["duration"] == 3000
        
        # Check markers
        assert len(data["markers"]) == 3
        assert data["markers"][0]["name"] == "Start"
    
    def test_timecode_conversion(self):
        """Test timecode conversion."""
        tc = DaVinciResolveExporter._seconds_to_timecode(3661.5, 30.0)
        assert tc == "01:01:01:15"  # 1 hour, 1 min, 1 sec, 15 frames
        
        tc = DaVinciResolveExporter._seconds_to_timecode(0.0, 30.0)
        assert tc == "00:00:00:00"
    
    def test_transition_mapping(self):
        """Test CapCut transition mapping."""
        assert CapCutExporter._map_transition("crossfade") == "fade"
        assert CapCutExporter._map_transition("dissolve") == "fade"
        assert CapCutExporter._map_transition("wipe") == "wipe_right"
        assert CapCutExporter._map_transition("unknown") == "fade"  # default
    
    def test_mood_suggestions(self):
        """Test mood-based suggestions."""
        suggestions = CapCutExporter._get_mood_suggestions("energetic")
        assert "transitions" in suggestions
        assert "effects" in suggestions
        assert suggestions["pace"] == "fast"
        
        suggestions = CapCutExporter._get_mood_suggestions("calm")
        assert suggestions["pace"] == "slow"
    
    @pytest.mark.asyncio
    async def test_video_export_manager(self, sample_timeline, tmp_path):
        """Test the main export manager."""
        manager = VideoExportManager()
        
        results = await manager.export_timeline(
            sample_timeline,
            tmp_path,
            formats=["edl", "xml", "capcut"],
            generate_proxies=False  # Skip proxy generation in test
        )
        
        assert results["success"] is True
        assert len(results["exports"]) == 3
        assert "edl" in results["exports"]
        assert "xml" in results["exports"]
        assert "capcut" in results["exports"]
        
        # Verify files exist
        for format_type, path in results["exports"].items():
            assert Path(path).exists()
    
    @pytest.mark.asyncio
    async def test_proxy_generation(self, tmp_path):
        """Test proxy file generation."""
        # Create a simple timeline with one image
        timeline = Timeline(
            name="Proxy_Test",
            duration=3.0,
            frame_rate=30.0
        )
        
        # Create a fake image
        img_path = tmp_path / "test_image.jpg"
        # Create a simple 100x100 white image
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='white')
        img.save(img_path)
        
        clip = TimelineClip(
            asset_path=img_path,
            start_time=0.0,
            duration=3.0
        )
        timeline.clips.append(clip)
        
        # Generate proxies
        generator = ProxyGenerator()
        proxy_map = await generator.generate_proxies(
            timeline,
            tmp_path / "proxies",
            proxy_resolution=(64, 36)  # Very small for testing
        )
        
        assert len(proxy_map) == 1
        proxy_path = list(proxy_map.values())[0]
        assert proxy_path.exists()
        
        # Check proxy size
        proxy_img = Image.open(proxy_path)
        assert proxy_img.size[0] <= 64
        assert proxy_img.size[1] <= 36


class TestTimelineCreation:
    """Test timeline creation from images."""
    
    @pytest.mark.asyncio
    async def test_simple_timeline_creation(self, tmp_path):
        """Test creating a simple timeline without music."""
        from alicemultiverse.workflows.video_export import (
            Timeline, TimelineClip, VideoExportManager
        )
        
        # Create fake images
        image_paths = []
        for i in range(5):
            img_path = tmp_path / f"img_{i}.jpg"
            img_path.write_text(f"fake image {i}")
            image_paths.append(img_path)
        
        # Create timeline manually (simulating what MCP tool does)
        timeline = Timeline(
            name="Simple_Timeline",
            duration=10.0,  # 5 images * 2 seconds
            frame_rate=30.0
        )
        
        current_time = 0.0
        for i, img_path in enumerate(image_paths):
            clip = TimelineClip(
                asset_path=img_path,
                start_time=current_time,
                duration=2.0,
                transition_in="crossfade" if i > 0 else None,
                transition_in_duration=0.5 if i > 0 else 0
            )
            timeline.clips.append(clip)
            current_time += 2.0 - (0.5 if i < len(image_paths) - 1 else 0)
        
        # Export
        manager = VideoExportManager()
        results = await manager.export_timeline(
            timeline,
            tmp_path / "exports",
            formats=["xml", "capcut"],
            generate_proxies=False
        )
        
        assert results["success"] is True
        assert len(results["exports"]) == 2
        
        # Verify CapCut JSON has correct structure
        capcut_path = results["exports"]["capcut"]
        with open(capcut_path) as f:
            data = json.load(f)
        
        assert len(data["tracks"]["video"]) == 5
        assert data["tracks"]["video"][1]["transition_in"]["type"] == "fade"
    
    def test_beat_sync_calculations(self):
        """Test beat synchronization calculations."""
        # Simulate beat points
        beat_points = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        image_count = 3
        
        # Calculate distribution
        images_per_beat = max(1, len(beat_points) // image_count)
        assert images_per_beat == 3
        
        # Test beat assignment
        for i in range(image_count):
            beat_index = min(i * images_per_beat, len(beat_points) - 1)
            if i == 0:
                assert beat_index == 0
            elif i == 1:
                assert beat_index == 3
            elif i == 2:
                assert beat_index == 6
    
    def test_timeline_clip_properties(self):
        """Test TimelineClip properties."""
        clip = TimelineClip(
            asset_path=Path("test.jpg"),
            start_time=1.0,
            duration=2.0,
            in_point=0.5,
            out_point=2.5
        )
        
        assert clip.end_time == 3.0  # start + duration
        assert clip.source_duration == 2.0  # out - in
        
        # Test with no out_point
        clip2 = TimelineClip(
            asset_path=Path("test2.jpg"),
            start_time=0.0,
            duration=5.0
        )
        assert clip2.source_duration == 5.0  # Uses duration