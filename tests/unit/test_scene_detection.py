"""
Tests for scene detection module.
"""

import json
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from alicemultiverse.scene_detection import (
    DetectionMethod,
    Scene,
    SceneDetector,
    SceneType,
    Shot,
    ShotList,
    ShotListGenerator,
)


@pytest.fixture
def test_video():
    """Create a test video with scene changes."""
    temp_dir = tempfile.mkdtemp()
    video_path = Path(temp_dir) / "test_video.mp4"

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

    # Scene 1: Red frames (60 frames = 2 seconds)
    for _ in range(60):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 2] = 255  # Red channel
        out.write(frame)

    # Scene 2: Green frames (90 frames = 3 seconds)
    for _ in range(90):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 1] = 255  # Green channel
        out.write(frame)

    # Scene 3: Blue frames (60 frames = 2 seconds)
    for _ in range(60):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 0] = 255  # Blue channel
        out.write(frame)

    out.release()

    yield video_path

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_images():
    """Create test images for sequence detection."""
    temp_dir = tempfile.mkdtemp()
    images = []

    # Group 1: Red images
    for i in range(3):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:, :, 2] = 255
        path = Path(temp_dir) / f"red_{i}.jpg"
        cv2.imwrite(str(path), img)
        images.append(path)

    # Group 2: Green images
    for i in range(3):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:, :, 1] = 255
        path = Path(temp_dir) / f"green_{i}.jpg"
        cv2.imwrite(str(path), img)
        images.append(path)

    # Group 3: Blue images
    for i in range(2):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:, :, 0] = 255
        path = Path(temp_dir) / f"blue_{i}.jpg"
        cv2.imwrite(str(path), img)
        images.append(path)

    yield images

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


class TestSceneDetector:
    """Test scene detection functionality."""

    def test_detector_creation(self):
        """Test creating scene detector."""
        detector = SceneDetector()
        assert detector is not None
        assert detector.threshold == 0.3
        assert detector.min_scene_duration == 1.0
        assert detector.use_ai is True

    def test_detect_video_scenes(self, test_video):
        """Test detecting scenes in video."""
        detector = SceneDetector(use_ai=False)  # Skip AI for test
        scenes = detector.detect_video_scenes(test_video)

        # Should detect 3 scenes
        assert len(scenes) >= 2  # At least 2 scene changes

        # Check scene properties
        for scene in scenes:
            assert scene.scene_id is not None
            assert scene.duration > 0
            assert scene.start_time >= 0
            assert scene.end_time > scene.start_time
            assert scene.start_frame is not None
            assert scene.end_frame is not None
            assert scene.detection_method == DetectionMethod.CONTENT

    def test_detect_image_sequence_grouped(self, test_images):
        """Test detecting scenes in image sequence with grouping."""
        detector = SceneDetector(use_ai=False)
        scenes = detector.detect_image_sequence_scenes(test_images, group_similar=True)

        # Should group similar images
        assert len(scenes) == 3  # 3 color groups

        # Check image counts
        assert len(scenes[0].images) == 3  # Red images
        assert len(scenes[1].images) == 3  # Green images
        assert len(scenes[2].images) == 2  # Blue images

    def test_detect_image_sequence_individual(self, test_images):
        """Test detecting scenes in image sequence without grouping."""
        detector = SceneDetector(use_ai=False)
        scenes = detector.detect_image_sequence_scenes(test_images, group_similar=False)

        # Each image should be its own scene
        assert len(scenes) == len(test_images)

        for i, scene in enumerate(scenes):
            assert len(scene.images) == 1
            assert scene.images[0] == test_images[i]

    def test_export_scenes(self, test_images, tmp_path):
        """Test exporting scenes to JSON."""
        detector = SceneDetector(use_ai=False)
        scenes = detector.detect_image_sequence_scenes(test_images, group_similar=True)

        output_file = tmp_path / "scenes.json"
        detector.export_scenes(scenes, output_file)

        assert output_file.exists()

        # Load and verify
        with open(output_file) as f:
            data = json.load(f)

        assert data["scene_count"] == len(scenes)
        assert len(data["scenes"]) == len(scenes)

        # Check scene data
        for scene_data in data["scenes"]:
            assert "id" in scene_data
            assert "type" in scene_data
            assert "duration" in scene_data
            assert "confidence" in scene_data


class TestShotListGenerator:
    """Test shot list generation functionality."""

    def test_generator_creation(self):
        """Test creating shot list generator."""
        generator = ShotListGenerator()
        assert generator is not None
        assert generator.style == "cinematic"
        assert generator.min_duration == 2.0
        assert generator.max_duration == 8.0

    def test_generate_shot_list(self):
        """Test generating shot list from scenes."""
        # Create test scenes
        scenes = [
            Scene(
                scene_id="scene_001",
                scene_type=SceneType.ESTABLISHING,
                start_time=0.0,
                end_time=5.0,
                duration=5.0,
                detection_method=DetectionMethod.CONTENT
            ),
            Scene(
                scene_id="scene_002",
                scene_type=SceneType.DIALOGUE,
                start_time=5.0,
                end_time=15.0,
                duration=10.0,
                detection_method=DetectionMethod.CONTENT
            ),
            Scene(
                scene_id="scene_003",
                scene_type=SceneType.ACTION,
                start_time=15.0,
                end_time=20.0,
                duration=5.0,
                detection_method=DetectionMethod.CONTENT
            ),
        ]

        generator = ShotListGenerator(use_ai_suggestions=False)
        shot_list = generator.generate_shot_list(scenes, "Test Project")

        assert shot_list.project_name == "Test Project"
        assert shot_list.total_duration == 20.0
        assert shot_list.scene_count == 3
        assert shot_list.shot_count > 0

        # Check shots
        for shot in shot_list.shots:
            assert shot.shot_number > 0
            assert shot.scene_id in ["scene_001", "scene_002", "scene_003"]
            assert shot.duration > 0
            assert shot.shot_type is not None
            assert shot.description is not None

    def test_shot_distribution(self):
        """Test shot type distribution."""
        generator = ShotListGenerator()

        # Test establishing scene shots
        scene = Scene(
            scene_id="test",
            scene_type=SceneType.ESTABLISHING,
            start_time=0,
            end_time=10,
            duration=10,
            detection_method=DetectionMethod.CONTENT
        )

        shots = generator._generate_shots_for_scene(scene, 1, None)

        # Should have multiple shots
        assert len(shots) > 0

        # Check shot types match template
        shot_types = [s.shot_type for s in shots]
        assert any("Wide" in st for st in shot_types)

    def test_technical_details(self):
        """Test adding technical details to shots."""
        generator = ShotListGenerator(style="cinematic")

        shot = Shot(
            shot_number=1,
            scene_id="test",
            shot_type="Wide",
            duration=5.0,
            description="Test shot"
        )

        scene = Scene(
            scene_id="test",
            scene_type=SceneType.ESTABLISHING,
            start_time=0,
            end_time=5,
            duration=5,
            mood="dramatic",
            detection_method=DetectionMethod.CONTENT
        )

        generator._add_technical_details(shot, scene, "cinematic")

        assert shot.lens is not None
        assert shot.camera_movement is not None
        assert shot.camera_angle is not None
        assert len(shot.notes) > 0

    def test_export_shot_list(self, tmp_path):
        """Test exporting shot list."""
        # Create simple shot list
        shot_list = ShotList(
            project_name="Test Project",
            total_duration=10.0
        )

        shot_list.add_shot(Shot(
            shot_number=1,
            scene_id="scene_001",
            shot_type="Wide",
            duration=5.0,
            description="Establishing shot"
        ))

        shot_list.add_shot(Shot(
            shot_number=2,
            scene_id="scene_001",
            shot_type="Medium",
            duration=5.0,
            description="Medium shot"
        ))

        generator = ShotListGenerator()

        # Test JSON export
        json_file = tmp_path / "shotlist.json"
        generator.export_shot_list(shot_list, json_file, "json")
        assert json_file.exists()

        # Test CSV export
        csv_file = tmp_path / "shotlist.csv"
        generator.export_shot_list(shot_list, csv_file, "csv")
        assert csv_file.exists()

        # Test Markdown export
        md_file = tmp_path / "shotlist.md"
        generator.export_shot_list(shot_list, md_file, "markdown")
        assert md_file.exists()

        # Verify markdown content
        with open(md_file) as f:
            content = f.read()
            assert "Test Project" in content
            assert "Shot 1" in content
            assert "Shot 2" in content


class TestCLI:
    """Test CLI functionality."""

    def test_cli_import(self):
        """Test that CLI module can be imported."""
        from alicemultiverse.scene_detection.cli import scenes
        assert scenes is not None
