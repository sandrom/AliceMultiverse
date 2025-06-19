"""
Subject morphing for smooth transitions between similar subjects.

This module detects similar subjects across shots and generates morph keyframes
for smooth transitions, with export support for After Effects.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np

from ...assets.metadata.models import AssetMetadata
from ...understanding.analyzer import ImageAnalyzer
from .models import TransitionSuggestion, TransitionType

logger = logging.getLogger(__name__)


@dataclass
class SubjectRegion:
    """Represents a detected subject region in an image."""
    label: str  # Subject type (e.g., "person", "face", "cat", "car")
    confidence: float  # Detection confidence
    bbox: tuple[float, float, float, float]  # Normalized x, y, w, h (0-1)
    center: tuple[float, float]  # Normalized center point
    area: float  # Normalized area (0-1)
    features: dict[str, Any] | None = None  # Additional features


@dataclass
class MorphKeyframe:
    """Keyframe data for morphing animation."""
    time: float  # Time in seconds
    source_point: tuple[float, float]  # Normalized coordinates
    target_point: tuple[float, float]  # Target coordinates
    control_points: list[tuple[float, float]] | None = None  # Bezier control points
    opacity: float = 1.0
    scale: float = 1.0
    rotation: float = 0.0


@dataclass
class MorphTransition:
    """Complete morph transition data."""
    source_image: str
    target_image: str
    duration: float
    subject_pairs: list[tuple[SubjectRegion, SubjectRegion]]  # Matched subjects
    keyframes: list[MorphKeyframe]
    transition_curve: str = "ease-in-out"  # Animation curve type
    morph_type: str = "smooth"  # smooth, elastic, bounce

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "source_image": self.source_image,
            "target_image": self.target_image,
            "duration": self.duration,
            "subject_pairs": [
                {
                    "source": asdict(source),
                    "target": asdict(target)
                }
                for source, target in self.subject_pairs
            ],
            "keyframes": [asdict(kf) for kf in self.keyframes],
            "transition_curve": self.transition_curve,
            "morph_type": self.morph_type
        }


class SubjectMorpher:
    """Handles subject detection and morphing keyframe generation."""

    # Subject similarity thresholds
    SIMILARITY_THRESHOLDS = {
        "person": 0.7,
        "face": 0.8,
        "animal": 0.6,
        "object": 0.5,
        "default": 0.6
    }

    # Morph timing curves
    MORPH_CURVES = {
        "linear": lambda t: t,
        "ease-in": lambda t: t * t,
        "ease-out": lambda t: 1 - (1 - t) ** 2,
        "ease-in-out": lambda t: 3 * t**2 - 2 * t**3,
        "elastic": lambda t: t + 0.1 * np.sin(t * np.pi * 4) * (1 - t),
        "bounce": lambda t: t + 0.15 * np.sin(t * np.pi * 3) * (1 - t) if t < 0.9 else t
    }

    def __init__(self):
        """Initialize the subject morpher."""
        self.analyzer = ImageAnalyzer()
        self._subject_cache = {}

    async def detect_subjects(
        self,
        image_path: str,
        metadata: AssetMetadata | None = None
    ) -> list[SubjectRegion]:
        """
        Detect subjects in an image using AI analysis.

        Args:
            image_path: Path to the image
            metadata: Optional existing metadata

        Returns:
            List of detected subject regions
        """
        # Check cache
        if image_path in self._subject_cache:
            return self._subject_cache[image_path]

        # TODO: Review unreachable code - subjects = []

        # TODO: Review unreachable code - # Get AI analysis if no metadata provided
        # TODO: Review unreachable code - if not metadata:
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - analysis = await self.analyzer.analyze(
        # TODO: Review unreachable code - image_path,
        # TODO: Review unreachable code - extract_tags=True,
        # TODO: Review unreachable code - detect_objects=True
        # TODO: Review unreachable code - )
        # TODO: Review unreachable code - metadata = analysis
        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Failed to analyze image {image_path}: {e}")
        # TODO: Review unreachable code - return subjects

        # TODO: Review unreachable code - # Extract subjects from tags and detected objects
        # TODO: Review unreachable code - subject_tags = self._extract_subject_tags(metadata)

        # TODO: Review unreachable code - # Load image for region detection
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - img = cv2.imread(str(image_path))
        # TODO: Review unreachable code - if img is None:
        # TODO: Review unreachable code - logger.error(f"Failed to load image: {image_path}")
        # TODO: Review unreachable code - return subjects

        # TODO: Review unreachable code - h, w = img.shape[:2]

        # TODO: Review unreachable code - # Use simple heuristics for now (can be enhanced with actual object detection)
        # TODO: Review unreachable code - for tag in subject_tags:
        # TODO: Review unreachable code - # Create regions based on tag type and image analysis
        # TODO: Review unreachable code - region = self._create_subject_region(tag, img, metadata)
        # TODO: Review unreachable code - if region:
        # TODO: Review unreachable code - subjects.append(region)

        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - logger.error(f"Error processing image {image_path}: {e}")

        # TODO: Review unreachable code - # Cache results
        # TODO: Review unreachable code - self._subject_cache[image_path] = subjects
        # TODO: Review unreachable code - return subjects

    def find_similar_subjects(
        self,
        source_subjects: list[SubjectRegion],
        target_subjects: list[SubjectRegion]
    ) -> list[tuple[SubjectRegion, SubjectRegion]]:
        """
        Find matching subjects between two images.

        Args:
            source_subjects: Subjects from source image
            target_subjects: Subjects from target image

        Returns:
            List of matched subject pairs
        """
        matches = []
        used_targets = set()

        for source in source_subjects:
            best_match = None
            best_score = 0.0

            for i, target in enumerate(target_subjects):
                if i in used_targets:
                    continue

                # Calculate similarity score
                score = self._calculate_subject_similarity(source, target)

                # Check threshold
                threshold = self.SIMILARITY_THRESHOLDS.get(
                    source.label,
                    self.SIMILARITY_THRESHOLDS["default"]
                )

                if score > threshold and score > best_score:
                    best_match = (target, i)
                    best_score = score

            if best_match:
                matches.append((source, best_match[0]))
                used_targets.add(best_match[1])

        return matches

    # TODO: Review unreachable code - def generate_morph_keyframes(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - subject_pairs: list[tuple[SubjectRegion, SubjectRegion]],
    # TODO: Review unreachable code - duration: float,
    # TODO: Review unreachable code - morph_type: str = "smooth",
    # TODO: Review unreachable code - keyframe_count: int = 10
    # TODO: Review unreachable code - ) -> list[MorphKeyframe]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Generate keyframes for morphing animation.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - subject_pairs: Matched subject pairs
    # TODO: Review unreachable code - duration: Transition duration in seconds
    # TODO: Review unreachable code - morph_type: Type of morph animation
    # TODO: Review unreachable code - keyframe_count: Number of keyframes to generate

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of morph keyframes
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - keyframes = []

    # TODO: Review unreachable code - # Get interpolation function
    # TODO: Review unreachable code - curve_func = self.MORPH_CURVES.get(
    # TODO: Review unreachable code - morph_type,
    # TODO: Review unreachable code - self.MORPH_CURVES["ease-in-out"]
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Generate keyframes for each subject pair
    # TODO: Review unreachable code - for source, target in subject_pairs:
    # TODO: Review unreachable code - # Calculate morph path
    # TODO: Review unreachable code - path_keyframes = self._generate_morph_path(
    # TODO: Review unreachable code - source, target, duration, keyframe_count, curve_func
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - keyframes.extend(path_keyframes)

    # TODO: Review unreachable code - # Sort by time
    # TODO: Review unreachable code - keyframes.sort(key=lambda k: k.time)

    # TODO: Review unreachable code - return keyframes

    # TODO: Review unreachable code - def create_morph_transition(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - source_path: str,
    # TODO: Review unreachable code - target_path: str,
    # TODO: Review unreachable code - source_subjects: list[SubjectRegion],
    # TODO: Review unreachable code - target_subjects: list[SubjectRegion],
    # TODO: Review unreachable code - duration: float = 1.2,
    # TODO: Review unreachable code - morph_type: str = "smooth"
    # TODO: Review unreachable code - ) -> MorphTransition | None:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Create a complete morph transition between two images.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - source_path: Path to source image
    # TODO: Review unreachable code - target_path: Path to target image
    # TODO: Review unreachable code - source_subjects: Subjects in source image
    # TODO: Review unreachable code - target_subjects: Subjects in target image
    # TODO: Review unreachable code - duration: Transition duration
    # TODO: Review unreachable code - morph_type: Type of morphing animation

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - MorphTransition object or None if no matches found
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Find matching subjects
    # TODO: Review unreachable code - subject_pairs = self.find_similar_subjects(source_subjects, target_subjects)

    # TODO: Review unreachable code - if not subject_pairs:
    # TODO: Review unreachable code - logger.info("No matching subjects found for morphing")
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - # Generate keyframes
    # TODO: Review unreachable code - keyframes = self.generate_morph_keyframes(
    # TODO: Review unreachable code - subject_pairs, duration, morph_type
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return MorphTransition(
    # TODO: Review unreachable code - source_image=source_path,
    # TODO: Review unreachable code - target_image=target_path,
    # TODO: Review unreachable code - duration=duration,
    # TODO: Review unreachable code - subject_pairs=subject_pairs,
    # TODO: Review unreachable code - keyframes=keyframes,
    # TODO: Review unreachable code - morph_type=morph_type
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def export_for_after_effects(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - morph_transition: MorphTransition,
    # TODO: Review unreachable code - output_path: str,
    # TODO: Review unreachable code - fps: float = 30.0
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Export morph data in After Effects compatible format.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - morph_transition: Morph transition data
    # TODO: Review unreachable code - output_path: Path for output file
    # TODO: Review unreachable code - fps: Frames per second for keyframe timing

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Export summary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Convert to After Effects keyframe format
    # TODO: Review unreachable code - ae_data = {
    # TODO: Review unreachable code - "version": "1.0",
    # TODO: Review unreachable code - "project": {
    # TODO: Review unreachable code - "fps": fps,
    # TODO: Review unreachable code - "duration": morph_transition.duration,
    # TODO: Review unreachable code - "source_layer": Path(morph_transition.source_image).name,
    # TODO: Review unreachable code - "target_layer": Path(morph_transition.target_image).name
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - "morph_data": []
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Convert each subject pair to AE format
    # TODO: Review unreachable code - for i, (source, target) in enumerate(morph_transition.subject_pairs):
    # TODO: Review unreachable code - morph_layer = {
    # TODO: Review unreachable code - "name": f"Morph_{source.label}_{i}",
    # TODO: Review unreachable code - "source_anchor": self._to_ae_coordinates(source.center),
    # TODO: Review unreachable code - "target_anchor": self._to_ae_coordinates(target.center),
    # TODO: Review unreachable code - "mask_data": {
    # TODO: Review unreachable code - "source": self._bbox_to_mask(source.bbox),
    # TODO: Review unreachable code - "target": self._bbox_to_mask(target.bbox)
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - "keyframes": []
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Convert keyframes
    # TODO: Review unreachable code - for kf in morph_transition.keyframes:
    # TODO: Review unreachable code - ae_keyframe = {
    # TODO: Review unreachable code - "time": kf.time * fps,  # Convert to frames
    # TODO: Review unreachable code - "position": self._to_ae_coordinates(kf.target_point),
    # TODO: Review unreachable code - "opacity": kf.opacity * 100,  # AE uses 0-100
    # TODO: Review unreachable code - "scale": [kf.scale * 100, kf.scale * 100],  # X, Y scale
    # TODO: Review unreachable code - "rotation": kf.rotation
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - if kf.control_points:
    # TODO: Review unreachable code - ae_keyframe["bezier_handles"] = [
    # TODO: Review unreachable code - self._to_ae_coordinates(cp) for cp in kf.control_points
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - morph_layer["keyframes"].append(ae_keyframe)

    # TODO: Review unreachable code - ae_data["morph_data"].append(morph_layer)

    # TODO: Review unreachable code - # Add expression controls
    # TODO: Review unreachable code - ae_data["expressions"] = self._generate_ae_expressions(morph_transition)

    # TODO: Review unreachable code - # Save to file
    # TODO: Review unreachable code - output_file = Path(output_path)
    # TODO: Review unreachable code - output_file.parent.mkdir(parents=True, exist_ok=True)

    # TODO: Review unreachable code - with open(output_file, 'w') as f:
    # TODO: Review unreachable code - json.dump(ae_data, f, indent=2)

    # TODO: Review unreachable code - # Also save a .jsx script for direct import
    # TODO: Review unreachable code - jsx_path = output_file.with_suffix('.jsx')
    # TODO: Review unreachable code - jsx_content = self._generate_jsx_script(ae_data)

    # TODO: Review unreachable code - with open(jsx_path, 'w') as f:
    # TODO: Review unreachable code - f.write(jsx_content)

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "json_path": str(output_file),
    # TODO: Review unreachable code - "jsx_path": str(jsx_path),
    # TODO: Review unreachable code - "subject_count": len(morph_transition.subject_pairs),
    # TODO: Review unreachable code - "keyframe_count": len(morph_transition.keyframes),
    # TODO: Review unreachable code - "duration": morph_transition.duration
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def _extract_subject_tags(self, metadata: AssetMetadata) -> list[str]:
    # TODO: Review unreachable code - """Extract subject-related tags from metadata."""
    # TODO: Review unreachable code - subject_keywords = {
    # TODO: Review unreachable code - "person", "people", "face", "portrait", "man", "woman", "child",
    # TODO: Review unreachable code - "cat", "dog", "animal", "pet", "bird", "horse",
    # TODO: Review unreachable code - "car", "vehicle", "building", "tree", "flower"
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - subject_tags = []

    # TODO: Review unreachable code - if hasattr(metadata, 'tags'):
    # TODO: Review unreachable code - tags = metadata.tags
    # TODO: Review unreachable code - if isinstance(tags, dict):
    # TODO: Review unreachable code - # Flatten categorized tags
    # TODO: Review unreachable code - all_tags = []
    # TODO: Review unreachable code - for category_tags in tags.values():
    # TODO: Review unreachable code - all_tags.extend(category_tags)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - all_tags = tags

    # TODO: Review unreachable code - # Find subject-related tags
    # TODO: Review unreachable code - for tag in all_tags:
    # TODO: Review unreachable code - tag_lower = tag.lower()
    # TODO: Review unreachable code - if any(keyword in tag_lower for keyword in subject_keywords):
    # TODO: Review unreachable code - subject_tags.append(tag)

    # TODO: Review unreachable code - return subject_tags

    # TODO: Review unreachable code - def _create_subject_region(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - tag: str,
    # TODO: Review unreachable code - image: np.ndarray,
    # TODO: Review unreachable code - metadata: AssetMetadata
    # TODO: Review unreachable code - ) -> SubjectRegion | None:
    # TODO: Review unreachable code - """Create a subject region based on tag and image analysis."""
    # TODO: Review unreachable code - h, w = image.shape[:2]

    # TODO: Review unreachable code - # Simple heuristic regions based on tag type
    # TODO: Review unreachable code - # In a real implementation, this would use object detection
    # TODO: Review unreachable code - tag_lower = tag.lower()

    # TODO: Review unreachable code - # Default to center region
    # TODO: Review unreachable code - bbox = (0.25, 0.25, 0.5, 0.5)  # Center 50% of image

    # TODO: Review unreachable code - if "face" in tag_lower or "portrait" in tag_lower:
    # TODO: Review unreachable code - # Faces typically in upper center
    # TODO: Review unreachable code - bbox = (0.3, 0.1, 0.4, 0.4)
    # TODO: Review unreachable code - elif "person" in tag_lower or "people" in tag_lower:
    # TODO: Review unreachable code - # Full person typically takes more vertical space
    # TODO: Review unreachable code - bbox = (0.2, 0.1, 0.6, 0.8)
    # TODO: Review unreachable code - elif tag_lower is not None and "landscape" in tag_lower:
    # TODO: Review unreachable code - # Landscape subjects often span horizontally
    # TODO: Review unreachable code - bbox = (0.0, 0.3, 1.0, 0.4)

    # TODO: Review unreachable code - # Calculate center and area
    # TODO: Review unreachable code - x, y, w_box, h_box = bbox
    # TODO: Review unreachable code - center = (x + w_box / 2, y + h_box / 2)
    # TODO: Review unreachable code - area = w_box * h_box

    # TODO: Review unreachable code - return SubjectRegion(
    # TODO: Review unreachable code - label=tag,
    # TODO: Review unreachable code - confidence=0.8,  # Default confidence
    # TODO: Review unreachable code - bbox=bbox,
    # TODO: Review unreachable code - center=center,
    # TODO: Review unreachable code - area=area
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _calculate_subject_similarity(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - source: SubjectRegion,
    # TODO: Review unreachable code - target: SubjectRegion
    # TODO: Review unreachable code - ) -> float:
    # TODO: Review unreachable code - """Calculate similarity score between two subjects."""
    # TODO: Review unreachable code - score = 0.0

    # TODO: Review unreachable code - # Label similarity (exact match or related)
    # TODO: Review unreachable code - if source.label == target.label:
    # TODO: Review unreachable code - score += 0.5
    # TODO: Review unreachable code - elif self._are_labels_related(source.label, target.label):
    # TODO: Review unreachable code - score += 0.3

    # TODO: Review unreachable code - # Spatial similarity (position and size)
    # TODO: Review unreachable code - position_dist = np.linalg.norm(
    # TODO: Review unreachable code - np.array(source.center) - np.array(target.center)
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - position_score = max(0, 1 - position_dist)
    # TODO: Review unreachable code - score += position_score * 0.3

    # TODO: Review unreachable code - # Size similarity
    # TODO: Review unreachable code - size_ratio = min(source.area, target.area) / max(source.area, target.area)
    # TODO: Review unreachable code - score += size_ratio * 0.2

    # TODO: Review unreachable code - return min(score, 1.0)

    # TODO: Review unreachable code - def _are_labels_related(self, label1: str, label2: str) -> bool:
    # TODO: Review unreachable code - """Check if two labels are semantically related."""
    # TODO: Review unreachable code - # Define related label groups
    # TODO: Review unreachable code - related_groups = [
    # TODO: Review unreachable code - {"person", "people", "man", "woman", "child", "face", "portrait"},
    # TODO: Review unreachable code - {"cat", "kitten", "feline"},
    # TODO: Review unreachable code - {"dog", "puppy", "canine"},
    # TODO: Review unreachable code - {"car", "vehicle", "automobile"},
    # TODO: Review unreachable code - {"tree", "forest", "woods"},
    # TODO: Review unreachable code - {"flower", "plant", "flora"}
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - label1_lower = label1.lower()
    # TODO: Review unreachable code - label2_lower = label2.lower()

    # TODO: Review unreachable code - for group in related_groups:
    # TODO: Review unreachable code - if label1_lower in group and label2_lower in group:
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - def _generate_morph_path(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - source: SubjectRegion,
    # TODO: Review unreachable code - target: SubjectRegion,
    # TODO: Review unreachable code - duration: float,
    # TODO: Review unreachable code - keyframe_count: int,
    # TODO: Review unreachable code - curve_func
    # TODO: Review unreachable code - ) -> list[MorphKeyframe]:
    # TODO: Review unreachable code - """Generate morph path keyframes between two subjects."""
    # TODO: Review unreachable code - keyframes = []

    # TODO: Review unreachable code - for i in range(keyframe_count):
    # TODO: Review unreachable code - t = i / (keyframe_count - 1)  # Normalized time (0-1)
    # TODO: Review unreachable code - time = t * duration

    # TODO: Review unreachable code - # Apply curve function
    # TODO: Review unreachable code - curved_t = curve_func(t)

    # TODO: Review unreachable code - # Interpolate position
    # TODO: Review unreachable code - source_pos = np.array(source.center)
    # TODO: Review unreachable code - target_pos = np.array(target.center)
    # TODO: Review unreachable code - current_pos = source_pos + (target_pos - source_pos) * curved_t

    # TODO: Review unreachable code - # Calculate scale based on area difference
    # TODO: Review unreachable code - source_scale = np.sqrt(source.area)
    # TODO: Review unreachable code - target_scale = np.sqrt(target.area)
    # TODO: Review unreachable code - current_scale = source_scale + (target_scale - source_scale) * curved_t

    # TODO: Review unreachable code - # Add some rotation for interest (optional)
    # TODO: Review unreachable code - rotation = 0.0
    # TODO: Review unreachable code - if source.label != target.label:
    # TODO: Review unreachable code - # Add slight rotation when morphing between different subjects
    # TODO: Review unreachable code - rotation = np.sin(t * np.pi) * 15  # Max 15 degrees

    # TODO: Review unreachable code - # Create keyframe
    # TODO: Review unreachable code - keyframe = MorphKeyframe(
    # TODO: Review unreachable code - time=time,
    # TODO: Review unreachable code - source_point=tuple(source_pos),
    # TODO: Review unreachable code - target_point=tuple(current_pos),
    # TODO: Review unreachable code - opacity=1.0,
    # TODO: Review unreachable code - scale=current_scale / source_scale,  # Relative to source
    # TODO: Review unreachable code - rotation=rotation
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Add bezier control points for smooth curves
    # TODO: Review unreachable code - if 0 < i < keyframe_count - 1:
    # TODO: Review unreachable code - # Calculate tangent for smooth bezier curves
    # TODO: Review unreachable code - prev_pos = source_pos + (target_pos - source_pos) * curve_func((i-1) / (keyframe_count - 1))
    # TODO: Review unreachable code - next_pos = source_pos + (target_pos - source_pos) * curve_func((i+1) / (keyframe_count - 1))

    # TODO: Review unreachable code - tangent = (next_pos - prev_pos) / 2
    # TODO: Review unreachable code - control1 = current_pos - tangent * 0.3
    # TODO: Review unreachable code - control2 = current_pos + tangent * 0.3

    # TODO: Review unreachable code - keyframe.control_points = [tuple(control1), tuple(control2)]

    # TODO: Review unreachable code - keyframes.append(keyframe)

    # TODO: Review unreachable code - return keyframes

    # TODO: Review unreachable code - def _to_ae_coordinates(self, point: tuple[float, float]) -> list[float]:
    # TODO: Review unreachable code - """Convert normalized coordinates to After Effects coordinates."""
    # TODO: Review unreachable code - # AE uses comp dimensions, typically 1920x1080
    # TODO: Review unreachable code - # This should be configurable based on actual comp size
    # TODO: Review unreachable code - ae_width = 1920
    # TODO: Review unreachable code - ae_height = 1080

    # TODO: Review unreachable code - return [point[0] * ae_width, point[1] * ae_height]

    # TODO: Review unreachable code - def _bbox_to_mask(self, bbox: tuple[float, float, float, float]) -> dict[str, Any]:
    # TODO: Review unreachable code - """Convert bounding box to After Effects mask data."""
    # TODO: Review unreachable code - x, y, w, h = bbox

    # TODO: Review unreachable code - # Create mask points (clockwise from top-left)
    # TODO: Review unreachable code - points = [
    # TODO: Review unreachable code - [x, y],
    # TODO: Review unreachable code - [x + w, y],
    # TODO: Review unreachable code - [x + w, y + h],
    # TODO: Review unreachable code - [x, y + h]
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - # Convert to AE coordinates
    # TODO: Review unreachable code - ae_points = [self._to_ae_coordinates(p) for p in points]

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "vertices": ae_points,
    # TODO: Review unreachable code - "inTangents": [[0, 0]] * 4,  # No bezier curves for rect
    # TODO: Review unreachable code - "outTangents": [[0, 0]] * 4,
    # TODO: Review unreachable code - "closed": True
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def _generate_ae_expressions(self, transition: MorphTransition) -> dict[str, str]:
    # TODO: Review unreachable code - """Generate After Effects expressions for advanced control."""
    # TODO: Review unreachable code - expressions = {}

    # TODO: Review unreachable code - # Time remapping expression
    # TODO: Review unreachable code - expressions["time_remap"] = """
# TODO: Review unreachable code - // Morph timing control
# TODO: Review unreachable code - transitionStart = 0;
# TODO: Review unreachable code - transitionEnd = %.2f;
# TODO: Review unreachable code - progress = linear(time, transitionStart, transitionEnd, 0, 1);
# TODO: Review unreachable code - easeProgress = ease(progress, 0, 1);
# TODO: Review unreachable code - easeProgress;
# TODO: Review unreachable code - """ % transition.duration

        # TODO: Review unreachable code - # Morph amount expression
        # TODO: Review unreachable code - if expressions is not None:
        # TODO: Review unreachable code -     expressions["morph_amount"] = """
# TODO: Review unreachable code - // Control morph intensity
# TODO: Review unreachable code - maxMorph = 100;
# TODO: Review unreachable code - morphCurve = thisComp.layer("Control").effect("Morph Curve")("Slider");
# TODO: Review unreachable code - progress = thisComp.layer("Control").effect("Progress")("Slider");
# TODO: Review unreachable code - morphAmount = progress * maxMorph * morphCurve / 100;
# TODO: Review unreachable code - morphAmount;
# TODO: Review unreachable code - """
        # TODO: Review unreachable code - 
        # TODO: Review unreachable code - # Auto-orient expression
        # TODO: Review unreachable code - if expressions is not None:
        # TODO: Review unreachable code -     expressions["auto_orient"] = """
# TODO: Review unreachable code - // Auto-orient based on motion direction
# TODO: Review unreachable code - prevPos = transform.position.valueAtTime(time - 0.1);
# TODO: Review unreachable code - currPos = transform.position;
# TODO: Review unreachable code - direction = currPos - prevPos;
# TODO: Review unreachable code - angle = Math.atan2(direction[1], direction[0]) * 180 / Math.PI;
# TODO: Review unreachable code - angle + value;
# TODO: Review unreachable code - """
# TODO: Review unreachable code - 
# TODO: Review unreachable code -         return expressions

    # TODO: Review unreachable code - def _generate_jsx_script(self, ae_data: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """Generate JSX script for After Effects import."""
    # TODO: Review unreachable code - jsx_template = """
# TODO: Review unreachable code - // Alice Multiverse - Subject Morph Import Script
# TODO: Review unreachable code - // Generated morph transition data
# TODO: Review unreachable code - 
# TODO: Review unreachable code - function importMorphData() {
# TODO: Review unreachable code -     var data = %s;
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     // Get active composition
# TODO: Review unreachable code -     var comp = app.project.activeItem;
# TODO: Review unreachable code -     if (!comp || !(comp instanceof CompItem)) {
# TODO: Review unreachable code -         alert("Please select a composition first");
# TODO: Review unreachable code -         return;
# TODO: Review unreachable code -     # TODO: Review unreachable code - }
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     # TODO: Review unreachable code - // Create null object for control
# TODO: Review unreachable code -     # TODO: Review unreachable code - var controlNull = comp.layers.addNull();
# TODO: Review unreachable code -     # TODO: Review unreachable code - controlNull.name = "Morph Control";
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     # TODO: Review unreachable code - // Add slider controls
# TODO: Review unreachable code -     # TODO: Review unreachable code - var progressSlider = controlNull.Effects.addProperty("ADBE Slider Control");
# TODO: Review unreachable code -     # TODO: Review unreachable code - progressSlider.name = "Progress";
# TODO: Review unreachable code -     # TODO: Review unreachable code - progressSlider.property("Slider").setValueAtTime(0, 0);
# TODO: Review unreachable code -     # TODO: Review unreachable code - progressSlider.property("Slider").setValueAtTime(data.project.duration, 100);
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     # TODO: Review unreachable code - var curveSlider = controlNull.Effects.addProperty("ADBE Slider Control");
# TODO: Review unreachable code -     # TODO: Review unreachable code - curveSlider.name = "Morph Curve";
# TODO: Review unreachable code -     # TODO: Review unreachable code - curveSlider.property("Slider").setValue(100);
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     # TODO: Review unreachable code - // Process each morph layer
# TODO: Review unreachable code -     # TODO: Review unreachable code - for (var i = 0; i < data.morph_data.length; i++) {
# TODO: Review unreachable code -     # TODO: Review unreachable code - var morphData = data.morph_data[i];
# TODO: Review unreachable code -     # TODO: Review unreachable code - createMorphLayer(comp, morphData, controlNull);
# TODO: Review unreachable code -     # TODO: Review unreachable code - }
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     # TODO: Review unreachable code - alert("Morph data imported successfully!");
# TODO: Review unreachable code - }
# TODO: Review unreachable code - 
# TODO: Review unreachable code - function createMorphLayer(comp, morphData, controlNull) {
# TODO: Review unreachable code -     // Create shape layer for morph
# TODO: Review unreachable code -     var morphLayer = comp.layers.addShape();
# TODO: Review unreachable code -     morphLayer.name = morphData.name;
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     // Add mask shape
# TODO: Review unreachable code -     var shapeGroup = morphLayer.property("Contents").addProperty("ADBE Vector Group");
# TODO: Review unreachable code -     var maskPath = shapeGroup.property("Contents").addProperty("ADBE Vector Shape - Group");
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     // Set mask vertices
# TODO: Review unreachable code -     var path = maskPath.property("Path");
# TODO: Review unreachable code -     var shape = new Shape();
# TODO: Review unreachable code -     shape.vertices = morphData.mask_data.source.vertices;
# TODO: Review unreachable code -     shape.inTangents = morphData.mask_data.source.inTangents;
# TODO: Review unreachable code -     shape.outTangents = morphData.mask_data.source.outTangents;
# TODO: Review unreachable code -     shape.closed = morphData.mask_data.source.closed;
# TODO: Review unreachable code -     path.setValue(shape);
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     // Add keyframes
# TODO: Review unreachable code -     for (var j = 0; j < morphData.keyframes.length; j++) {
# TODO: Review unreachable code -         var kf = morphData.keyframes[j];
# TODO: Review unreachable code -         var time = kf.time / %.1f; // Convert frames to seconds
# TODO: Review unreachable code - 
# TODO: Review unreachable code -         morphLayer.transform.position.setValueAtTime(time, kf.position);
# TODO: Review unreachable code -         morphLayer.transform.opacity.setValueAtTime(time, kf.opacity);
# TODO: Review unreachable code -         morphLayer.transform.scale.setValueAtTime(time, kf.scale);
# TODO: Review unreachable code -         morphLayer.transform.rotation.setValueAtTime(time, kf.rotation);
# TODO: Review unreachable code -     }
# TODO: Review unreachable code - 
# TODO: Review unreachable code -     // Link to control null
# TODO: Review unreachable code -     morphLayer.parent = controlNull;
# TODO: Review unreachable code - }
# TODO: Review unreachable code - 
# TODO: Review unreachable code - // Run the import
# TODO: Review unreachable code - importMorphData();
# TODO: Review unreachable code - """ % (json.dumps(ae_data), ae_data["project"]["fps"])
# TODO: Review unreachable code - 
# TODO: Review unreachable code -         return jsx_template


# TODO: Review unreachable code - class MorphingTransitionMatcher:
# TODO: Review unreachable code - """Enhanced transition matcher with morphing support."""

# TODO: Review unreachable code - def __init__(self):
# TODO: Review unreachable code - """Initialize the morphing transition matcher."""
# TODO: Review unreachable code - self.morpher = SubjectMorpher()

# TODO: Review unreachable code - async def analyze_for_morphing(
# TODO: Review unreachable code - self,
# TODO: Review unreachable code - image_paths: list[str],
# TODO: Review unreachable code - min_similarity: float = 0.6
# TODO: Review unreachable code - ) -> list[MorphTransition]:
# TODO: Review unreachable code - """
# TODO: Review unreachable code - Analyze image sequence for potential morphing transitions.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - image_paths: List of image paths in sequence
# TODO: Review unreachable code - min_similarity: Minimum similarity score for morphing

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - List of morph transitions
# TODO: Review unreachable code - """
# TODO: Review unreachable code - transitions = []

# TODO: Review unreachable code - # Detect subjects in all images
# TODO: Review unreachable code - all_subjects = []
# TODO: Review unreachable code - for path in image_paths:
# TODO: Review unreachable code - subjects = await self.morpher.detect_subjects(path)
# TODO: Review unreachable code - all_subjects.append((path, subjects))

# TODO: Review unreachable code - # Find morphing opportunities
# TODO: Review unreachable code - for i in range(len(all_subjects) - 1):
# TODO: Review unreachable code - source_path, source_subjects = all_subjects[i]
# TODO: Review unreachable code - target_path, target_subjects = all_subjects[i + 1]

# TODO: Review unreachable code - if source_subjects and target_subjects:
# TODO: Review unreachable code - # Try to create morph transition
# TODO: Review unreachable code - morph = self.morpher.create_morph_transition(
# TODO: Review unreachable code - source_path,
# TODO: Review unreachable code - target_path,
# TODO: Review unreachable code - source_subjects,
# TODO: Review unreachable code - target_subjects
# TODO: Review unreachable code - )

# TODO: Review unreachable code - if morph and len(morph.subject_pairs) > 0:
# TODO: Review unreachable code - transitions.append(morph)

# TODO: Review unreachable code - return transitions

# TODO: Review unreachable code - def suggest_morph_transition(
# TODO: Review unreachable code - self,
# TODO: Review unreachable code - source_path: str,
# TODO: Review unreachable code - target_path: str,
# TODO: Review unreachable code - source_subjects: list[SubjectRegion],
# TODO: Review unreachable code - target_subjects: list[SubjectRegion]
# TODO: Review unreachable code - ) -> TransitionSuggestion | None:
# TODO: Review unreachable code - """
# TODO: Review unreachable code - Create a transition suggestion with morphing.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - source_path: Source image path
# TODO: Review unreachable code - target_path: Target image path
# TODO: Review unreachable code - source_subjects: Subjects in source
# TODO: Review unreachable code - target_subjects: Subjects in target

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Transition suggestion or None
# TODO: Review unreachable code - """
# TODO: Review unreachable code - morph = self.morpher.create_morph_transition(
# TODO: Review unreachable code - source_path,
# TODO: Review unreachable code - target_path,
# TODO: Review unreachable code - source_subjects,
# TODO: Review unreachable code - target_subjects
# TODO: Review unreachable code - )

# TODO: Review unreachable code - if not morph:
# TODO: Review unreachable code - return None

# TODO: Review unreachable code - # Calculate confidence based on match quality
# TODO: Review unreachable code - confidence = len(morph.subject_pairs) / max(
# TODO: Review unreachable code - len(source_subjects),
# TODO: Review unreachable code - len(target_subjects)
# TODO: Review unreachable code - )

# TODO: Review unreachable code - return TransitionSuggestion(
# TODO: Review unreachable code - source_image=source_path,
# TODO: Review unreachable code - target_image=target_path,
# TODO: Review unreachable code - transition_type=TransitionType.MORPH,
# TODO: Review unreachable code - duration=morph.duration,
# TODO: Review unreachable code - effects={
# TODO: Review unreachable code - "morph_data": morph.to_dict(),
# TODO: Review unreachable code - "subject_count": len(morph.subject_pairs),
# TODO: Review unreachable code - "morph_type": morph.morph_type
# TODO: Review unreachable code - },
# TODO: Review unreachable code - confidence=confidence
# TODO: Review unreachable code - )
