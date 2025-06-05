"""Music analysis for video synchronization.

This module analyzes audio tracks to extract beat information, mood,
and timing data for synchronized video creation.
"""

import logging
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import librosa
import librosa.display
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BeatInfo:
    """Beat detection information."""
    
    tempo: float  # BPM
    beats: List[float] = field(default_factory=list)  # Beat timestamps
    downbeats: List[float] = field(default_factory=list)  # Measure starts
    beat_strength: List[float] = field(default_factory=list)  # Beat emphasis
    time_signature: Tuple[int, int] = (4, 4)  # Beats per measure


@dataclass
class MusicMood:
    """Music mood analysis."""
    
    energy: float = 0.5  # 0-1 scale
    valence: float = 0.5  # 0-1 scale (sad to happy)
    intensity: float = 0.5  # 0-1 scale
    mood_tags: List[str] = field(default_factory=list)
    dominant_mood: str = "neutral"
    
    def get_mood_category(self) -> str:
        """Get simplified mood category."""
        if self.energy > 0.7 and self.valence > 0.6:
            return "upbeat"
        elif self.energy < 0.4 and self.valence < 0.4:
            return "melancholic"
        elif self.energy > 0.7 and self.valence < 0.4:
            return "intense"
        elif self.energy < 0.4 and self.valence > 0.6:
            return "peaceful"
        else:
            return "neutral"


@dataclass
class MusicSection:
    """A section of music with consistent characteristics."""
    
    start_time: float
    end_time: float
    section_type: str  # intro, verse, chorus, bridge, outro
    energy_level: float
    suggested_pace: str  # slow, medium, fast
    beat_count: int


@dataclass
class MusicAnalysis:
    """Complete music analysis for video sync."""
    
    file_path: str
    duration: float
    beat_info: BeatInfo
    mood: MusicMood
    sections: List[MusicSection] = field(default_factory=list)
    key_moments: List[float] = field(default_factory=list)  # Timestamps for emphasis
    suggested_cut_points: List[float] = field(default_factory=list)
    scene_durations: Dict[str, float] = field(default_factory=dict)


class MusicAnalyzer:
    """Analyzes music for video synchronization."""
    
    def __init__(self):
        """Initialize music analyzer."""
        self.default_fps = 30  # For frame-accurate timing
        
    async def analyze_audio(self, audio_path: Path) -> MusicAnalysis:
        """Analyze audio file for video synchronization.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Complete music analysis
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Extract features
            beat_info = self._analyze_beats(y, sr)
            mood = self._analyze_mood(y, sr)
            sections = self._analyze_sections(y, sr, beat_info)
            key_moments = self._find_key_moments(y, sr)
            
            # Generate cut points
            cut_points = self._generate_cut_points(
                beat_info, sections, key_moments, duration
            )
            
            # Calculate scene durations
            scene_durations = self._calculate_scene_durations(
                beat_info, mood, duration
            )
            
            return MusicAnalysis(
                file_path=str(audio_path),
                duration=duration,
                beat_info=beat_info,
                mood=mood,
                sections=sections,
                key_moments=key_moments,
                suggested_cut_points=cut_points,
                scene_durations=scene_durations
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze audio {audio_path}: {e}")
            # Return minimal analysis on error
            return MusicAnalysis(
                file_path=str(audio_path),
                duration=0,
                beat_info=BeatInfo(tempo=120),
                mood=MusicMood()
            )
    
    def _analyze_beats(self, y: np.ndarray, sr: int) -> BeatInfo:
        """Analyze beat structure of audio."""
        # Get tempo and beats
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        # Get beat strength
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        beat_strength = onset_env[beats].tolist() if len(beats) > 0 else []
        
        # Normalize beat strength
        if beat_strength:
            max_strength = max(beat_strength)
            if max_strength > 0:
                beat_strength = [s / max_strength for s in beat_strength]
        
        # Estimate downbeats (simplified - every 4 beats)
        downbeats = []
        if len(beat_times) > 4:
            for i in range(0, len(beat_times), 4):
                downbeats.append(beat_times[i])
        
        return BeatInfo(
            tempo=float(tempo),
            beats=beat_times.tolist(),
            downbeats=downbeats,
            beat_strength=beat_strength
        )
    
    def _analyze_mood(self, y: np.ndarray, sr: int) -> MusicMood:
        """Analyze mood characteristics of audio."""
        # Extract features for mood analysis
        
        # Energy: RMS energy
        rms = librosa.feature.rms(y=y)[0]
        energy = float(np.mean(rms))
        energy = min(energy * 10, 1.0)  # Normalize to 0-1
        
        # Intensity: Spectral rolloff (brightness)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        intensity = float(np.mean(rolloff) / sr)
        intensity = min(intensity * 4, 1.0)  # Normalize
        
        # Valence: Approximated by mode (major/minor) and tempo
        # This is simplified - real valence detection is complex
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        # Major thirds (C-E, F-A, G-B) vs minor thirds
        major_weight = np.mean([chroma[0] * chroma[4], chroma[5] * chroma[9], chroma[7] * chroma[11]])
        minor_weight = np.mean([chroma[0] * chroma[3], chroma[5] * chroma[8], chroma[7] * chroma[10]])
        valence = 0.5 + (major_weight - minor_weight) * 2
        valence = max(0, min(1, valence))
        
        mood = MusicMood(
            energy=energy,
            valence=valence,
            intensity=intensity
        )
        
        # Generate mood tags
        mood_tags = []
        if energy > 0.7:
            mood_tags.append("energetic")
        elif energy < 0.3:
            mood_tags.append("calm")
        
        if valence > 0.7:
            mood_tags.append("happy")
        elif valence < 0.3:
            mood_tags.append("sad")
        
        if intensity > 0.7:
            mood_tags.append("intense")
        elif intensity < 0.3:
            mood_tags.append("soft")
        
        mood.mood_tags = mood_tags
        mood.dominant_mood = mood.get_mood_category()
        
        return mood
    
    def _analyze_sections(self, y: np.ndarray, sr: int, 
                         beat_info: BeatInfo) -> List[MusicSection]:
        """Analyze musical sections."""
        # Use structural features to segment
        sections = []
        
        # Get segment boundaries using spectral clustering
        mfcc = librosa.feature.mfcc(y=y, sr=sr)
        bounds = librosa.segment.agglomerative(mfcc, k=7)
        bound_times = librosa.frames_to_time(bounds, sr=sr)
        
        # Analyze each section
        for i in range(len(bound_times) - 1):
            start = bound_times[i]
            end = bound_times[i + 1]
            
            # Get section of audio
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            section_audio = y[start_sample:end_sample]
            
            # Calculate energy level
            if len(section_audio) > 0:
                rms = librosa.feature.rms(y=section_audio)[0]
                energy_level = float(np.mean(rms)) * 10
                energy_level = min(energy_level, 1.0)
            else:
                energy_level = 0.5
            
            # Determine section type (simplified)
            if i == 0:
                section_type = "intro"
            elif i == len(bound_times) - 2:
                section_type = "outro"
            elif energy_level > 0.7:
                section_type = "chorus"
            elif energy_level < 0.4:
                section_type = "bridge"
            else:
                section_type = "verse"
            
            # Suggested pace based on energy
            if energy_level > 0.7:
                suggested_pace = "fast"
            elif energy_level < 0.4:
                suggested_pace = "slow"
            else:
                suggested_pace = "medium"
            
            # Count beats in section
            beats_in_section = sum(
                1 for beat in beat_info.beats 
                if start <= beat <= end
            )
            
            sections.append(MusicSection(
                start_time=float(start),
                end_time=float(end),
                section_type=section_type,
                energy_level=energy_level,
                suggested_pace=suggested_pace,
                beat_count=beats_in_section
            ))
        
        return sections
    
    def _find_key_moments(self, y: np.ndarray, sr: int) -> List[float]:
        """Find key moments for emphasis (drops, builds, etc)."""
        key_moments = []
        
        # Detect onset peaks (sudden changes)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(
            onset_env, pre_max=3, post_max=3, 
            pre_avg=3, post_avg=5, delta=0.3, wait=10
        )
        peak_times = librosa.frames_to_time(peaks, sr=sr)
        
        # Add significant peaks as key moments
        if len(peak_times) > 0:
            # Take top 20% strongest peaks
            peak_strengths = [(onset_env[p], t) for p, t in zip(peaks, peak_times)]
            peak_strengths.sort(reverse=True)
            n_key = max(1, len(peak_strengths) // 5)
            
            for strength, time in peak_strengths[:n_key]:
                key_moments.append(float(time))
        
        return sorted(key_moments)
    
    def _generate_cut_points(self, beat_info: BeatInfo, 
                           sections: List[MusicSection],
                           key_moments: List[float],
                           duration: float) -> List[float]:
        """Generate suggested cut points for video editing."""
        cut_points = []
        
        # Add section boundaries
        for section in sections:
            cut_points.append(section.start_time)
        
        # Add downbeats for major cuts
        cut_points.extend(beat_info.downbeats)
        
        # Add key moments
        cut_points.extend(key_moments)
        
        # Add regular beats for fast sections
        for section in sections:
            if section.suggested_pace == "fast":
                # Add every 2nd beat in fast sections
                section_beats = [
                    b for b in beat_info.beats 
                    if section.start_time <= b <= section.end_time
                ]
                cut_points.extend(section_beats[::2])
            elif section.suggested_pace == "medium":
                # Add every 4th beat in medium sections
                section_beats = [
                    b for b in beat_info.beats 
                    if section.start_time <= b <= section.end_time
                ]
                cut_points.extend(section_beats[::4])
        
        # Remove duplicates and sort
        cut_points = sorted(list(set(cut_points)))
        
        # Filter out cuts too close together (minimum 0.5 seconds)
        filtered_cuts = []
        last_cut = -1
        for cut in cut_points:
            if cut - last_cut >= 0.5:
                filtered_cuts.append(cut)
                last_cut = cut
        
        return filtered_cuts
    
    def _calculate_scene_durations(self, beat_info: BeatInfo, 
                                 mood: MusicMood, 
                                 duration: float) -> Dict[str, float]:
        """Calculate suggested scene durations based on tempo and mood."""
        # Base duration on tempo
        beat_duration = 60.0 / beat_info.tempo if beat_info.tempo > 0 else 0.5
        
        # Adjust for mood
        mood_multiplier = {
            "upbeat": 0.75,      # Faster cuts
            "melancholic": 1.5,  # Slower, contemplative
            "intense": 0.6,      # Very fast cuts
            "peaceful": 2.0,     # Long, peaceful shots
            "neutral": 1.0
        }.get(mood.dominant_mood, 1.0)
        
        return {
            "minimum": beat_duration * mood_multiplier,
            "short": beat_duration * 2 * mood_multiplier,
            "medium": beat_duration * 4 * mood_multiplier,
            "long": beat_duration * 8 * mood_multiplier,
            "maximum": beat_duration * 16 * mood_multiplier,
            "recommended": beat_duration * 4 * mood_multiplier
        }
    
    def match_images_to_mood(self, music_analysis: MusicAnalysis,
                           image_moods: Dict[str, List[str]]) -> List[Tuple[str, float, float]]:
        """Match images to music sections based on mood.
        
        Args:
            music_analysis: Analyzed music
            image_moods: Dict mapping image paths to mood tags
            
        Returns:
            List of (image_path, start_time, end_time) tuples
        """
        matches = []
        
        # Group images by dominant mood
        mood_groups = defaultdict(list)
        for image, moods in image_moods.items():
            # Find best matching mood category
            if "energetic" in moods or "vibrant" in moods:
                mood_groups["upbeat"].append(image)
            elif "dark" in moods or "melancholic" in moods:
                mood_groups["melancholic"].append(image)
            elif "dramatic" in moods or "intense" in moods:
                mood_groups["intense"].append(image)
            elif "peaceful" in moods or "serene" in moods:
                mood_groups["peaceful"].append(image)
            else:
                mood_groups["neutral"].append(image)
        
        # Match sections to images
        for section in music_analysis.sections:
            # Determine section mood
            if section.energy_level > 0.7:
                section_mood = "upbeat" if music_analysis.mood.valence > 0.5 else "intense"
            elif section.energy_level < 0.4:
                section_mood = "peaceful" if music_analysis.mood.valence > 0.5 else "melancholic"
            else:
                section_mood = "neutral"
            
            # Get matching images
            available_images = mood_groups.get(section_mood, [])
            if not available_images:
                available_images = mood_groups.get("neutral", [])
            
            if available_images:
                # Distribute images across section
                section_duration = section.end_time - section.start_time
                if len(available_images) > 0:
                    time_per_image = section_duration / len(available_images)
                    
                    for i, image in enumerate(available_images):
                        start = section.start_time + i * time_per_image
                        end = start + time_per_image
                        matches.append((image, start, end))
        
        return matches
    
    def create_rhythm_timeline(self, music_analysis: MusicAnalysis,
                             target_duration: Optional[float] = None) -> Dict[str, Any]:
        """Create a rhythm-based timeline for video editing.
        
        Args:
            music_analysis: Analyzed music
            target_duration: Target video duration (uses music duration if None)
            
        Returns:
            Timeline with cut points and timing info
        """
        duration = target_duration or music_analysis.duration
        
        timeline = {
            "duration": duration,
            "fps": self.default_fps,
            "tempo": music_analysis.beat_info.tempo,
            "time_signature": music_analysis.beat_info.time_signature,
            "cuts": [],
            "sections": []
        }
        
        # Add cuts with timing
        for i, cut_time in enumerate(music_analysis.suggested_cut_points):
            if cut_time > duration:
                break
                
            # Determine cut type based on what it aligns with
            if cut_time in music_analysis.beat_info.downbeats:
                cut_type = "downbeat"
                strength = 1.0
            elif cut_time in music_analysis.key_moments:
                cut_type = "key_moment"
                strength = 0.9
            elif cut_time in music_analysis.beat_info.beats:
                cut_type = "beat"
                idx = music_analysis.beat_info.beats.index(cut_time)
                strength = music_analysis.beat_info.beat_strength[idx] if idx < len(music_analysis.beat_info.beat_strength) else 0.5
            else:
                cut_type = "section"
                strength = 0.7
            
            timeline["cuts"].append({
                "time": cut_time,
                "frame": int(cut_time * self.default_fps),
                "type": cut_type,
                "strength": strength
            })
        
        # Add section info
        for section in music_analysis.sections:
            if section.start_time < duration:
                timeline["sections"].append({
                    "start": section.start_time,
                    "end": min(section.end_time, duration),
                    "type": section.section_type,
                    "pace": section.suggested_pace,
                    "energy": section.energy_level,
                    "beat_count": section.beat_count
                })
        
        return timeline