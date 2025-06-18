"""Video production workflow template.

Common workflow: Generate Video → Add Audio → Enhance
"""

import logging

from alicemultiverse.workflows.base import WorkflowContext, WorkflowStep, WorkflowTemplate

logger = logging.getLogger(__name__)


class VideoProductionWorkflow(WorkflowTemplate):
    """Workflow for producing videos with synchronized audio.

    This workflow:
    1. Generates a video using providers like Veo, Kling, or Runway
    2. Adds synchronized audio using mmaudio
    3. Optionally enhances the video quality
    4. Optionally adds captions or effects

    Parameters:
        video_provider: Provider for video generation (default: veo)
        video_model: Model for video generation
        video_duration: Duration in seconds (default: 8)
        add_audio: Whether to add audio (default: True)
        audio_provider: Provider for audio generation (default: mmaudio)
        enhance_video: Whether to enhance video quality (default: False)
        add_captions: Whether to add captions (default: False)
    """

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define the video production workflow steps."""
        steps = []
        params = context.initial_params

        # Step 1: Video generation
        video_provider = params.get("video_provider", "veo")
        video_model = params.get("video_model")
        video_duration = params.get("video_duration", 8)

        steps.append(WorkflowStep(
            name="generate_video",
            provider=video_provider,
            operation="generate_video",
            parameters={
                "model": video_model,
                "duration": video_duration,
                "fps": params.get("fps", 24),
                "resolution": params.get("resolution", "1080p"),
                "aspect_ratio": params.get("aspect_ratio", "16:9"),
                "seed": params.get("seed"),
            },
            cost_limit=params.get("video_cost_limit", 0.50)
        ))

        # Step 2: Audio generation (if enabled)
        if params.get("add_audio", True):
            audio_provider = params.get("audio_provider", "mmaudio")

            steps.append(WorkflowStep(
                name="generate_audio",
                provider=audio_provider,
                operation="generate_audio",
                parameters={
                    "input_from": "generate_video",
                    "duration": video_duration,
                    "style": params.get("audio_style", "cinematic"),
                    "cfg_strength": params.get("audio_cfg_strength", 4.5),
                    "seed": params.get("audio_seed"),
                },
                condition="previous.success",
                cost_limit=params.get("audio_cost_limit", 0.10)
            ))

            # Step 2b: Merge audio with video
            steps.append(WorkflowStep(
                name="merge_audio_video",
                provider="local",
                operation="merge_media",
                parameters={
                    "video_from": "generate_video",
                    "audio_from": "generate_audio",
                    "output_format": "mp4",
                },
                condition="generate_audio.success",
                cost_limit=0.0
            ))

        # Step 3: Video enhancement (if enabled)
        if params.get("enhance_video", False):
            enhance_provider = params.get("enhance_provider", "topaz")

            steps.append(WorkflowStep(
                name="enhance_video",
                provider=enhance_provider,
                operation="enhance_video",
                parameters={
                    "input_from": "merge_audio_video" if params.get("add_audio", True) else "generate_video",
                    "enhancement_type": params.get("enhancement_type", "quality"),
                    "denoise": params.get("denoise", True),
                    "sharpen": params.get("sharpen", True),
                    "upscale": params.get("upscale_video", False),
                },
                condition="previous.success",
                cost_limit=params.get("enhance_cost_limit", 0.20)
            ))

        # Step 4: Add captions (if enabled)
        if params.get("add_captions", False):
            caption_provider = params.get("caption_provider", "whisper")

            steps.append(WorkflowStep(
                name="generate_captions",
                provider=caption_provider,
                operation="transcribe",
                parameters={
                    "input_from": self._get_previous_video_step(params),
                    "language": params.get("caption_language", "auto"),
                    "style": params.get("caption_style", "minimal"),
                },
                condition="previous.success",
                cost_limit=params.get("caption_cost_limit", 0.05)
            ))

            steps.append(WorkflowStep(
                name="burn_captions",
                provider="local",
                operation="burn_captions",
                parameters={
                    "video_from": self._get_previous_video_step(params),
                    "captions_from": "generate_captions",
                    "font": params.get("caption_font", "Arial"),
                    "size": params.get("caption_size", 24),
                    "position": params.get("caption_position", "bottom"),
                },
                condition="generate_captions.success",
                cost_limit=0.0
            ))

        # Step 5: Final output
        steps.append(WorkflowStep(
            name="final_output",
            provider="local",
            operation="finalize_video",
            parameters={
                "optimize_for_web": params.get("optimize_for_web", True),
                "create_thumbnail": params.get("create_thumbnail", True),
                "create_preview": params.get("create_preview", False),
            },
            condition="previous.success",
            cost_limit=0.0
        ))

        return steps

    def _get_previous_video_step(self, params: dict) -> str:
        """Determine the previous video step based on workflow configuration."""
        if (params.get("add_captions", False) and params.get("enhance_video", False)) or params.get("enhance_video", False):
            return "enhance_video"
        elif params.get("add_audio", True):
            return "merge_audio_video"
        else:
            return "generate_video"

    def validate(self, context: WorkflowContext) -> list[str]:
        """Validate the workflow can execute."""
        errors = super().validate(context)
        params = context.initial_params

        # Check video duration
        duration = params.get("video_duration", 8)
        if duration < 1 or duration > 60:
            errors.append(f"Video duration {duration}s should be between 1 and 60 seconds")

        # Check resolution
        valid_resolutions = ["480p", "720p", "1080p", "4k"]
        resolution = params.get("resolution", "1080p")
        if resolution not in valid_resolutions:
            errors.append(f"Resolution {resolution} not valid. Choose from: {valid_resolutions}")

        return errors

    def estimate_cost(self, context: WorkflowContext) -> float:
        """Estimate total workflow cost."""
        params = context.initial_params
        total = 0.0

        # Video generation (most expensive)
        duration = params.get("video_duration", 8)
        if params.get("video_provider") == "veo":
            total += 0.10 + (duration * 0.02)  # Base + per second
        elif params.get("video_provider") == "kling":
            total += 0.15 + (duration * 0.01)
        else:
            total += 0.20  # Conservative estimate

        # Audio generation
        if params.get("add_audio", True):
            total += 0.05  # mmaudio is relatively cheap

        # Enhancement
        if params.get("enhance_video", False):
            total += 0.10 + (duration * 0.01)  # Processing cost

        # Captions
        if params.get("add_captions", False):
            total += 0.02  # Transcription cost

        return total


class QuickVideoWorkflow(VideoProductionWorkflow):
    """Quick video generation workflow for fast results.

    Uses faster settings and skips enhancement.
    """

    def __init__(self):
        super().__init__(name="QuickVideo")

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define quick video steps."""
        # Override defaults for speed
        params = context.initial_params
        params.setdefault("video_provider", "veo")  # Fast provider
        params.setdefault("video_duration", 5)  # Shorter duration
        params.setdefault("resolution", "720p")  # Lower resolution
        params.setdefault("enhance_video", False)
        params.setdefault("add_captions", False)
        params.setdefault("optimize_for_web", True)

        return super().define_steps(context)


class CinematicVideoWorkflow(VideoProductionWorkflow):
    """Cinematic video workflow for film-quality results.

    Uses best settings and full enhancement pipeline.
    """

    def __init__(self):
        super().__init__(name="CinematicVideo")

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define cinematic video steps."""
        # Override defaults for quality
        params = context.initial_params
        params.setdefault("video_provider", "kling")  # High quality
        params.setdefault("video_model", "kling-2.1-pro")
        params.setdefault("video_duration", 10)
        params.setdefault("resolution", "1080p")
        params.setdefault("fps", 30)
        params.setdefault("add_audio", True)
        params.setdefault("audio_style", "cinematic")
        params.setdefault("enhance_video", True)
        params.setdefault("enhancement_type", "cinematic")
        params.setdefault("add_captions", False)  # Clean look

        # Add color grading step
        steps = super().define_steps(context)

        # Insert color grading before final output
        color_step = WorkflowStep(
            name="color_grade",
            provider="local",
            operation="color_grade",
            parameters={
                "input_from": "enhance_video",
                "lut": params.get("color_lut", "cinematic_warm"),
                "intensity": params.get("color_intensity", 0.7),
            },
            condition="enhance_video.success"
        )

        # Insert before final output
        steps.insert(-1, color_step)

        return steps
