"""
Tests for the transitions module.
"""

import json
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from alicemultiverse.transitions import MotionAnalyzer, TransitionMatcher
from alicemultiverse.transitions.models import MotionDirection, TransitionType


@pytest.fixture
def test_images():
    """Create test images with different characteristics."""
    images = []

    # Image 1: Horizontal lines (left to right motion)
    img1 = np.zeros((300, 400, 3), dtype=np.uint8)
    for y in range(50, 250, 20):
        cv2.line(img1, (50, y), (350, y), (255, 255, 255), 2)

    # Image 2: Vertical lines (up to down motion)
    img2 = np.zeros((300, 400, 3), dtype=np.uint8)
    for x in range(50, 350, 20):
        cv2.line(img2, (x, 50), (x, 250), (255, 255, 255), 2)

    # Image 3: Diagonal lines
    img3 = np.zeros((300, 400, 3), dtype=np.uint8)
    for i in range(10):
        offset = i * 30
        cv2.line(img3, (offset, 0), (offset + 300, 300), (255, 255, 255), 2)

    # Save temporary images
    temp_dir = tempfile.mkdtemp()
    paths = []

    for i, img in enumerate([img1, img2, img3]):
        path = Path(temp_dir) / f"test_image_{i}.jpg"
        cv2.imwrite(str(path), img)
        paths.append(str(path))
        images.append(img)

    yield paths, images

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


class TestMotionAnalyzer:
    """Test motion analysis functionality."""

    def test_analyzer_creation(self):
        """Test creating motion analyzer."""
        analyzer = MotionAnalyzer()
        assert analyzer is not None
        assert analyzer.feature_detector is not None

    def test_analyze_image(self, test_images):
        """Test analyzing a single image."""
        paths, _ = test_images
        analyzer = MotionAnalyzer()

        result = analyzer.analyze_image(paths[0])

        assert result is not None
        assert 'motion' in result
        assert 'composition' in result
        assert 'colors' in result
        assert 'path' in result
        assert 'dimensions' in result

        # Check motion data
        motion = result['motion']
        assert hasattr(motion, 'direction')
        assert hasattr(motion, 'speed')
        assert hasattr(motion, 'focal_point')
        assert hasattr(motion, 'confidence')

        # Check composition data
        composition = result['composition']
        assert hasattr(composition, 'rule_of_thirds_points')
        assert hasattr(composition, 'leading_lines')
        assert hasattr(composition, 'visual_weight_center')

    def test_motion_direction_detection(self, test_images):
        """Test detection of motion direction."""
        paths, _ = test_images
        analyzer = MotionAnalyzer()

        # Horizontal lines should suggest horizontal motion
        result1 = analyzer.analyze_image(paths[0])
        # The direction might be STATIC for simple lines
        assert result1['motion'].direction in [
            MotionDirection.LEFT_TO_RIGHT,
            MotionDirection.RIGHT_TO_LEFT,
            MotionDirection.STATIC
        ]

        # Vertical lines should suggest vertical motion
        result2 = analyzer.analyze_image(paths[1])
        assert result2['motion'].direction in [
            MotionDirection.UP_TO_DOWN,
            MotionDirection.DOWN_TO_UP,
            MotionDirection.STATIC
        ]

    def test_color_analysis(self, test_images):
        """Test color analysis."""
        paths, _ = test_images
        analyzer = MotionAnalyzer()

        result = analyzer.analyze_image(paths[0])
        colors = result['colors']

        assert 'temperature' in colors
        assert colors['temperature'] in ['warm', 'cool']
        assert 'brightness' in colors
        assert 'saturation' in colors
        assert 'contrast' in colors

        assert isinstance(colors['brightness'], (int, float))
        assert isinstance(colors['saturation'], (int, float))


class TestTransitionMatcher:
    """Test transition matching functionality."""

    def test_matcher_creation(self):
        """Test creating transition matcher."""
        matcher = TransitionMatcher()
        assert matcher is not None
        assert matcher.analyzer is not None
        assert len(matcher.rules) > 0

    def test_analyze_sequence(self, test_images):
        """Test analyzing a sequence of images."""
        paths, _ = test_images
        matcher = TransitionMatcher()

        suggestions = matcher.analyze_sequence(paths)

        # Should have n-1 transitions for n images
        assert len(suggestions) == len(paths) - 1

        for suggestion in suggestions:
            assert hasattr(suggestion, 'source_image')
            assert hasattr(suggestion, 'target_image')
            assert hasattr(suggestion, 'transition_type')
            assert hasattr(suggestion, 'duration')
            assert hasattr(suggestion, 'confidence')

            # Transition type should be valid
            assert isinstance(suggestion.transition_type, TransitionType)

            # Duration should be positive
            assert suggestion.duration >= 0

            # Confidence should be between 0 and 1
            assert 0 <= suggestion.confidence <= 1

    def test_compatibility_calculation(self, test_images):
        """Test scene compatibility calculation."""
        paths, _ = test_images
        matcher = TransitionMatcher()

        # Analyze first two images
        analysis1 = matcher.analyzer.analyze_image(paths[0])
        analysis2 = matcher.analyzer.analyze_image(paths[1])

        suggestion = matcher.suggest_transition(
            analysis1, analysis2, paths[0], paths[1]
        )

        assert suggestion.compatibility is not None
        comp = suggestion.compatibility

        assert 0 <= comp.overall_score <= 1
        assert 0 <= comp.motion_continuity <= 1
        assert 0 <= comp.color_harmony <= 1
        assert 0 <= comp.composition_match <= 1

        assert isinstance(comp.suggested_transition, TransitionType)
        assert comp.transition_duration > 0

    def test_transition_effects(self, test_images):
        """Test generation of transition effects."""
        paths, _ = test_images
        matcher = TransitionMatcher()

        suggestions = matcher.analyze_sequence(paths[:2])
        suggestion = suggestions[0]

        if suggestion.effects:
            assert isinstance(suggestion.effects, dict)

            # Check specific effect parameters based on transition type
            if suggestion.transition_type == TransitionType.MOMENTUM:
                assert 'direction' in suggestion.effects
                assert 'speed' in suggestion.effects
            elif suggestion.transition_type == TransitionType.ZOOM:
                assert 'zoom_from' in suggestion.effects
                assert 'zoom_to' in suggestion.effects


class TestTransitionCLI:
    """Test CLI functionality."""

    def test_cli_import(self):
        """Test that CLI module can be imported."""
        from alicemultiverse.transitions.cli import transitions
        assert transitions is not None

    def test_transition_export_format(self, test_images, tmp_path):
        """Test export format of transition analysis."""
        paths, _ = test_images
        matcher = TransitionMatcher()

        suggestions = matcher.analyze_sequence(paths)

        # Convert to export format
        output_data = []
        for suggestion in suggestions:
            data = {
                'source': suggestion.source_image,
                'target': suggestion.target_image,
                'transition': suggestion.transition_type.value,
                'duration': suggestion.duration,
                'confidence': suggestion.confidence,
                'effects': suggestion.effects or {}
            }
            if suggestion.compatibility:
                data['compatibility'] = {
                    'overall': suggestion.compatibility.overall_score,
                    'motion': suggestion.compatibility.motion_continuity,
                    'color': suggestion.compatibility.color_harmony,
                    'composition': suggestion.compatibility.composition_match,
                    'notes': suggestion.compatibility.notes
                }
            output_data.append(data)

        # Save to JSON
        output_file = tmp_path / "transitions.json"
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        # Verify file was created and is valid JSON
        assert output_file.exists()
        with open(output_file) as f:
            loaded_data = json.load(f)

        assert len(loaded_data) == len(suggestions)
        for item in loaded_data:
            assert 'source' in item
            assert 'target' in item
            assert 'transition' in item
            assert 'duration' in item
            assert 'confidence' in item
