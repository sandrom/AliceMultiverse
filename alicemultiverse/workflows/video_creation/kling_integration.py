"""Kling AI integration for video generation."""

import logging
from pathlib import Path

from ...providers.provider_types import GenerationRequest, GenerationType
from .models import VideoStoryboard

logger = logging.getLogger(__name__)


class KlingIntegrationMixin:
    """Mixin for Kling AI integration."""
    
    def create_kling_requests(
        self,
        storyboard: VideoStoryboard,
        model: str = "kling-v2.1-pro-text",
        output_dir: Path | None = None
    ) -> list[GenerationRequest]:
        """Create Kling generation requests from storyboard.
        
        Args:
            storyboard: Video storyboard
            model: Kling model to use
            output_dir: Output directory for videos
            
        Returns:
            List of generation requests ready for Kling
        """
        requests = []

        for i, shot in enumerate(storyboard.shots):
            # Determine if this is image-to-video
            is_image_based = "image" in model

            # Create output path
            if output_dir:
                output_path = output_dir / f"shot_{i+1:02d}_{shot.image_hash[:8]}.mp4"
            else:
                output_path = None

            # Build parameters
            parameters = {
                "duration": shot.duration,
                "camera_motion": shot.camera_motion.value,
                "aspect_ratio": "16:9",  # Could be customized
            }

            # Add mode for pro/master models
            if "pro" in model:
                parameters["mode"] = "professional"
            elif "master" in model:
                parameters["mode"] = "master"

            # Create request
            request = GenerationRequest(
                prompt=shot.prompt,
                generation_type=GenerationType.VIDEO,
                model=model,
                reference_assets=[shot.image_hash] if is_image_based else None,
                parameters=parameters,
                output_path=output_path
            )

            requests.append(request)

        return requests
    
    def create_transition_guide(self, storyboard: VideoStoryboard) -> str:
        """Create a text guide for video editing with transitions.
        
        Args:
            storyboard: Video storyboard
            
        Returns:
            Text guide for manual editing
        """
        guide_lines = [
            "# Video Editing Guide",
            f"Project: {storyboard.project_name}",
            f"Total Duration: {storyboard.total_duration} seconds",
            "",
            "## Shot List with Transitions:",
            ""
        ]

        for i, shot in enumerate(storyboard.shots):
            guide_lines.append(f"### Shot {i+1}")
            guide_lines.append(f"- **Image**: {shot.image_hash[:8]}...")
            guide_lines.append(f"- **Duration**: {shot.duration}s")
            guide_lines.append(f"- **Camera Motion**: {shot.camera_motion.value}")
            guide_lines.append(f"- **Transition In**: {shot.transition_in.value}")
            guide_lines.append(f"- **Transition Out**: {shot.transition_out.value}")
            guide_lines.append(f"- **Prompt**: {shot.prompt}")
            
            if shot.motion_keywords:
                guide_lines.append(f"- **Motion Keywords**: {', '.join(shot.motion_keywords)}")
            
            guide_lines.append("")

        # Add editing tips
        guide_lines.extend([
            "## Editing Tips:",
            "",
            "1. Import all video clips in sequence",
            "2. Apply transitions as specified above",
            "3. Consider adding ambient music that matches the style",
            f"4. Recommended frame rate: 30fps",
            "5. Export settings: H.264, High Quality",
            "",
            "## Style Notes:",
            ""
        ])

        style_guide = storyboard.style_guide.get("template", {})
        if style_guide:
            for hint in style_guide.get("camera_hints", []):
                guide_lines.append(f"- {hint}")

        return "\n".join(guide_lines)