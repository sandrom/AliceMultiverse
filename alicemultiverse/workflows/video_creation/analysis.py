"""Image analysis for video creation."""

import logging
from typing import Any

from .enums import CameraMotion

logger = logging.getLogger(__name__)


class AnalysisMixin:
    """Mixin for image analysis operations."""

    # Motion indicators mapping
    MOTION_INDICATORS = {
        CameraMotion.ZOOM_IN: ["close-up", "detail", "intimate", "focus"],
        CameraMotion.ZOOM_OUT: ["wide", "reveal", "establishing", "panoramic"],
        CameraMotion.PAN_LEFT: ["left", "scanning left", "westward"],
        CameraMotion.PAN_RIGHT: ["right", "scanning right", "eastward"],
        CameraMotion.TILT_UP: ["up", "ascending", "rising", "skyward"],
        CameraMotion.TILT_DOWN: ["down", "descending", "falling", "earthward"],
        CameraMotion.TRACK_FORWARD: ["forward", "approaching", "advancing", "push in"],
        CameraMotion.TRACK_BACKWARD: ["backward", "retreating", "pulling back", "dolly out"],
        CameraMotion.ORBIT_LEFT: ["orbit", "circular", "around left"],
        CameraMotion.ORBIT_RIGHT: ["orbit", "circular", "around right"],
    }

    async def analyze_image_for_video(self, image_hash: str) -> dict[str, Any]:
        """Analyze image characteristics for video generation.
        
        Args:
            image_hash: Content hash of the image
            
        Returns:
            Analysis with suggested camera motion and prompt elements
        """
        # Get image metadata from search
        metadata = self.search_db.get_asset_by_hash(image_hash)
        if not metadata:
            raise ValueError(f"Image not found: {image_hash}")

        # Extract tags
        tags = metadata.get("tags", [])

        # Analyze composition
        composition = self._analyze_composition(tags)

        # Suggest camera motion
        suggested_motion = self._suggest_camera_motion(tags, composition)

        # Extract motion keywords
        motion_keywords = self._extract_motion_keywords(tags)

        return {
            "image_hash": image_hash,
            "file_path": metadata.get("file_path"),
            "tags": tags,
            "composition": composition,
            "suggested_motion": suggested_motion,
            "motion_keywords": motion_keywords,
            "original_prompt": metadata.get("prompt", "")
        }

    def _analyze_composition(self, tags: list[str]) -> dict[str, Any]:
        """Analyze image composition from tags."""
        composition = {
            "has_character": any(tag in ["portrait", "person", "character", "face"] for tag in tags),
            "is_landscape": any(tag in ["landscape", "scenery", "environment", "vista"] for tag in tags),
            "has_architecture": any(tag in ["building", "architecture", "city", "interior"] for tag in tags),
            "is_abstract": any(tag in ["abstract", "pattern", "texture", "geometric"] for tag in tags),
            "has_action": any(tag in ["motion", "action", "movement", "dynamic"] for tag in tags),
            "depth": "deep" if any(tag in ["perspective", "depth", "layers"] for tag in tags) else "shallow"
        }
        return composition

    def _suggest_camera_motion(self, tags: list[str], composition: dict[str, Any]) -> CameraMotion:
        """Suggest camera motion based on image analysis."""
        # Check for explicit motion indicators in tags
        for motion, keywords in self.MOTION_INDICATORS.items():
            if any(keyword in tag.lower() for tag in tags for keyword in keywords):
                return motion

        # Rule-based suggestions
        if composition["has_character"] and not composition["is_landscape"]:
            return CameraMotion.ZOOM_IN  # Focus on character
        elif composition["is_landscape"] and composition["depth"] == "deep":
            return CameraMotion.TRACK_FORWARD  # Explore the landscape
        elif composition["has_architecture"]:
            return CameraMotion.ORBIT_LEFT  # Reveal architecture
        elif composition["is_abstract"]:
            return CameraMotion.AUTO  # Let AI decide
        elif composition["has_action"]:
            return CameraMotion.PAN_RIGHT  # Follow action
        else:
            return CameraMotion.STATIC  # Default to static

    def _extract_motion_keywords(self, tags: list[str]) -> list[str]:
        """Extract keywords that suggest motion or dynamism."""
        motion_words = [
            "flying", "running", "flowing", "spinning", "floating",
            "falling", "rising", "moving", "dancing", "jumping",
            "wind", "wave", "storm", "fire", "explosion",
            "speed", "velocity", "energy", "dynamic", "kinetic"
        ]

        return [tag for tag in tags if any(word in tag.lower() for word in motion_words)]
