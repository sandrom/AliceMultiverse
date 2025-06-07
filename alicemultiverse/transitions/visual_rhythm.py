"""
Visual rhythm analysis for pacing and energy matching.

Analyzes visual complexity, energy levels, and pacing to create
rhythmic video edits that match musical or narrative flow.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import cv2
import json
from scipy import signal

from ..core.types import ImagePath
from ..core.logging import get_logger

logger = get_logger(__name__)


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
    shot_complexities: List[VisualComplexity]
    shot_energies: List[EnergyProfile]
    pacing_suggestions: List[PacingSuggestion]
    rhythm_curve: List[float]  # Normalized pacing curve
    energy_curve: List[float]  # Energy over time
    balance_score: float  # How well balanced the sequence is
    
    def to_dict(self) -> Dict[str, Any]:
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
                    self.pacing_suggestions
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
        images: List[ImagePath],
        target_duration: Optional[float] = None,
        music_bpm: Optional[float] = None
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
    
    def _analyze_complexity(self, image_path: ImagePath) -> VisualComplexity:
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
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        movement = np.mean(np.sqrt(sobelx**2 + sobely**2)) / 255.0
        
        return VisualComplexity(
            edge_density=min(edge_density * 5, 1.0),
            color_variance=min(color_variance * 2, 1.0),
            texture_complexity=texture,
            compositional_elements=num_elements,
            movement_potential=min(movement * 3, 1.0)
        )
    
    def _analyze_energy(self, image_path: ImagePath) -> EnergyProfile:
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
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F
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
    
    def _suggest_pacing(
        self,
        complexities: List[VisualComplexity],
        energies: List[EnergyProfile],
        target_duration: Optional[float],
        music_bpm: Optional[float]
    ) -> List[PacingSuggestion]:
        """Suggest pacing for each shot."""
        suggestions = []
        
        # Calculate beat duration if BPM provided
        beat_duration = 60.0 / music_bpm if music_bpm else None
        
        # Base durations on complexity
        base_durations = []
        for complexity, energy in zip(complexities, energies):
            # More complex shots need more time
            complexity_factor = 1.0 + (complexity.overall_complexity * self.complexity_multiplier)
            
            # High energy shots can be shorter
            energy_factor = 1.0 - (energy.total_energy * 0.3)
            
            duration = self.base_duration * complexity_factor * energy_factor
            
            # Snap to beat grid if BPM provided
            if beat_duration:
                beats = max(1, round(duration / beat_duration))
                duration = beats * beat_duration
            
            base_durations.append(duration)
        
        # Adjust to target duration if provided
        if target_duration:
            current_total = sum(base_durations)
            scale_factor = target_duration / current_total
            base_durations = [d * scale_factor for d in base_durations]
        
        # Create suggestions
        for i, (duration, complexity, energy) in enumerate(
            zip(base_durations, complexities, energies)
        ):
            # Determine cut style
            if duration < 1.0:
                cut_style = "quick"
                reasoning = "High energy, low complexity - quick cut"
            elif duration < 2.5:
                cut_style = "standard"
                reasoning = "Balanced complexity and energy"
            elif duration < 4.0:
                cut_style = "long"
                reasoning = "Complex shot needs time to read"
            else:
                cut_style = "hold"
                reasoning = "Very complex or establishing shot"
            
            suggestion = PacingSuggestion(
                hold_duration=duration,
                complexity_score=complexity.overall_complexity,
                energy_score=energy.total_energy,
                cut_style=cut_style,
                reasoning=reasoning
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _create_rhythm_curve(
        self,
        pacing: List[PacingSuggestion]
    ) -> List[float]:
        """Create normalized rhythm curve from pacing."""
        if not pacing:
            return []
        
        # Convert durations to rhythm values (inverse)
        rhythm_values = [1.0 / p.hold_duration for p in pacing]
        
        # Normalize to 0-1
        min_rhythm = min(rhythm_values)
        max_rhythm = max(rhythm_values)
        range_rhythm = max_rhythm - min_rhythm
        
        if range_rhythm > 0:
            normalized = [(r - min_rhythm) / range_rhythm for r in rhythm_values]
        else:
            normalized = [0.5] * len(rhythm_values)
        
        # Smooth the curve
        if len(normalized) > 3:
            window = signal.windows.hann(3)
            smoothed = signal.convolve(normalized, window, mode='same')
            smoothed /= np.sum(window)
            return smoothed.tolist()
        
        return normalized
    
    def _calculate_balance(
        self,
        pacing: List[PacingSuggestion],
        energies: List[EnergyProfile]
    ) -> float:
        """Calculate rhythm balance score."""
        if len(pacing) < 2:
            return 1.0
        
        # Check pacing variety
        durations = [p.hold_duration for p in pacing]
        duration_std = np.std(durations)
        duration_mean = np.mean(durations)
        pacing_variety = min(duration_std / duration_mean, 1.0) if duration_mean > 0 else 0
        
        # Check energy distribution
        energy_values = [e.total_energy for e in energies]
        energy_std = np.std(energy_values)
        energy_variety = min(energy_std * 2, 1.0)
        
        # Check for rhythm patterns (alternating fast/slow)
        rhythm_changes = 0
        for i in range(1, len(durations)):
            if (durations[i] > duration_mean) != (durations[i-1] > duration_mean):
                rhythm_changes += 1
        
        pattern_score = rhythm_changes / (len(durations) - 1)
        
        # Combine scores
        balance = (
            pacing_variety * 0.3 +
            energy_variety * 0.3 +
            pattern_score * 0.4
        )
        
        return balance
    
    def _energy_curve(self, value: float) -> float:
        """Apply energy curve transformation."""
        # S-curve for more dramatic energy differences
        return 1 / (1 + np.exp(-10 * (value - 0.5)))


def match_rhythm_to_music(
    visual_rhythm: RhythmAnalysis,
    music_energy: List[float],
    music_beats: List[float]
) -> Dict[str, Any]:
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
        visual_rhythm.pacing_suggestions
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
                analysis.pacing_suggestions
            )):
                f.write(f"{i},{c.overall_complexity:.3f},{e.total_energy:.3f},")
                f.write(f"{p.hold_duration:.2f},{p.cut_style},\"{p.reasoning}\"\n")