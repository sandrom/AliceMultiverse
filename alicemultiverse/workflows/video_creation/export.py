"""Export functionality for video creation workflow."""

import logging
from pathlib import Path

from .davinci import DaVinciResolveTimeline
from .enums import TransitionType
from .models import VideoStoryboard

logger = logging.getLogger(__name__)


class ExportMixin:
    """Mixin for exporting video projects."""
    
    def export_to_davinci_resolve(
        self,
        storyboard: VideoStoryboard,
        video_files: dict[int, Path],
        project_name: str | None = None,
        frame_rate: float = 30.0,
        resolution: tuple[int, int] = (1920, 1080)
    ) -> Path:
        """Export storyboard and videos to DaVinci Resolve timeline format.
        
        Args:
            storyboard: Video storyboard
            video_files: Dict mapping shot index to video file paths
            project_name: Optional project name (uses storyboard name if not provided)
            frame_rate: Timeline frame rate (default: 30 fps)
            resolution: Timeline resolution (default: 1920x1080)
            
        Returns:
            Path to the exported .fcpxml file
        """
        project_name = project_name or storyboard.project_name

        # Create timeline XML
        timeline = DaVinciResolveTimeline(
            project_name=project_name,
            frame_rate=frame_rate,
            resolution=resolution
        )

        # Add shots to timeline
        current_time = 0
        for i, shot in enumerate(storyboard.shots):
            if i not in video_files:
                logger.warning(f"No video file for shot {i+1}, skipping")
                continue

            video_path = video_files[i]

            # Add clip to timeline
            timeline.add_clip(
                file_path=video_path,
                start_time=current_time,
                duration=shot.duration,
                shot_name=f"Shot_{i+1:02d}",
                notes=shot.prompt
            )

            # Add transitions
            if i > 0 and shot.transition_in != TransitionType.CUT:
                timeline.add_transition(
                    transition_type=shot.transition_in,
                    start_time=current_time,
                    duration=0.5  # Default 0.5s transition
                )

            current_time += shot.duration

        # Export timeline
        output_path = Path(f"{project_name}_timeline.fcpxml")
        timeline.export(output_path)

        return output_path
    
    def create_flux_kontext_requests(
        self,
        storyboard: VideoStoryboard,
        frames_per_shot: int = 2
    ) -> dict[str, list[dict]]:
        """Create Flux Kontext requests for keyframe preparation.
        
        Args:
            storyboard: Video storyboard
            frames_per_shot: Number of keyframes per shot
            
        Returns:
            Dictionary mapping shot indices to Flux requests
        """
        flux_requests = {}
        
        for i, shot in enumerate(storyboard.shots):
            requests = []
            
            # Create keyframe at start and end of motion
            for frame_pos in ["start", "end"]:
                prompt = shot.prompt
                
                # Modify prompt based on frame position
                if frame_pos == "start":
                    prompt = f"{prompt}, at the beginning of {shot.camera_motion.value} motion"
                else:
                    prompt = f"{prompt}, at the end of {shot.camera_motion.value} motion"
                
                request = {
                    "prompt": prompt,
                    "model": "flux-kontext",
                    "reference_image": shot.image_hash,
                    "frame_position": frame_pos,
                    "camera_motion": shot.camera_motion.value
                }
                
                requests.append(request)
            
            flux_requests[str(i)] = requests
        
        return flux_requests