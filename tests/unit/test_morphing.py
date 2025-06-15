"""
Unit tests for subject morphing functionality.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from alicemultiverse.transitions.models import TransitionType
from alicemultiverse.transitions.morphing import (
    MorphingTransitionMatcher,
    MorphKeyframe,
    MorphTransition,
    SubjectMorpher,
    SubjectRegion,
)


class TestSubjectRegion:
    """Test SubjectRegion data class."""

    def test_subject_region_creation(self):
        """Test creating a subject region."""
        region = SubjectRegion(
            label="person",
            confidence=0.95,
            bbox=(0.2, 0.3, 0.4, 0.5),
            center=(0.4, 0.55),
            area=0.2
        )

        assert region.label == "person"
        assert region.confidence == 0.95
        assert region.bbox == (0.2, 0.3, 0.4, 0.5)
        assert region.center == (0.4, 0.55)
        assert region.area == 0.2
        assert region.features is None

    def test_subject_region_with_features(self):
        """Test subject region with additional features."""
        features = {"pose": "standing", "age_group": "adult"}
        region = SubjectRegion(
            label="person",
            confidence=0.9,
            bbox=(0.1, 0.1, 0.5, 0.8),
            center=(0.35, 0.5),
            area=0.4,
            features=features
        )

        assert region.features == features


class TestMorphKeyframe:
    """Test MorphKeyframe data class."""

    def test_keyframe_creation(self):
        """Test creating a morph keyframe."""
        keyframe = MorphKeyframe(
            time=0.5,
            source_point=(0.3, 0.4),
            target_point=(0.4, 0.5),
            opacity=0.8,
            scale=1.2,
            rotation=15.0
        )

        assert keyframe.time == 0.5
        assert keyframe.source_point == (0.3, 0.4)
        assert keyframe.target_point == (0.4, 0.5)
        assert keyframe.opacity == 0.8
        assert keyframe.scale == 1.2
        assert keyframe.rotation == 15.0
        assert keyframe.control_points is None

    def test_keyframe_with_bezier(self):
        """Test keyframe with bezier control points."""
        control_points = [(0.35, 0.45), (0.38, 0.48)]
        keyframe = MorphKeyframe(
            time=1.0,
            source_point=(0.3, 0.4),
            target_point=(0.4, 0.5),
            control_points=control_points
        )

        assert keyframe.control_points == control_points


class TestSubjectMorpher:
    """Test SubjectMorpher class."""

    @pytest.fixture
    def morpher(self):
        """Create a morpher instance."""
        return SubjectMorpher()

    def test_calculate_subject_similarity_exact_match(self, morpher):
        """Test similarity calculation for exact match."""
        subject1 = SubjectRegion(
            label="person",
            confidence=0.9,
            bbox=(0.3, 0.3, 0.4, 0.4),
            center=(0.5, 0.5),
            area=0.16
        )
        subject2 = SubjectRegion(
            label="person",
            confidence=0.9,
            bbox=(0.3, 0.3, 0.4, 0.4),
            center=(0.5, 0.5),
            area=0.16
        )

        similarity = morpher._calculate_subject_similarity(subject1, subject2)
        assert similarity > 0.9  # Should be very high for identical subjects

    def test_calculate_subject_similarity_different_labels(self, morpher):
        """Test similarity for different but related labels."""
        subject1 = SubjectRegion(
            label="person",
            confidence=0.9,
            bbox=(0.3, 0.3, 0.4, 0.4),
            center=(0.5, 0.5),
            area=0.16
        )
        subject2 = SubjectRegion(
            label="face",
            confidence=0.9,
            bbox=(0.35, 0.35, 0.3, 0.3),
            center=(0.5, 0.5),
            area=0.09
        )

        similarity = morpher._calculate_subject_similarity(subject1, subject2)
        assert 0.3 < similarity < 0.8  # Should be moderate for related subjects

    def test_find_similar_subjects(self, morpher):
        """Test finding similar subjects between images."""
        source_subjects = [
            SubjectRegion("person", 0.9, (0.2, 0.2, 0.4, 0.6), (0.4, 0.5), 0.24),
            SubjectRegion("cat", 0.8, (0.6, 0.6, 0.3, 0.3), (0.75, 0.75), 0.09)
        ]

        target_subjects = [
            SubjectRegion("dog", 0.85, (0.1, 0.7, 0.2, 0.2), (0.2, 0.8), 0.04),
            SubjectRegion("person", 0.92, (0.25, 0.22, 0.38, 0.58), (0.44, 0.51), 0.22),
            SubjectRegion("cat", 0.87, (0.58, 0.62, 0.32, 0.28), (0.74, 0.76), 0.09)
        ]

        matches = morpher.find_similar_subjects(source_subjects, target_subjects)

        assert len(matches) == 2  # Should match person and cat
        assert matches[0][0].label == "person"
        assert matches[0][1].label == "person"
        assert matches[1][0].label == "cat"
        assert matches[1][1].label == "cat"

    def test_generate_morph_keyframes(self, morpher):
        """Test keyframe generation."""
        subject_pairs = [(
            SubjectRegion("person", 0.9, (0.2, 0.2, 0.4, 0.6), (0.4, 0.5), 0.24),
            SubjectRegion("person", 0.92, (0.25, 0.22, 0.38, 0.58), (0.44, 0.51), 0.22)
        )]

        keyframes = morpher.generate_morph_keyframes(
            subject_pairs,
            duration=1.0,
            morph_type="smooth",
            keyframe_count=5
        )

        assert len(keyframes) == 5
        assert keyframes[0].time == 0.0
        assert keyframes[-1].time == 1.0

        # Check interpolation
        for i, kf in enumerate(keyframes):
            assert 0 <= kf.opacity <= 1.0
            assert kf.scale > 0

    def test_morph_curves(self, morpher):
        """Test different morph curve functions."""
        # Test linear
        assert morpher.MORPH_CURVES["linear"](0.5) == 0.5

        # Test ease-in (should start slow)
        assert morpher.MORPH_CURVES["ease-in"](0.1) < 0.1

        # Test ease-out (should end slow)
        assert morpher.MORPH_CURVES["ease-out"](0.9) > 0.9

        # Test ease-in-out (S-curve)
        t = 0.5
        ease_value = morpher.MORPH_CURVES["ease-in-out"](t)
        assert 0.4 < ease_value < 0.6

    def test_create_morph_transition(self, morpher):
        """Test creating a complete morph transition."""
        source_subjects = [
            SubjectRegion("person", 0.9, (0.3, 0.3, 0.4, 0.4), (0.5, 0.5), 0.16)
        ]
        target_subjects = [
            SubjectRegion("person", 0.92, (0.32, 0.31, 0.39, 0.41), (0.52, 0.52), 0.16)
        ]

        transition = morpher.create_morph_transition(
            "source.jpg",
            "target.jpg",
            source_subjects,
            target_subjects,
            duration=1.5
        )

        assert transition is not None
        assert transition.source_image == "source.jpg"
        assert transition.target_image == "target.jpg"
        assert transition.duration == 1.5
        assert len(transition.subject_pairs) == 1
        assert len(transition.keyframes) > 0

    def test_export_for_after_effects(self, morpher, tmp_path):
        """Test After Effects export functionality."""
        # Create test transition
        transition = MorphTransition(
            source_image="source.jpg",
            target_image="target.jpg",
            duration=1.0,
            subject_pairs=[(
                SubjectRegion("person", 0.9, (0.2, 0.2, 0.4, 0.6), (0.4, 0.5), 0.24),
                SubjectRegion("person", 0.92, (0.25, 0.22, 0.38, 0.58), (0.44, 0.51), 0.22)
            )],
            keyframes=[
                MorphKeyframe(0.0, (0.4, 0.5), (0.4, 0.5), scale=1.0),
                MorphKeyframe(0.5, (0.42, 0.505), (0.42, 0.505), scale=1.05),
                MorphKeyframe(1.0, (0.44, 0.51), (0.44, 0.51), scale=1.08)
            ]
        )

        # Export
        output_file = tmp_path / "test_morph.json"
        result = morpher.export_for_after_effects(
            transition,
            str(output_file),
            fps=30.0
        )

        assert Path(result["json_path"]).exists()
        assert Path(result["jsx_path"]).exists()
        assert result["subject_count"] == 1
        assert result["keyframe_count"] == 3

        # Check JSON content
        with open(result["json_path"]) as f:
            data = json.load(f)

        assert data["version"] == "1.0"
        assert data["project"]["fps"] == 30.0
        assert len(data["morph_data"]) == 1
        assert len(data["morph_data"][0]["keyframes"]) == 3

    @pytest.mark.asyncio
    async def test_detect_subjects_with_mock(self, morpher):
        """Test subject detection with mocked analyzer."""
        with patch.object(morpher.analyzer, 'analyze') as mock_analyze:
            # Mock analysis result
            mock_result = Mock()
            mock_result.tags = {
                "objects": ["person", "face"],
                "scene": ["portrait"]
            }
            mock_analyze.return_value = mock_result

            subjects = await morpher.detect_subjects("test.jpg")

            assert len(subjects) >= 2
            assert any(s.label == "person" for s in subjects)
            assert any(s.label == "face" for s in subjects)


class TestMorphingTransitionMatcher:
    """Test MorphingTransitionMatcher class."""

    @pytest.fixture
    def matcher(self):
        """Create a matcher instance."""
        return MorphingTransitionMatcher()

    @pytest.mark.asyncio
    async def test_analyze_for_morphing(self, matcher):
        """Test analyzing image sequence for morphing."""
        # Mock the morpher's detect_subjects method
        with patch.object(matcher.morpher, 'detect_subjects') as mock_detect:
            # Set up mock subjects for 3 images
            mock_detect.side_effect = [
                # Image 1 subjects
                [SubjectRegion("person", 0.9, (0.3, 0.3, 0.4, 0.4), (0.5, 0.5), 0.16)],
                # Image 2 subjects
                [SubjectRegion("person", 0.92, (0.32, 0.31, 0.39, 0.41), (0.52, 0.52), 0.16)],
                # Image 3 subjects
                [SubjectRegion("person", 0.88, (0.34, 0.32, 0.38, 0.40), (0.53, 0.52), 0.15)]
            ]

            image_paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
            transitions = await matcher.analyze_for_morphing(image_paths)

            assert len(transitions) == 2  # Should find 2 transitions
            assert transitions[0].source_image == "img1.jpg"
            assert transitions[0].target_image == "img2.jpg"
            assert transitions[1].source_image == "img2.jpg"
            assert transitions[1].target_image == "img3.jpg"

    def test_suggest_morph_transition(self, matcher):
        """Test creating transition suggestion."""
        source_subjects = [
            SubjectRegion("cat", 0.9, (0.4, 0.4, 0.3, 0.3), (0.55, 0.55), 0.09)
        ]
        target_subjects = [
            SubjectRegion("cat", 0.88, (0.42, 0.41, 0.29, 0.31), (0.57, 0.57), 0.09)
        ]

        suggestion = matcher.suggest_morph_transition(
            "cat1.jpg",
            "cat2.jpg",
            source_subjects,
            target_subjects
        )

        assert suggestion is not None
        assert suggestion.source_image == "cat1.jpg"
        assert suggestion.target_image == "cat2.jpg"
        assert suggestion.transition_type == TransitionType.MORPH
        assert suggestion.duration > 0
        assert "morph_data" in suggestion.effects
        assert suggestion.confidence > 0


class TestMorphTransition:
    """Test MorphTransition data class."""

    def test_to_dict_conversion(self):
        """Test converting morph transition to dictionary."""
        transition = MorphTransition(
            source_image="source.jpg",
            target_image="target.jpg",
            duration=1.2,
            subject_pairs=[(
                SubjectRegion("person", 0.9, (0.2, 0.2, 0.4, 0.6), (0.4, 0.5), 0.24),
                SubjectRegion("person", 0.92, (0.25, 0.22, 0.38, 0.58), (0.44, 0.51), 0.22)
            )],
            keyframes=[
                MorphKeyframe(0.0, (0.4, 0.5), (0.4, 0.5)),
                MorphKeyframe(1.2, (0.44, 0.51), (0.44, 0.51))
            ],
            morph_type="elastic"
        )

        data = transition.to_dict()

        assert data["source_image"] == "source.jpg"
        assert data["target_image"] == "target.jpg"
        assert data["duration"] == 1.2
        assert data["morph_type"] == "elastic"
        assert len(data["subject_pairs"]) == 1
        assert len(data["keyframes"]) == 2

        # Check nested structure
        pair = data["subject_pairs"][0]
        assert pair["source"]["label"] == "person"
        assert pair["target"]["label"] == "person"
