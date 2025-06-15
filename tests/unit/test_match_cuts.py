"""
Unit tests for match cut detection.
"""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from alicemultiverse.transitions.match_cuts import (
    MatchCutAnalysis,
    MatchCutDetector,
    MotionVector,
    ShapeMatch,
    export_match_cuts,
    find_match_cuts,
)


@pytest.fixture
def sample_images():
    """Create sample test images with shapes and motion cues."""
    images = []

    # Image 1: Circle on left side
    img1 = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.circle(img1, (160, 240), 80, (0, 0, 0), -1)

    # Image 2: Circle on right side (motion match)
    img2 = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.circle(img2, (480, 240), 80, (0, 0, 0), -1)

    # Image 3: Rectangle in center
    img3 = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.rectangle(img3, (220, 140), (420, 340), (0, 0, 0), -1)

    # Save to temporary files
    for i, img in enumerate([img1, img2, img3]):
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        Image.fromarray(img).save(tmp.name)
        images.append(Path(tmp.name))
        tmp.close()

    yield images

    # Cleanup
    for img_path in images:
        img_path.unlink(missing_ok=True)


class TestMotionVector:
    """Test MotionVector functionality."""

    def test_motion_vector_creation(self):
        """Test creating motion vectors."""
        vector = MotionVector(
            direction=(1.0, 0.0),
            magnitude=0.8,
            center=(0.5, 0.5)
        )

        assert vector.direction == (1.0, 0.0)
        assert vector.magnitude == 0.8
        assert vector.center == (0.5, 0.5)

    def test_motion_vector_similarity(self):
        """Test similarity calculation between vectors."""
        v1 = MotionVector(
            direction=(1.0, 0.0),
            magnitude=0.8,
            center=(0.5, 0.5)
        )

        # Very similar vector
        v2 = MotionVector(
            direction=(0.9, 0.1),
            magnitude=0.7,
            center=(0.6, 0.5)
        )

        similarity = v1.similarity_to(v2)
        assert 0.8 < similarity < 1.0

        # Opposite direction
        v3 = MotionVector(
            direction=(-1.0, 0.0),
            magnitude=0.8,
            center=(0.5, 0.5)
        )

        similarity = v1.similarity_to(v3)
        assert similarity < 0.3


class TestMatchCutDetector:
    """Test MatchCutDetector functionality."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = MatchCutDetector()
        assert detector.motion_threshold == 0.7
        assert detector.shape_threshold == 0.8

    def test_analyze_match_cut(self, sample_images):
        """Test analyzing match cut between two images."""
        detector = MatchCutDetector()

        # Analyze circle motion (left to right)
        analysis = detector.analyze_match_cut(
            sample_images[0],  # Circle on left
            sample_images[1]   # Circle on right
        )

        assert isinstance(analysis, MatchCutAnalysis)
        assert analysis.confidence > 0
        assert analysis.match_type in ["motion", "shape", "action", "composite"]
        assert 0 <= analysis.action_continuity <= 1

    def test_shape_detection(self, sample_images):
        """Test shape detection in images."""
        detector = MatchCutDetector()

        # Load test image with circle
        img = detector._load_image(sample_images[0])
        shapes = detector._detect_shapes(img)

        # Should detect at least one circle
        circles = [s for s in shapes if s["type"] == "circle"]
        assert len(circles) > 0

        # Load test image with rectangle
        img = detector._load_image(sample_images[2])
        shapes = detector._detect_shapes(img)

        # Should detect at least one rectangle
        rectangles = [s for s in shapes if s["type"] == "rectangle"]
        assert len(rectangles) > 0

    def test_motion_detection(self, sample_images):
        """Test motion pattern detection."""
        detector = MatchCutDetector()

        img = detector._load_image(sample_images[0])
        motions = detector._detect_motion(img)

        assert isinstance(motions, list)
        for motion in motions:
            assert isinstance(motion, MotionVector)
            assert 0 <= motion.magnitude <= 1
            assert len(motion.direction) == 2
            assert len(motion.center) == 2

    def test_match_cuts_to_dict(self, sample_images):
        """Test serialization of match cut analysis."""
        detector = MatchCutDetector()

        analysis = detector.analyze_match_cut(
            sample_images[0],
            sample_images[1]
        )

        data = analysis.to_dict()

        assert "motion_matches" in data
        assert "shape_matches" in data
        assert "action_continuity" in data
        assert "match_type" in data
        assert "confidence" in data

        # Check structure
        assert isinstance(data["motion_matches"], list)
        assert isinstance(data["shape_matches"], list)
        assert isinstance(data["action_continuity"], float)


class TestMatchCutFunctions:
    """Test module-level functions."""

    def test_find_match_cuts(self, sample_images):
        """Test finding match cuts in sequence."""
        matches = find_match_cuts(sample_images, threshold=0.5)

        assert isinstance(matches, list)

        if matches:
            i, j, analysis = matches[0]
            assert isinstance(i, int)
            assert isinstance(j, int)
            assert i < j
            assert isinstance(analysis, MatchCutAnalysis)

    def test_export_match_cuts_json(self, sample_images):
        """Test exporting match cuts as JSON."""
        matches = find_match_cuts(sample_images, threshold=0.5)

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_match_cuts(matches, Path(tmp.name), format='json')

            # Verify file was created
            assert Path(tmp.name).exists()

            # Cleanup
            Path(tmp.name).unlink()

    def test_export_match_cuts_edl(self, sample_images):
        """Test exporting match cuts as EDL."""
        # Create some dummy matches
        analysis = MatchCutAnalysis(
            motion_matches=[],
            shape_matches=[],
            action_continuity=0.8,
            cut_point_suggestion=None,
            match_type="shape",
            confidence=0.85
        )

        matches = [(0, 1, analysis), (1, 2, analysis)]

        with tempfile.NamedTemporaryFile(suffix='.edl', delete=False) as tmp:
            export_match_cuts(matches, Path(tmp.name), format='edl')

            # Verify file was created and has content
            assert Path(tmp.name).exists()

            content = Path(tmp.name).read_text()
            assert "TITLE: Match Cuts" in content
            assert "MATCH CUT:" in content
            assert "CONFIDENCE:" in content

            # Cleanup
            Path(tmp.name).unlink()


class TestShapeMatch:
    """Test ShapeMatch dataclass."""

    def test_shape_match_creation(self):
        """Test creating shape match."""
        match = ShapeMatch(
            shape_type="circle",
            position1=(0.3, 0.5),
            position2=(0.7, 0.5),
            size1=0.2,
            size2=0.2,
            confidence=0.9
        )

        assert match.shape_type == "circle"
        assert match.position1 == (0.3, 0.5)
        assert match.position2 == (0.7, 0.5)
        assert match.size1 == 0.2
        assert match.size2 == 0.2
        assert match.confidence == 0.9
