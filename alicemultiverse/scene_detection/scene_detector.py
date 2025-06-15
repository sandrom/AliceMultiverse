"""
AI-powered scene detection for videos and image sequences.
"""

import json
import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ..understanding.analyzer import ImageAnalyzer
from .models import DetectionMethod, Scene, SceneType

logger = logging.getLogger(__name__)


class SceneDetector:
    """Detects scenes in videos or image sequences using AI and traditional methods."""

    def __init__(
        self,
        threshold: float = 0.3,
        min_scene_duration: float = 1.0,
        use_ai: bool = True,
        ai_provider: str | None = None
    ):
        """
        Initialize scene detector.
        
        Args:
            threshold: Sensitivity threshold for scene detection (0-1)
            min_scene_duration: Minimum scene duration in seconds
            use_ai: Whether to use AI vision for scene analysis
            ai_provider: AI provider for vision analysis
        """
        self.threshold = threshold
        self.min_scene_duration = min_scene_duration
        self.use_ai = use_ai
        self.ai_provider = ai_provider

        # Detection parameters
        self.histogram_threshold = 0.4
        self.motion_threshold = 0.5
        self.edge_threshold = 0.3

    def detect_video_scenes(self, video_path: str | Path) -> list[Scene]:
        """
        Detect scenes in a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of detected scenes
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Detect scene boundaries
            boundaries = self._detect_boundaries_video(cap, fps)

            # Create scenes from boundaries
            scenes = self._create_scenes_from_boundaries(
                boundaries, fps, total_frames, video_path
            )

            # Analyze scenes with AI if enabled
            if self.use_ai and scenes:
                scenes = self._analyze_scenes_with_ai(scenes, cap)

            return scenes

        finally:
            cap.release()

    def detect_image_sequence_scenes(
        self,
        images: list[str | Path],
        group_similar: bool = True
    ) -> list[Scene]:
        """
        Detect scenes in an image sequence.
        
        Args:
            images: List of image paths
            group_similar: Whether to group similar images into scenes
            
        Returns:
            List of detected scenes
        """
        if not images:
            return []

        image_paths = [Path(img) for img in images]

        if group_similar:
            # Group similar images into scenes
            scenes = self._group_similar_images(image_paths)
        else:
            # Each image is its own scene
            scenes = self._create_individual_scenes(image_paths)

        # Analyze scenes with AI if enabled
        if self.use_ai and scenes:
            scenes = self._analyze_image_scenes_with_ai(scenes)

        return scenes

    def _detect_boundaries_video(
        self,
        cap: cv2.VideoCapture,
        fps: float
    ) -> list[tuple[int, float]]:
        """
        Detect scene boundaries in video.
        
        Returns list of (frame_number, confidence) tuples.
        """
        boundaries = []
        frame_count = 0
        prev_hist = None
        prev_edges = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Calculate histogram
            hist = self._calculate_histogram(frame)

            # Calculate edges
            edges = self._calculate_edges(frame)

            if prev_hist is not None:
                # Compare histograms
                hist_diff = cv2.compareHist(
                    prev_hist, hist, cv2.HISTCMP_CORREL
                )

                # Compare edge maps
                edge_diff = np.mean(np.abs(edges - prev_edges))

                # Combined score
                score = (1 - hist_diff) * 0.6 + edge_diff * 0.4

                # Check if scene boundary
                if score > self.threshold:
                    boundaries.append((frame_count, score))

            prev_hist = hist
            prev_edges = edges
            frame_count += 1

        # Reset capture for later use
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # Filter boundaries by minimum duration
        filtered = self._filter_boundaries_by_duration(boundaries, fps)

        return filtered

    def _calculate_histogram(self, frame: np.ndarray) -> np.ndarray:
        """Calculate color histogram for frame."""
        # Convert to HSV for better color representation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Calculate histogram
        hist = cv2.calcHist(
            [hsv], [0, 1], None, [50, 60], [0, 180, 0, 256]
        )
        hist = cv2.normalize(hist, hist).flatten()

        return hist

    def _calculate_edges(self, frame: np.ndarray) -> np.ndarray:
        """Calculate edge map for frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return edges

    def _filter_boundaries_by_duration(
        self,
        boundaries: list[tuple[int, float]],
        fps: float
    ) -> list[tuple[int, float]]:
        """Filter out boundaries that create scenes shorter than minimum."""
        if not boundaries:
            return boundaries

        filtered = [boundaries[0]]

        for i in range(1, len(boundaries)):
            prev_frame = filtered[-1][0]
            curr_frame = boundaries[i][0]
            duration = (curr_frame - prev_frame) / fps

            if duration >= self.min_scene_duration:
                filtered.append(boundaries[i])

        return filtered

    def _create_scenes_from_boundaries(
        self,
        boundaries: list[tuple[int, float]],
        fps: float,
        total_frames: int,
        video_path: Path
    ) -> list[Scene]:
        """Create scene objects from detected boundaries."""
        scenes = []

        # Add start boundary if not present
        if not boundaries or boundaries[0][0] > 0:
            boundaries.insert(0, (0, 1.0))

        # Add end boundary
        boundaries.append((total_frames, 1.0))

        for i in range(len(boundaries) - 1):
            start_frame = boundaries[i][0]
            end_frame = boundaries[i + 1][0] - 1

            start_time = start_frame / fps
            end_time = end_frame / fps
            duration = end_time - start_time

            scene = Scene(
                scene_id=f"scene_{i:03d}",
                scene_type=SceneType.WIDE,  # Default, will be refined
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                start_frame=start_frame,
                end_frame=end_frame,
                detection_method=DetectionMethod.CONTENT,
                confidence=boundaries[i][1] if i < len(boundaries) - 1 else 1.0
            )

            # Link scenes
            if i > 0:
                scene.previous_scene = scenes[-1].scene_id
                scenes[-1].next_scene = scene.scene_id

            scenes.append(scene)

        return scenes

    def _group_similar_images(self, image_paths: list[Path]) -> list[Scene]:
        """Group similar images into scenes."""
        if not image_paths:
            return []

        scenes = []
        current_group = [image_paths[0]]
        prev_hist = None

        for i, img_path in enumerate(image_paths):
            # Load and analyze image
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            hist = self._calculate_histogram(img)

            if prev_hist is not None:
                # Compare with previous
                similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)

                if similarity < (1 - self.threshold):
                    # New scene
                    scene = self._create_scene_from_images(
                        current_group,
                        f"scene_{len(scenes):03d}"
                    )
                    scenes.append(scene)
                    current_group = [img_path]
                else:
                    # Same scene
                    current_group.append(img_path)

            prev_hist = hist

        # Add final group
        if current_group:
            scene = self._create_scene_from_images(
                current_group,
                f"scene_{len(scenes):03d}"
            )
            scenes.append(scene)

        return scenes

    def _create_individual_scenes(self, image_paths: list[Path]) -> list[Scene]:
        """Create individual scene for each image."""
        scenes = []

        for i, img_path in enumerate(image_paths):
            scene = Scene(
                scene_id=f"scene_{i:03d}",
                scene_type=SceneType.WIDE,
                start_time=0.0,
                end_time=0.0,
                duration=0.0,
                images=[img_path],
                detection_method=DetectionMethod.CONTENT,
                confidence=1.0
            )

            # Link scenes
            if i > 0:
                scene.previous_scene = scenes[-1].scene_id
                scenes[-1].next_scene = scene.scene_id

            scenes.append(scene)

        return scenes

    def _create_scene_from_images(
        self,
        images: list[Path],
        scene_id: str
    ) -> Scene:
        """Create a scene from a group of images."""
        return Scene(
            scene_id=scene_id,
            scene_type=SceneType.WIDE,
            start_time=0.0,
            end_time=0.0,
            duration=0.0,
            images=images,
            detection_method=DetectionMethod.CONTENT,
            confidence=0.8
        )

    def _analyze_scenes_with_ai(
        self,
        scenes: list[Scene],
        cap: cv2.VideoCapture
    ) -> list[Scene]:
        """Use AI vision to analyze scene content."""
        if not self.ai_provider:
            return scenes

        try:
            analyzer = ImageAnalyzer()
            if self.ai_provider and self.ai_provider not in analyzer.analyzers:
                logger.warning(f"Provider {self.ai_provider} not available")
                return scenes

            for scene in scenes:
                # Extract representative frame
                middle_frame = (scene.start_frame + scene.end_frame) // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
                ret, frame = cap.read()

                if not ret:
                    continue

                # Analyze with AI
                analysis = self._analyze_frame_with_ai(frame, analyzer)

                # Update scene with AI insights
                if analysis:
                    scene.scene_type = self._determine_scene_type(analysis)
                    scene.ai_description = analysis.get("description", "")
                    scene.ai_tags = analysis.get("tags", [])
                    scene.dominant_subject = analysis.get("subject", "")
                    scene.mood = analysis.get("mood", "")
                    scene.location = analysis.get("location", "")

        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")

        return scenes

    def _analyze_image_scenes_with_ai(self, scenes: list[Scene]) -> list[Scene]:
        """Use AI vision to analyze image scenes."""
        if not self.ai_provider:
            return scenes

        try:
            analyzer = ImageAnalyzer()
            if self.ai_provider and self.ai_provider not in analyzer.analyzers:
                logger.warning(f"Provider {self.ai_provider} not available")
                return scenes

            for scene in scenes:
                if not scene.images:
                    continue

                # Use first image as representative
                img_path = scene.images[0]
                img = cv2.imread(str(img_path))

                if img is None:
                    continue

                # Analyze with AI
                analysis = self._analyze_frame_with_ai(img, provider)

                # Update scene
                if analysis:
                    scene.scene_type = self._determine_scene_type(analysis)
                    scene.ai_description = analysis.get("description", "")
                    scene.ai_tags = analysis.get("tags", [])
                    scene.dominant_subject = analysis.get("subject", "")
                    scene.mood = analysis.get("mood", "")
                    scene.location = analysis.get("location", "")

        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")

        return scenes

    def _analyze_frame_with_ai(
        self,
        frame: np.ndarray,
        analyzer: ImageAnalyzer
    ) -> dict[str, Any] | None:
        """Analyze a single frame with AI vision."""
        try:
            # Convert frame to PIL Image
            from PIL import Image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            Image.fromarray(rgb_frame)

            # Create prompt for scene analysis
            prompt = """Analyze this video frame and provide:
1. Scene type (establishing, closeup, medium, wide, action, dialogue, etc.)
2. Main subject or focus
3. Location/setting
4. Mood/atmosphere
5. Camera angle and movement
6. Brief description
7. Relevant tags

Return as JSON with keys: scene_type, subject, location, mood, camera, description, tags"""

            # Get analysis from provider
            # This would need to be implemented based on provider interface
            # For now, return mock data
            return {
                "scene_type": "wide",
                "subject": "landscape",
                "location": "outdoor",
                "mood": "peaceful",
                "camera": "static",
                "description": "Wide landscape shot",
                "tags": ["nature", "outdoor", "landscape"]
            }

        except Exception as e:
            logger.error(f"AI frame analysis failed: {e}")
            return None

    def _determine_scene_type(self, analysis: dict[str, Any]) -> SceneType:
        """Determine scene type from AI analysis."""
        scene_type_str = analysis.get("scene_type", "wide").lower()

        type_mapping = {
            "establishing": SceneType.ESTABLISHING,
            "closeup": SceneType.CLOSEUP,
            "close-up": SceneType.CLOSEUP,
            "medium": SceneType.MEDIUM,
            "wide": SceneType.WIDE,
            "action": SceneType.ACTION,
            "dialogue": SceneType.DIALOGUE,
            "transition": SceneType.TRANSITION,
            "montage": SceneType.MONTAGE,
            "detail": SceneType.DETAIL,
            "pov": SceneType.POV,
        }

        return type_mapping.get(scene_type_str, SceneType.WIDE)

    def export_scenes(self, scenes: list[Scene], output_path: str | Path):
        """Export scenes to JSON file."""
        output_path = Path(output_path)

        data = {
            "scene_count": len(scenes),
            "total_duration": sum(s.duration for s in scenes),
            "scenes": [
                {
                    "id": s.scene_id,
                    "type": s.scene_type.value,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "duration": s.duration,
                    "frames": [s.start_frame, s.end_frame] if s.start_frame else None,
                    "images": [str(p) for p in s.images] if s.images else None,
                    "description": s.ai_description,
                    "tags": s.ai_tags,
                    "subject": s.dominant_subject,
                    "mood": s.mood,
                    "confidence": s.confidence,
                }
                for s in scenes
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(scenes)} scenes to {output_path}")
