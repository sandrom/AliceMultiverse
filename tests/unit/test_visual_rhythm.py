"""
Unit tests for visual rhythm analysis.
"""

import csv
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from alicemultiverse.transitions.visual_rhythm import (
    EnergyProfile,
    PacingSuggestion,
    RhythmAnalysis,
    VisualComplexity,
    VisualRhythmAnalyzer,
    export_rhythm_analysis,
    match_rhythm_to_music,
)


@pytest.fixture
def rhythm_images():
    """Create test images with varying complexity and energy."""
    images = []

    # Image 1: Simple, low energy (solid color)
    img1 = np.ones((480, 640, 3), dtype=np.uint8) * 100

    # Image 2: Medium complexity (gradient)
    img2 = np.zeros((480, 640, 3), dtype=np.uint8)
    for y in range(480):
        img2[y, :] = int(255 * y / 480)

    # Image 3: High complexity (noise pattern)
    img3 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Image 4: High energy (bright colors with edges)
    img4 = np.zeros((480, 640, 3), dtype=np.uint8)
    img4[:, :320] = [255, 0, 0]  # Red
    img4[:, 320:] = [0, 255, 0]  # Green

    # Save to temporary files
    for i, img in enumerate([img1, img2, img3, img4]):
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        Image.fromarray(img).save(tmp.name)
        images.append(Path(tmp.name))
        tmp.close()

    yield images

    # Cleanup
    for img_path in images:
        img_path.unlink(missing_ok=True)


class TestVisualComplexity:
    """Test VisualComplexity dataclass."""

    def test_visual_complexity_creation(self):
        """Test creating visual complexity."""
        complexity = VisualComplexity(
            edge_density=0.3,
            color_variance=0.5,
            texture_complexity=0.4,
            compositional_elements=5,
            movement_potential=0.2
        )

        assert complexity.edge_density == 0.3
        assert complexity.color_variance == 0.5
        assert complexity.texture_complexity == 0.4
        assert complexity.compositional_elements == 5
        assert complexity.movement_potential == 0.2

    def test_overall_complexity(self):
        """Test overall complexity calculation."""
        # Low complexity
        low = VisualComplexity(
            edge_density=0.1,
            color_variance=0.1,
            texture_complexity=0.1,
            compositional_elements=1,
            movement_potential=0.1
        )

        assert low.overall_complexity < 0.3

        # High complexity
        high = VisualComplexity(
            edge_density=0.9,
            color_variance=0.9,
            texture_complexity=0.9,
            compositional_elements=15,
            movement_potential=0.9
        )

        assert high.overall_complexity > 0.7


class TestEnergyProfile:
    """Test EnergyProfile dataclass."""

    def test_energy_profile_creation(self):
        """Test creating energy profile."""
        energy = EnergyProfile(
            visual_energy=0.7,
            brightness_energy=0.6,
            color_energy=0.8,
            motion_energy=0.5,
            emotional_energy=0.7
        )

        assert energy.visual_energy == 0.7
        assert energy.brightness_energy == 0.6
        assert energy.color_energy == 0.8
        assert energy.motion_energy == 0.5
        assert energy.emotional_energy == 0.7

    def test_total_energy(self):
        """Test total energy calculation."""
        # Low energy
        low = EnergyProfile(
            visual_energy=0.2,
            brightness_energy=0.1,
            color_energy=0.1,
            motion_energy=0.1,
            emotional_energy=0.2
        )

        assert low.total_energy < 0.3

        # High energy
        high = EnergyProfile(
            visual_energy=0.9,
            brightness_energy=0.9,
            color_energy=0.9,
            motion_energy=0.8,
            emotional_energy=0.9
        )

        assert high.total_energy > 0.8


class TestPacingSuggestion:
    """Test PacingSuggestion dataclass."""

    def test_pacing_suggestion_creation(self):
        """Test creating pacing suggestion."""
        pacing = PacingSuggestion(
            hold_duration=2.5,
            complexity_score=0.6,
            energy_score=0.4,
            cut_style="standard",
            reasoning="Balanced complexity and energy"
        )

        assert pacing.hold_duration == 2.5
        assert pacing.complexity_score == 0.6
        assert pacing.energy_score == 0.4
        assert pacing.cut_style == "standard"
        assert pacing.reasoning == "Balanced complexity and energy"


class TestVisualRhythmAnalyzer:
    """Test VisualRhythmAnalyzer functionality."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = VisualRhythmAnalyzer()
        assert analyzer.base_duration == 2.0
        assert analyzer.complexity_multiplier == 1.5

    def test_analyze_sequence_rhythm(self, rhythm_images):
        """Test analyzing rhythm of image sequence."""
        analyzer = VisualRhythmAnalyzer()

        analysis = analyzer.analyze_sequence_rhythm(rhythm_images)

        assert isinstance(analysis, RhythmAnalysis)
        assert len(analysis.shot_complexities) == len(rhythm_images)
        assert len(analysis.shot_energies) == len(rhythm_images)
        assert len(analysis.pacing_suggestions) == len(rhythm_images)
        assert 0 <= analysis.balance_score <= 1

    def test_complexity_analysis(self, rhythm_images):
        """Test visual complexity analysis."""
        analyzer = VisualRhythmAnalyzer()

        # Simple image should have low complexity
        simple_complexity = analyzer._analyze_complexity(rhythm_images[0])
        assert simple_complexity.overall_complexity < 0.3

        # Noisy image should have high complexity
        complex_complexity = analyzer._analyze_complexity(rhythm_images[2])
        assert complex_complexity.overall_complexity > 0.5

    def test_energy_analysis(self, rhythm_images):
        """Test energy profile analysis."""
        analyzer = VisualRhythmAnalyzer()

        # Dark image should have low energy
        low_energy = analyzer._analyze_energy(rhythm_images[0])
        assert low_energy.total_energy < 0.5

        # Bright colorful image should have high energy
        high_energy = analyzer._analyze_energy(rhythm_images[3])
        assert high_energy.total_energy > 0.5

    def test_pacing_suggestions(self, rhythm_images):
        """Test pacing suggestions based on complexity."""
        analyzer = VisualRhythmAnalyzer()

        complexities = [analyzer._analyze_complexity(img) for img in rhythm_images]
        energies = [analyzer._analyze_energy(img) for img in rhythm_images]

        pacing = analyzer._suggest_pacing(complexities, energies, None, None)

        assert len(pacing) == len(rhythm_images)

        for suggestion in pacing:
            assert suggestion.hold_duration > 0
            assert suggestion.cut_style in ["quick", "standard", "long", "hold"]
            assert suggestion.reasoning != ""

    def test_target_duration(self, rhythm_images):
        """Test pacing with target duration."""
        analyzer = VisualRhythmAnalyzer()

        target = 10.0  # 10 seconds total
        analysis = analyzer.analyze_sequence_rhythm(
            rhythm_images,
            target_duration=target
        )

        total_duration = sum(p.hold_duration for p in analysis.pacing_suggestions)
        assert abs(total_duration - target) < 0.1  # Close to target

    def test_bpm_sync(self, rhythm_images):
        """Test pacing with BPM synchronization."""
        analyzer = VisualRhythmAnalyzer()

        bpm = 120  # 120 BPM = 0.5s per beat
        analysis = analyzer.analyze_sequence_rhythm(
            rhythm_images[:2],  # Just 2 images
            music_bpm=bpm
        )

        # Durations should be multiples of beat duration (0.5s)
        beat_duration = 60.0 / bpm
        for pacing in analysis.pacing_suggestions:
            beats = pacing.hold_duration / beat_duration
            assert abs(beats - round(beats)) < 0.01  # Should be whole beats

    def test_rhythm_curve(self, rhythm_images):
        """Test rhythm curve generation."""
        analyzer = VisualRhythmAnalyzer()

        analysis = analyzer.analyze_sequence_rhythm(rhythm_images)

        assert len(analysis.rhythm_curve) == len(rhythm_images)

        # Curve should be normalized
        for value in analysis.rhythm_curve:
            assert 0 <= value <= 1

    def test_balance_score(self, rhythm_images):
        """Test rhythm balance calculation."""
        analyzer = VisualRhythmAnalyzer()

        # Varied images should have good balance
        analysis = analyzer.analyze_sequence_rhythm(rhythm_images)
        assert analysis.balance_score > 0.3

        # Same image repeated should have poor balance
        same_images = [rhythm_images[0]] * 4
        analysis = analyzer.analyze_sequence_rhythm(same_images)
        assert analysis.balance_score < 0.5


class TestRhythmAnalysis:
    """Test RhythmAnalysis dataclass."""

    def test_rhythm_analysis_to_dict(self, rhythm_images):
        """Test serialization of rhythm analysis."""
        analyzer = VisualRhythmAnalyzer()

        analysis = analyzer.analyze_sequence_rhythm(rhythm_images)
        data = analysis.to_dict()

        assert "shots" in data
        assert "rhythm_curve" in data
        assert "energy_curve" in data
        assert "balance_score" in data
        assert "total_duration" in data

        # Check structure
        assert isinstance(data["shots"], list)
        assert len(data["shots"]) == len(rhythm_images)

        for shot in data["shots"]:
            assert "complexity" in shot
            assert "energy" in shot
            assert "suggested_duration" in shot
            assert "cut_style" in shot


class TestMusicMatching:
    """Test music rhythm matching."""

    def test_match_rhythm_to_music(self, rhythm_images):
        """Test matching visual rhythm to music."""
        analyzer = VisualRhythmAnalyzer()

        visual_rhythm = analyzer.analyze_sequence_rhythm(rhythm_images)

        # Create fake music data
        music_energy = [0.3, 0.5, 0.8, 0.6]  # Match image count
        music_beats = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

        result = match_rhythm_to_music(
            visual_rhythm,
            music_energy,
            music_beats
        )

        assert "matched_cuts" in result
        assert "total_duration" in result
        assert "average_match_score" in result

        assert len(result["matched_cuts"]) == len(rhythm_images)

        for cut in result["matched_cuts"]:
            assert "shot_index" in cut
            assert "duration" in cut
            assert "visual_energy" in cut
            assert "music_energy" in cut
            assert "match_score" in cut
            assert cut["duration"] >= 0.5  # Minimum duration


class TestRhythmExport:
    """Test export functionality."""

    def test_export_json(self, rhythm_images):
        """Test JSON export."""
        analyzer = VisualRhythmAnalyzer()

        analysis = analyzer.analyze_sequence_rhythm(rhythm_images)

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            export_rhythm_analysis(analysis, Path(tmp.name), format='json')

            # Verify file was created and is valid JSON
            assert Path(tmp.name).exists()

            with open(tmp.name) as f:
                data = json.load(f)

            assert "shots" in data
            assert "rhythm_curve" in data

            # Cleanup
            Path(tmp.name).unlink()

    def test_export_csv(self, rhythm_images):
        """Test CSV export."""
        analyzer = VisualRhythmAnalyzer()

        analysis = analyzer.analyze_sequence_rhythm(rhythm_images)

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            export_rhythm_analysis(analysis, Path(tmp.name), format='csv')

            # Verify file was created and has correct structure
            assert Path(tmp.name).exists()

            with open(tmp.name) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == len(rhythm_images)

            # Check columns
            for row in rows:
                assert "shot" in row
                assert "complexity" in row
                assert "energy" in row
                assert "duration" in row
                assert "style" in row
                assert "reasoning" in row

            # Cleanup
            Path(tmp.name).unlink()
