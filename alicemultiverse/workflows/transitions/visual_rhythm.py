"""
Visual rhythm analysis for pacing and energy matching.

Analyzes visual complexity, energy levels, and pacing to create
rhythmic video edits that match musical or narrative flow.
"""

import json

# ImagePath type removed - using str instead
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np
from scipy import signal  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class VisualComplexity:
    """Measures visual complexity of an image."""
    edge_density: float  # 0-1 amount of edges
    color_variance: float  # 0-1 color diversity
    texture_complexity: float  # 0-1 texture detail
    compositional_elements: int  # Number of distinct regions
    movement_potential: float  # 0-1 implied motion

    @property
    def overall_complexity(self) -> float:
        """Calculate overall visual complexity score."""
        return (
            self.edge_density * 0.3 +
            self.color_variance * 0.2 +
            self.texture_complexity * 0.2 +
            min(self.compositional_elements / 10, 1.0) * 0.2 +
            self.movement_potential * 0.1
        )


@dataclass
class EnergyProfile:
    """Energy profile of an image or sequence."""
    visual_energy: float  # 0-1 overall energy
    brightness_energy: float  # 0-1 luminance
    color_energy: float  # 0-1 saturation/vibrancy
    motion_energy: float  # 0-1 implied movement
    emotional_energy: float  # 0-1 emotional intensity

    @property
    def total_energy(self) -> float:
        """Calculate total energy score."""
        return (
            self.visual_energy * 0.3 +
            self.brightness_energy * 0.2 +
            self.color_energy * 0.2 +
            self.motion_energy * 0.2 +
            self.emotional_energy * 0.1
        )


@dataclass
class PacingSuggestion:
    """Suggested pacing for a shot."""
    hold_duration: float  # Suggested duration in seconds
    complexity_score: float  # Visual complexity
    energy_score: float  # Energy level
    cut_style: str  # "quick", "standard", "long", "hold"
    reasoning: str  # Why this duration was suggested


@dataclass
class RhythmAnalysis:
    """Complete rhythm analysis for a sequence."""
    shot_complexities: list[VisualComplexity]
    shot_energies: list[EnergyProfile]
    pacing_suggestions: list[PacingSuggestion]
    rhythm_curve: list[float]  # Normalized pacing curve
    energy_curve: list[float]  # Energy over time
    balance_score: float  # How well balanced the sequence is

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "shots": [
                {
                    "complexity": s.overall_complexity,
                    "energy": e.total_energy,
                    "suggested_duration": p.hold_duration,
                    "cut_style": p.cut_style
                }
                for s, e, p in zip(
                    self.shot_complexities,
                    self.shot_energies,
                    self.pacing_suggestions, strict=False
                )
            ],
            "rhythm_curve": self.rhythm_curve,
            "energy_curve": self.energy_curve,
            "balance_score": self.balance_score,
            "total_duration": sum(p.hold_duration for p in self.pacing_suggestions)
        }


class VisualRhythmAnalyzer:
    """Analyzes visual rhythm and suggests pacing."""

    def __init__(self):
        """Initialize rhythm analyzer."""
        self.base_duration = 2.0  # Base shot duration
        self.complexity_multiplier = 1.5  # How much complexity affects duration

    def analyze_sequence_rhythm(
        self,
        images: list[str],
        target_duration: float | None = None,
        music_bpm: float | None = None
    ) -> RhythmAnalysis:
        """
        Analyze rhythm of an image sequence.

        Args:
            images: List of image paths
            target_duration: Target total duration in seconds
            music_bpm: Music tempo for rhythm matching

        Returns:
            RhythmAnalysis with pacing suggestions
        """
        # Analyze each image
        complexities = []
        energies = []

        for img_path in images:
            complexity = self._analyze_complexity(img_path)
            energy = self._analyze_energy(img_path)
            complexities.append(complexity)
            energies.append(energy)

        # Generate pacing suggestions
        pacing = self._suggest_pacing(
            complexities, energies, target_duration, music_bpm
        )

        # Create rhythm curves
        rhythm_curve = self._create_rhythm_curve(pacing)
        energy_curve = [e.total_energy for e in energies]

        # Calculate balance
        balance = self._calculate_balance(pacing, energies)

        return RhythmAnalysis(
            shot_complexities=complexities,
            shot_energies=energies,
            pacing_suggestions=pacing,
            rhythm_curve=rhythm_curve,
            energy_curve=energy_curve,
            balance_score=balance
        )

    def _analyze_complexity(self, image_path: str) -> VisualComplexity:
        """Analyze visual complexity of an image."""
        img = cv2.imread(str(image_path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = img.shape[:2]

        # Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)

        # Color variance
        img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        color_std = np.std(img_lab.reshape(-1, 3), axis=0)
        color_variance = np.mean(color_std) / 128.0  # Normalize

        # Texture complexity using local binary patterns
        texture = self._analyze_texture(gray)

        # Compositional elements using connected components
        _, labels = cv2.connectedComponents(edges)
        num_elements = min(len(np.unique(labels)) - 1, 20)  # Cap at 20

        # Movement potential from directional edges
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)  # type: ignore
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)  # type: ignore
        movement = np.mean(np.sqrt(sobelx**2 + sobely**2)) / 255.0

        return VisualComplexity(
            edge_density=min(edge_density * 5, 1.0),
            color_variance=min(color_variance * 2, 1.0),
            texture_complexity=texture,
            compositional_elements=num_elements,
            movement_potential=min(movement * 3, 1.0)
        )

    def _analyze_energy(self, image_path: str) -> EnergyProfile:
        """Analyze energy profile of an image."""
        img = cv2.imread(str(image_path))
        cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Brightness energy
        brightness = np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)) / 255.0
        brightness_energy = self._energy_curve(brightness)

        # Color energy (saturation)
        saturation = np.mean(hsv[:, :, 1]) / 255.0
        color_energy = saturation

        # Motion energy (from blur detection)
        blur_score = cv2.Laplacian(
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F  # type: ignore
        ).var()
        motion_energy = 1.0 - min(blur_score / 1000, 1.0)  # Inverse blur

        # Emotional energy (warm vs cool colors)
        avg_hue = np.mean(hsv[:, :, 0])
        if 0 <= avg_hue <= 30 or 150 <= avg_hue <= 180:  # Reds
            emotional_base = 0.8
        elif 30 <= avg_hue <= 90:  # Yellows/Greens
            emotional_base = 0.5
        else:  # Blues
            emotional_base = 0.3
        emotional_energy = emotional_base * saturation

        # Visual energy (combination)
        visual_energy = (
            brightness_energy * 0.3 +
            color_energy * 0.3 +
            motion_energy * 0.2 +
            emotional_energy * 0.2
        )

        return EnergyProfile(
            visual_energy=visual_energy,
            brightness_energy=brightness_energy,
            color_energy=color_energy,
            motion_energy=motion_energy,
            emotional_energy=emotional_energy
        )

    def _analyze_texture(self, gray: np.ndarray) -> float:
        """Analyze texture complexity using frequency analysis."""
        # Use FFT to analyze frequency content
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shift)

        # High frequency content indicates texture
        h, w = gray.shape
        center_h, center_w = h // 2, w // 2

        # Measure high frequency energy
        high_freq_mask = np.zeros_like(magnitude)
        cv2.circle(
            high_freq_mask,
            (center_w, center_h),
            min(h, w) // 4,
            1.0, -1
        )
        high_freq_mask = 1 - high_freq_mask

        high_freq_energy = np.sum(magnitude * high_freq_mask)
        total_energy = np.sum(magnitude)

        texture_score = high_freq_energy / (total_energy + 1e-6)
        return min(texture_score * 10, 1.0)

    # TODO: Review unreachable code - def _suggest_pacing(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - complexities: list[VisualComplexity],
    # TODO: Review unreachable code - energies: list[EnergyProfile],
    # TODO: Review unreachable code - target_duration: float | None,
    # TODO: Review unreachable code - music_bpm: float | None
    # TODO: Review unreachable code - ) -> list[PacingSuggestion]:
    # TODO: Review unreachable code - """Suggest pacing for each shot."""
    # TODO: Review unreachable code - suggestions = []

    # TODO: Review unreachable code - # Calculate beat duration if BPM provided
    # TODO: Review unreachable code - beat_duration = 60.0 / music_bpm if music_bpm else None

    # TODO: Review unreachable code - # Base durations on complexity
    # TODO: Review unreachable code - base_durations = []
    # TODO: Review unreachable code - for complexity, energy in zip(complexities, energies, strict=False):
    # TODO: Review unreachable code - # More complex shots need more time
    # TODO: Review unreachable code - complexity_factor = 1.0 + (complexity.overall_complexity * self.complexity_multiplier)

    # TODO: Review unreachable code - # High energy shots can be shorter
    # TODO: Review unreachable code - energy_factor = 1.0 - (energy.total_energy * 0.3)

    # TODO: Review unreachable code - duration = self.base_duration * complexity_factor * energy_factor

    # TODO: Review unreachable code - # Snap to beat grid if BPM provided
    # TODO: Review unreachable code - if beat_duration:
    # TODO: Review unreachable code - beats = max(1, round(duration / beat_duration))
    # TODO: Review unreachable code - duration = beats * beat_duration

    # TODO: Review unreachable code - base_durations.append(duration)

    # TODO: Review unreachable code - # Adjust to target duration if provided
    # TODO: Review unreachable code - if target_duration:
    # TODO: Review unreachable code - current_total = sum(base_durations)
    # TODO: Review unreachable code - scale_factor = target_duration / current_total
    # TODO: Review unreachable code - base_durations = [d * scale_factor for d in base_durations]

    # TODO: Review unreachable code - # Create suggestions
    # TODO: Review unreachable code - for i, (duration, complexity, energy) in enumerate(
    # TODO: Review unreachable code - zip(base_durations, complexities, energies, strict=False)
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - # Determine cut style
    # TODO: Review unreachable code - if duration < 1.0:
    # TODO: Review unreachable code - cut_style = "quick"
    # TODO: Review unreachable code - reasoning = "High energy, low complexity - quick cut"
    # TODO: Review unreachable code - elif duration < 2.5:
    # TODO: Review unreachable code - cut_style = "standard"
    # TODO: Review unreachable code - reasoning = "Balanced complexity and energy"
    # TODO: Review unreachable code - elif duration < 4.0:
    # TODO: Review unreachable code - cut_style = "long"
    # TODO: Review unreachable code - reasoning = "Complex shot needs time to read"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - cut_style = "hold"
    # TODO: Review unreachable code - reasoning = "Very complex or establishing shot"

    # TODO: Review unreachable code - suggestion = PacingSuggestion(
    # TODO: Review unreachable code - hold_duration=duration,
    # TODO: Review unreachable code - complexity_score=complexity.overall_complexity,
    # TODO: Review unreachable code - energy_score=energy.total_energy,
    # TODO: Review unreachable code - cut_style=cut_style,
    # TODO: Review unreachable code - reasoning=reasoning
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - suggestions.append(suggestion)

    # TODO: Review unreachable code - return suggestions

    # TODO: Review unreachable code - def _create_rhythm_curve(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - pacing: list[PacingSuggestion]
    # TODO: Review unreachable code - ) -> list[float]:
    # TODO: Review unreachable code - """Create normalized rhythm curve from pacing."""
    # TODO: Review unreachable code - if not pacing:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - # Convert durations to rhythm values (inverse)
    # TODO: Review unreachable code - rhythm_values = [1.0 / p.hold_duration for p in pacing]

    # TODO: Review unreachable code - # Normalize to 0-1
    # TODO: Review unreachable code - min_rhythm = min(rhythm_values)
    # TODO: Review unreachable code - max_rhythm = max(rhythm_values)
    # TODO: Review unreachable code - range_rhythm = max_rhythm - min_rhythm

    # TODO: Review unreachable code - if range_rhythm > 0:
    # TODO: Review unreachable code - normalized = [(r - min_rhythm) / range_rhythm for r in rhythm_values]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - normalized = [0.5] * len(rhythm_values)

    # TODO: Review unreachable code - # Smooth the curve
    # TODO: Review unreachable code - if len(normalized) > 3:
    # TODO: Review unreachable code - window = signal.windows.hann(3)
    # TODO: Review unreachable code - smoothed = signal.convolve(normalized, window, mode='same')
    # TODO: Review unreachable code - smoothed /= np.sum(window)
    # TODO: Review unreachable code - return smoothed.tolist()

    # TODO: Review unreachable code - return normalized

    # TODO: Review unreachable code - def _calculate_balance(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - pacing: list[PacingSuggestion],
    # TODO: Review unreachable code - energies: list[EnergyProfile]
    # TODO: Review unreachable code - ) -> float:
    # TODO: Review unreachable code - """Calculate rhythm balance score."""
    # TODO: Review unreachable code - if len(pacing) < 2:
    # TODO: Review unreachable code - return 1.0

    # TODO: Review unreachable code - # Check pacing variety
    # TODO: Review unreachable code - durations = [p.hold_duration for p in pacing]
    # TODO: Review unreachable code - duration_std = np.std(durations)
    # TODO: Review unreachable code - duration_mean = np.mean(durations)
    # TODO: Review unreachable code - pacing_variety = min(duration_std / duration_mean, 1.0) if duration_mean > 0 else 0

    # TODO: Review unreachable code - # Check energy distribution
    # TODO: Review unreachable code - energy_values = [e.total_energy for e in energies]
    # TODO: Review unreachable code - energy_std = np.std(energy_values)
    # TODO: Review unreachable code - energy_variety = min(energy_std * 2, 1.0)

    # TODO: Review unreachable code - # Check for rhythm patterns (alternating fast/slow)
    # TODO: Review unreachable code - rhythm_changes = 0
    # TODO: Review unreachable code - for i in range(1, len(durations)):
    # TODO: Review unreachable code - if (durations[i] > duration_mean) != (durations[i-1] > duration_mean):
    # TODO: Review unreachable code - rhythm_changes += 1

    # TODO: Review unreachable code - pattern_score = rhythm_changes / (len(durations) - 1)

    # TODO: Review unreachable code - # Combine scores
    # TODO: Review unreachable code - balance = (
    # TODO: Review unreachable code - pacing_variety * 0.3 +
    # TODO: Review unreachable code - energy_variety * 0.3 +
    # TODO: Review unreachable code - pattern_score * 0.4
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return balance

    # TODO: Review unreachable code - def _energy_curve(self, value: float) -> float:
    # TODO: Review unreachable code - """Apply energy curve transformation."""
    # TODO: Review unreachable code - # S-curve for more dramatic energy differences
    # TODO: Review unreachable code - return 1 / (1 + np.exp(-10 * (value - 0.5)))


def match_rhythm_to_music(
    visual_rhythm: RhythmAnalysis,
    music_energy: list[float],
    music_beats: list[float]
) -> dict[str, Any]:
    """
    Match visual rhythm to music energy and beats.

    Args:
        visual_rhythm: Visual rhythm analysis
        music_energy: Energy values over time
        music_beats: Beat timestamps

    Returns:
        Matched rhythm with cut points
    """
    suggestions = []

    # Resample music energy to match shot count
    shot_count = len(visual_rhythm.pacing_suggestions)

    if len(music_energy) != shot_count:
        # Resample music energy
        x_old = np.linspace(0, 1, len(music_energy))
        x_new = np.linspace(0, 1, shot_count)
        music_energy_resampled = np.interp(x_new, x_old, music_energy)
    else:
        music_energy_resampled = music_energy

    # Match high energy music to high energy visuals
    for i, (visual_e, music_e, pacing) in enumerate(zip(
        visual_rhythm.shot_energies,
        music_energy_resampled,
        visual_rhythm.pacing_suggestions, strict=False
    )):
        # Adjust duration based on music energy match
        energy_match = 1.0 - abs(visual_e.total_energy - music_e)

        # Good matches can hold longer
        duration_multiplier = 0.8 + (energy_match * 0.4)
        adjusted_duration = pacing.hold_duration * duration_multiplier

        # Find nearest beat
        if music_beats:
            cumulative_time = sum(s["duration"] for s in suggestions)
            nearest_beat_idx = np.argmin(
                np.abs(np.array(music_beats) - (cumulative_time + adjusted_duration))
            )
            adjusted_duration = music_beats[nearest_beat_idx] - cumulative_time

        suggestions.append({
            "shot_index": i,
            "duration": max(0.5, adjusted_duration),  # Minimum 0.5s
            "visual_energy": visual_e.total_energy,
            "music_energy": music_e,
            "match_score": energy_match
        })

    return {
        "matched_cuts": suggestions,
        "total_duration": sum(s["duration"] for s in suggestions),
        "average_match_score": np.mean([s["match_score"] for s in suggestions])
    }


def export_rhythm_analysis(
    analysis: RhythmAnalysis,
    output_path: Path,
    format: str = "json"
) -> None:
    """Export rhythm analysis for editing software."""

    if format == "json":
        with open(output_path, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)

    elif format == "csv":
        # Export as CSV for spreadsheet analysis
        with open(output_path, 'w') as f:
            f.write("shot,complexity,energy,duration,style,reasoning\n")

            for i, (c, e, p) in enumerate(zip(
                analysis.shot_complexities,
                analysis.shot_energies,
                analysis.pacing_suggestions, strict=False
            )):
                f.write(f"{i},{c.overall_complexity:.3f},{e.total_energy:.3f},")
                f.write(f"{p.hold_duration:.2f},{p.cut_style},\"{p.reasoning}\"\n")
