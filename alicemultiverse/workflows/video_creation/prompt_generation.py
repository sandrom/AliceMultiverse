"""Prompt generation for video creation."""

import logging
from datetime import datetime
from typing import Any, TYPE_CHECKING

from .enums import CameraMotion, TransitionType
from .models import ShotDescription, VideoStoryboard

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from ...core.protocols import HasUnderstandingProvider

class PromptGenerationMixin:
    """Mixin for video prompt generation."""

    if TYPE_CHECKING:
        # Type hints for mypy
        understanding_provider: Any


    # Style templates for different video types
    STYLE_TEMPLATES = {
        "cinematic": {
            "prefix": "Cinematic shot",
            "camera_hints": ["dramatic lighting", "professional cinematography"],
            "duration": 5,
            "transitions": ["dissolve", "fade"]
        },
        "documentary": {
            "prefix": "Documentary footage",
            "camera_hints": ["natural lighting", "handheld camera feel"],
            "duration": 7,
            "transitions": ["cut", "dissolve"]
        },
        "artistic": {
            "prefix": "Artistic video",
            "camera_hints": ["experimental visuals", "creative composition"],
            "duration": 4,
            "transitions": ["morph", "motion_blur"]
        },
        "narrative": {
            "prefix": "Story-driven scene",
            "camera_hints": ["emotional depth", "character focus"],
            "duration": 6,
            "transitions": ["cut", "fade"]
        },
        "dynamic": {
            "prefix": "High-energy sequence",
            "camera_hints": ["fast-paced motion", "dynamic angles"],
            "duration": 3,
            "transitions": ["cut", "motion_blur"]
        }
    }

    async def generate_video_prompts(
        self,
        image_hashes: list[str],
        style: str = "cinematic",
        target_duration: int = 30,
        enhance_with_ai: bool = False
    ) -> VideoStoryboard:
        """Generate video prompts from selected images.

        Args:
            image_hashes: List of selected image hashes
            style: Video style (cinematic, documentary, etc.)
            target_duration: Target video duration in seconds
            enhance_with_ai: Use AI to enhance prompts

        Returns:
            Complete video storyboard
        """
        if style not in self.STYLE_TEMPLATES:
            style = "cinematic"

        style_template = self.STYLE_TEMPLATES[style]
        shots = []

        # Calculate duration per shot
        shot_duration = min(
            style_template["duration"],
            max(3, target_duration // len(image_hashes))
        )

        for i, image_hash in enumerate(image_hashes):
            # Analyze image
            analysis = await self.analyze_image_for_video(image_hash)

            # Generate base prompt
            prompt = self._generate_shot_prompt(analysis, style_template)

            # Enhance with AI if requested
            if enhance_with_ai and self.understanding_provider:
                prompt = await self._enhance_prompt_with_ai(
                    prompt,
                    analysis,
                    style_template
                )

            # Determine transitions
            transition_in = TransitionType.FADE if i == 0 else TransitionType.CUT
            transition_out = TransitionType.FADE if i == len(image_hashes) - 1 else TransitionType.CUT

            # Create shot description
            shot = ShotDescription(
                image_hash=image_hash,
                prompt=prompt,
                camera_motion=analysis["suggested_motion"],
                duration=shot_duration,
                transition_in=transition_in,
                transition_out=transition_out,
                motion_keywords=analysis["motion_keywords"],
                style_notes=style_template["camera_hints"]
            )

            shots.append(shot)

        # Create storyboard
        storyboard = VideoStoryboard(
            project_name=f"{style}_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            shots=shots,
            total_duration=sum(shot.duration for shot in shots),
            style_guide={
                "style": style,
                "template": style_template,
                "image_count": len(image_hashes)
            }
        )

        return storyboard

    def _generate_shot_prompt(self, analysis: dict[str, Any], style_template: dict[str, Any]) -> str:
        """Generate a video prompt for a single shot."""
        # Start with style prefix
        prompt_parts = [style_template["prefix"]]

        # Add descriptive elements from tags
        key_tags = analysis["tags"][:5]  # Use top 5 tags
        if key_tags:
            prompt_parts.append(", ".join(key_tags))

        # Add composition hints
        comp = analysis["composition"]
        if comp["has_character"]:
            prompt_parts.append("with character in focus")
        elif comp["is_landscape"]:
            prompt_parts.append("sweeping landscape view")

        # Add motion description
        motion = analysis["suggested_motion"]
        if motion != CameraMotion.STATIC:
            motion_desc = motion.value.replace("_", " ")
            prompt_parts.append(f"camera {motion_desc}")

        # Add style-specific camera hints
        if style_template["camera_hints"]:
            prompt_parts.append(style_template["camera_hints"][0])

        # Add motion keywords if present
        if analysis["motion_keywords"]:
            prompt_parts.append(f"featuring {', '.join(analysis['motion_keywords'][:2])}")

        return ", ".join(prompt_parts)

    async def _enhance_prompt_with_ai(
        self,
        base_prompt: str,
        analysis: dict[str, Any],
        style_template: dict[str, Any]
    ) -> str:
        """Use AI to enhance the video prompt."""
        if not self.understanding_provider:
            return base_prompt

        # Create enhancement prompt
        enhancement_prompt = f"""
        Enhance this video generation prompt for Kling AI:

        Base prompt: {base_prompt}
        Style: {style_template.get('prefix', 'cinematic')}
        Camera motion: {analysis['suggested_motion'].value}

        Make it more cinematic and specific for video generation.
        Keep it under 100 words. Focus on movement and atmosphere.
        """

        try:
            # Use understanding provider to enhance
            # This is a simplified version - you might want to add proper API integration
            enhanced = await self.understanding_provider.analyze_with_prompt(
                analysis["file_path"],
                enhancement_prompt
            )
            return enhanced.get("description", base_prompt)
        except Exception as e:
            logger.warning(f"Failed to enhance prompt with AI: {e}")
            return base_prompt
