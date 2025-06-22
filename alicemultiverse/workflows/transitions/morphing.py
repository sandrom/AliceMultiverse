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

        subjects = []

        # Get AI analysis if no metadata provided
        if not metadata:
            try:
                analysis = await self.analyzer.analyze(
                    image_path,
                    extract_tags=True,
                    detect_objects=True
                )
                metadata = analysis
            except Exception as e:
                logger.error(f"Failed to analyze image {image_path}: {e}")
                return subjects

        # Extract subjects from tags and detected objects
        subject_tags = self._extract_subject_tags(metadata)

        # Load image for region detection
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return subjects

            h, w = img.shape[:2]

            # Use simple heuristics for now (can be enhanced with actual object detection)
            for tag in subject_tags:
                # Create regions based on tag type and image analysis
                region = self._create_subject_region(tag, img, metadata)
                if region:
                    subjects.append(region)

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")

        # Cache results
        self._subject_cache[image_path] = subjects
        return subjects

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

    def generate_morph_keyframes(
        self,
        subject_pairs: list[tuple[SubjectRegion, SubjectRegion]],
        duration: float,
        morph_type: str = "smooth",
        keyframe_count: int = 10
    ) -> list[MorphKeyframe]:
        """
        Generate keyframes for morphing animation.

        Args:
            subject_pairs: Matched subject pairs
            duration: Transition duration in seconds
            morph_type: Type of morph animation
            keyframe_count: Number of keyframes to generate

        Returns:
            List of morph keyframes
        """
        keyframes = []

        # Get interpolation function
        curve_func = self.MORPH_CURVES.get(
            morph_type,
            self.MORPH_CURVES["ease-in-out"]
        )

        # Generate keyframes for each subject pair
        for source, target in subject_pairs:
            # Calculate morph path
            path_keyframes = self._generate_morph_path(
                source, target, duration, keyframe_count, curve_func
            )
            keyframes.extend(path_keyframes)

        # Sort by time
        keyframes.sort(key=lambda k: k.time)

        return keyframes

    def create_morph_transition(
        self,
        source_path: str,
        target_path: str,
        source_subjects: list[SubjectRegion],
        target_subjects: list[SubjectRegion],
        duration: float = 1.2,
        morph_type: str = "smooth"
    ) -> MorphTransition | None:
        """
        Create a complete morph transition between two images.

        Args:
            source_path: Path to source image
            target_path: Path to target image
            source_subjects: Subjects in source image
            target_subjects: Subjects in target image
            duration: Transition duration
            morph_type: Type of morphing animation

        Returns:
            MorphTransition object or None if no matches found
        """
        # Find matching subjects
        subject_pairs = self.find_similar_subjects(source_subjects, target_subjects)

        if not subject_pairs:
            logger.info("No matching subjects found for morphing")
            return None

        # Generate keyframes
        keyframes = self.generate_morph_keyframes(
            subject_pairs, duration, morph_type
        )

        return MorphTransition(
            source_image=source_path,
            target_image=target_path,
            duration=duration,
            subject_pairs=subject_pairs,
            keyframes=keyframes,
            morph_type=morph_type
        )

    def export_for_after_effects(
        self,
        morph_transition: MorphTransition,
        output_path: str,
        fps: float = 30.0
    ) -> dict[str, Any]:
        """
        Export morph data in After Effects compatible format.

        Args:
            morph_transition: Morph transition data
            output_path: Path for output file
            fps: Frames per second for keyframe timing

        Returns:
            Export summary
        """
        # Convert to After Effects keyframe format
        ae_data = {
            "version": "1.0",
            "project": {
                "fps": fps,
                "duration": morph_transition.duration,
                "source_layer": Path(morph_transition.source_image).name,
                "target_layer": Path(morph_transition.target_image).name
            },
            "morph_data": []
        }

        # Convert each subject pair to AE format
        for i, (source, target) in enumerate(morph_transition.subject_pairs):
            morph_layer = {
                "name": f"Morph_{source.label}_{i}",
                "source_anchor": self._to_ae_coordinates(source.center),
                "target_anchor": self._to_ae_coordinates(target.center),
                "mask_data": {
                    "source": self._bbox_to_mask(source.bbox),
                    "target": self._bbox_to_mask(target.bbox)
                },
                "keyframes": []
            }

            # Convert keyframes
            for kf in morph_transition.keyframes:
                ae_keyframe = {
                    "time": kf.time * fps,  # Convert to frames
                    "position": self._to_ae_coordinates(kf.target_point),
                    "opacity": kf.opacity * 100,  # AE uses 0-100
                    "scale": [kf.scale * 100, kf.scale * 100],  # X, Y scale
                    "rotation": kf.rotation
                }

                if kf.control_points:
                    ae_keyframe["bezier_handles"] = [
                        self._to_ae_coordinates(cp) for cp in kf.control_points
                    ]

                morph_layer["keyframes"].append(ae_keyframe)

            ae_data["morph_data"].append(morph_layer)

        # Add expression controls
        ae_data["expressions"] = self._generate_ae_expressions(morph_transition)

        # Save to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(ae_data, f, indent=2)

        # Also save a .jsx script for direct import
        jsx_path = output_file.with_suffix('.jsx')
        jsx_content = self._generate_jsx_script(ae_data)

        with open(jsx_path, 'w') as f:
            f.write(jsx_content)

        return {
            "json_path": str(output_file),
            "jsx_path": str(jsx_path),
            "subject_count": len(morph_transition.subject_pairs),
            "keyframe_count": len(morph_transition.keyframes),
            "duration": morph_transition.duration
        }

    def _extract_subject_tags(self, metadata: AssetMetadata) -> list[str]:
        """Extract subject-related tags from metadata."""
        subject_keywords = {
            "person", "people", "face", "portrait", "man", "woman", "child",
            "cat", "dog", "animal", "pet", "bird", "horse",
            "car", "vehicle", "building", "tree", "flower"
        }

        subject_tags = []

        if hasattr(metadata, 'tags'):
            tags = metadata.tags
            if isinstance(tags, dict):
                # Flatten categorized tags
                all_tags = []
                for category_tags in tags.values():
                    all_tags.extend(category_tags)
            else:
                all_tags = tags

            # Find subject-related tags
            for tag in all_tags:
                tag_lower = tag.lower()
                if any(keyword in tag_lower for keyword in subject_keywords):
                    subject_tags.append(tag)

        return subject_tags

    def _create_subject_region(
        self,
        tag: str,
        image: np.ndarray,
        metadata: AssetMetadata
    ) -> SubjectRegion | None:
        """Create a subject region based on tag and image analysis."""
        h, w = image.shape[:2]

        # Simple heuristic regions based on tag type
        # In a real implementation, this would use object detection
        tag_lower = tag.lower()

        # Default to center region
        bbox = (0.25, 0.25, 0.5, 0.5)  # Center 50% of image

        if "face" in tag_lower or "portrait" in tag_lower:
            # Faces typically in upper center
            bbox = (0.3, 0.1, 0.4, 0.4)
        elif "person" in tag_lower or "people" in tag_lower:
            # Full person typically takes more vertical space
            bbox = (0.2, 0.1, 0.6, 0.8)
        elif tag_lower is not None and "landscape" in tag_lower:
            # Landscape subjects often span horizontally
            bbox = (0.0, 0.3, 1.0, 0.4)

        # Calculate center and area
        x, y, w_box, h_box = bbox
        center = (x + w_box / 2, y + h_box / 2)
        area = w_box * h_box

        return SubjectRegion(
            label=tag,
            confidence=0.8,  # Default confidence
            bbox=bbox,
            center=center,
            area=area
        )

    def _calculate_subject_similarity(
        self,
        source: SubjectRegion,
        target: SubjectRegion
    ) -> float:
        """Calculate similarity score between two subjects."""
        score = 0.0

        # Label similarity (exact match or related)
        if source.label == target.label:
            score += 0.5
        elif self._are_labels_related(source.label, target.label):
            score += 0.3

        # Spatial similarity (position and size)
        position_dist = np.linalg.norm(
            np.array(source.center) - np.array(target.center)
        )
        position_score = max(0, 1 - position_dist)
        score += position_score * 0.3

        # Size similarity
        size_ratio = min(source.area, target.area) / max(source.area, target.area)
        score += size_ratio * 0.2

        return min(score, 1.0)

    def _are_labels_related(self, label1: str, label2: str) -> bool:
        """Check if two labels are semantically related."""
        # Define related label groups
        related_groups = [
            {"person", "people", "man", "woman", "child", "face", "portrait"},
            {"cat", "kitten", "feline"},
            {"dog", "puppy", "canine"},
            {"car", "vehicle", "automobile"},
            {"tree", "forest", "woods"},
            {"flower", "plant", "flora"}
        ]

        label1_lower = label1.lower()
        label2_lower = label2.lower()

        for group in related_groups:
            if label1_lower in group and label2_lower in group:
                return True

        return False

    def _generate_morph_path(
        self,
        source: SubjectRegion,
        target: SubjectRegion,
        duration: float,
        keyframe_count: int,
        curve_func
    ) -> list[MorphKeyframe]:
        """Generate morph path keyframes between two subjects."""
        keyframes = []

        for i in range(keyframe_count):
            t = i / (keyframe_count - 1)  # Normalized time (0-1)
            time = t * duration

            # Apply curve function
            curved_t = curve_func(t)

            # Interpolate position
            source_pos = np.array(source.center)
            target_pos = np.array(target.center)
            current_pos = source_pos + (target_pos - source_pos) * curved_t

            # Calculate scale based on area difference
            source_scale = np.sqrt(source.area)
            target_scale = np.sqrt(target.area)
            current_scale = source_scale + (target_scale - source_scale) * curved_t

            # Add some rotation for interest (optional)
            rotation = 0.0
            if source.label != target.label:
                # Add slight rotation when morphing between different subjects
                rotation = np.sin(t * np.pi) * 15  # Max 15 degrees

            # Create keyframe
            keyframe = MorphKeyframe(
                time=time,
                source_point=tuple(source_pos),
                target_point=tuple(current_pos),
                opacity=1.0,
                scale=current_scale / source_scale,  # Relative to source
                rotation=rotation
            )

            # Add bezier control points for smooth curves
            if 0 < i < keyframe_count - 1:
                # Calculate tangent for smooth bezier curves
                prev_pos = source_pos + (target_pos - source_pos) * curve_func((i-1) / (keyframe_count - 1))
                next_pos = source_pos + (target_pos - source_pos) * curve_func((i+1) / (keyframe_count - 1))

                tangent = (next_pos - prev_pos) / 2
                control1 = current_pos - tangent * 0.3
                control2 = current_pos + tangent * 0.3

                keyframe.control_points = [tuple(control1), tuple(control2)]

            keyframes.append(keyframe)

        return keyframes

    def _to_ae_coordinates(self, point: tuple[float, float]) -> list[float]:
        """Convert normalized coordinates to After Effects coordinates."""
        # AE uses comp dimensions, typically 1920x1080
        # This should be configurable based on actual comp size
        ae_width = 1920
        ae_height = 1080

        return [point[0] * ae_width, point[1] * ae_height]

    def _bbox_to_mask(self, bbox: tuple[float, float, float, float]) -> dict[str, Any]:
        """Convert bounding box to After Effects mask data."""
        x, y, w, h = bbox

        # Create mask points (clockwise from top-left)
        points = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

        # Convert to AE coordinates
        ae_points = [self._to_ae_coordinates(p) for p in points]

        return {
            "vertices": ae_points,
            "inTangents": [[0, 0]] * 4,  # No bezier curves for rect
            "outTangents": [[0, 0]] * 4,
            "closed": True
        }

    def _generate_ae_expressions(self, transition: MorphTransition) -> dict[str, str]:
        """Generate After Effects expressions for advanced control."""
        expressions = {}

        # Time remapping expression
        expressions["time_remap"] = """
// Morph timing control
transitionStart = 0;
transitionEnd = %.2f;
progress = linear(time, transitionStart, transitionEnd, 0, 1);
easeProgress = ease(progress, 0, 1);
easeProgress;
""" % transition.duration

        # Morph amount expression
        if expressions is not None:
            expressions["morph_amount"] = """
// Control morph intensity
maxMorph = 100;
morphCurve = thisComp.layer("Control").effect("Morph Curve")("Slider");
progress = thisComp.layer("Control").effect("Progress")("Slider");
morphAmount = progress * maxMorph * morphCurve / 100;
morphAmount;
"""
        
        # Auto-orient expression
        if expressions is not None:
            expressions["auto_orient"] = """
// Auto-orient based on motion direction
prevPos = transform.position.valueAtTime(time - 0.1);
currPos = transform.position;
direction = currPos - prevPos;
angle = Math.atan2(direction[1], direction[0]) * 180 / Math.PI;
angle + value;
"""

        return expressions

    def _generate_jsx_script(self, ae_data: dict[str, Any]) -> str:
        """Generate JSX script for After Effects import."""
        jsx_template = """
// Alice Multiverse - Subject Morph Import Script
// Generated morph transition data

function importMorphData() {
    var data = %s;

    // Get active composition
    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) {
        alert("Please select a composition first");
        return;
    }

    // Create null object for control
    var controlNull = comp.layers.addNull();
    controlNull.name = "Morph Control";

    // Add slider controls
    var progressSlider = controlNull.Effects.addProperty("ADBE Slider Control");
    progressSlider.name = "Progress";
    progressSlider.property("Slider").setValueAtTime(0, 0);
    progressSlider.property("Slider").setValueAtTime(data.project.duration, 100);

    var curveSlider = controlNull.Effects.addProperty("ADBE Slider Control");
    curveSlider.name = "Morph Curve";
    curveSlider.property("Slider").setValue(100);

    // Process each morph layer
    for (var i = 0; i < data.morph_data.length; i++) {
        var morphData = data.morph_data[i];
        createMorphLayer(comp, morphData, controlNull);
    }

    alert("Morph data imported successfully!");
}

function createMorphLayer(comp, morphData, controlNull) {
    // Create shape layer for morph
    var morphLayer = comp.layers.addShape();
    morphLayer.name = morphData.name;

    // Add mask shape
    var shapeGroup = morphLayer.property("Contents").addProperty("ADBE Vector Group");
    var maskPath = shapeGroup.property("Contents").addProperty("ADBE Vector Shape - Group");

    // Set mask vertices
    var path = maskPath.property("Path");
    var shape = new Shape();
    shape.vertices = morphData.mask_data.source.vertices;
    shape.inTangents = morphData.mask_data.source.inTangents;
    shape.outTangents = morphData.mask_data.source.outTangents;
    shape.closed = morphData.mask_data.source.closed;
    path.setValue(shape);

    // Add keyframes
    for (var j = 0; j < morphData.keyframes.length; j++) {
        var kf = morphData.keyframes[j];
        var time = kf.time / %.1f; // Convert frames to seconds

        morphLayer.transform.position.setValueAtTime(time, kf.position);
        morphLayer.transform.opacity.setValueAtTime(time, kf.opacity);
        morphLayer.transform.scale.setValueAtTime(time, kf.scale);
        morphLayer.transform.rotation.setValueAtTime(time, kf.rotation);
    }

    // Link to control null
    morphLayer.parent = controlNull;
}

// Run the import
importMorphData();
""" % (json.dumps(ae_data), ae_data["project"]["fps"])

        return jsx_template


class MorphingTransitionMatcher:
    """Enhanced transition matcher with morphing support."""

    def __init__(self):
        """Initialize the morphing transition matcher."""
        self.morpher = SubjectMorpher()

    async def analyze_for_morphing(
        self,
        image_paths: list[str],
        min_similarity: float = 0.6
    ) -> list[MorphTransition]:
        """
        Analyze image sequence for potential morphing transitions.

        Args:
            image_paths: List of image paths in sequence
            min_similarity: Minimum similarity score for morphing

        Returns:
            List of morph transitions
        """
        transitions = []

        # Detect subjects in all images
        all_subjects = []
        for path in image_paths:
            subjects = await self.morpher.detect_subjects(path)
            all_subjects.append((path, subjects))

        # Find morphing opportunities
        for i in range(len(all_subjects) - 1):
            source_path, source_subjects = all_subjects[i]
            target_path, target_subjects = all_subjects[i + 1]

            if source_subjects and target_subjects:
                # Try to create morph transition
                morph = self.morpher.create_morph_transition(
                    source_path,
                    target_path,
                    source_subjects,
                    target_subjects
                )

                if morph and len(morph.subject_pairs) > 0:
                    transitions.append(morph)

        return transitions

    def suggest_morph_transition(
        self,
        source_path: str,
        target_path: str,
        source_subjects: list[SubjectRegion],
        target_subjects: list[SubjectRegion]
    ) -> TransitionSuggestion | None:
        """
        Create a transition suggestion with morphing.

        Args:
            source_path: Source image path
            target_path: Target image path
            source_subjects: Subjects in source
            target_subjects: Subjects in target

        Returns:
            Transition suggestion or None
        """
        morph = self.morpher.create_morph_transition(
            source_path,
            target_path,
            source_subjects,
            target_subjects
        )

        if not morph:
            return None

        # Calculate confidence based on match quality
        confidence = len(morph.subject_pairs) / max(
            len(source_subjects),
            len(target_subjects)
        )

        return TransitionSuggestion(
            source_image=source_path,
            target_image=target_path,
            transition_type=TransitionType.MORPH,
            duration=morph.duration,
            effects={
                "morph_data": morph.to_dict(),
                "subject_count": len(morph.subject_pairs),
                "morph_type": morph.morph_type
            },
            confidence=confidence
        )
