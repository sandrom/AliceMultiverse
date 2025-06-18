"""Social media workflow templates for platform-specific content.

Optimized for different social platforms with their unique requirements.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from alicemultiverse.workflows.base import WorkflowContext, WorkflowStep, WorkflowTemplate

logger = logging.getLogger(__name__)


@dataclass
class PlatformSpec:
    """Specifications for a social media platform."""
    name: str
    aspect_ratio: tuple[int, int]
    max_duration: float
    min_duration: float
    optimal_duration: float
    fps: int
    max_file_size_mb: int
    safe_zones: dict[str, float]  # Percentages for UI elements
    features: list[str]
    audio_required: bool = True


class SocialPlatform(Enum):
    """Supported social media platforms."""
    INSTAGRAM_REEL = "instagram_reel"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_POST = "instagram_post"
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_VIDEO = "youtube_video"
    TWITTER_VIDEO = "twitter_video"
    LINKEDIN_VIDEO = "linkedin_video"
    PINTEREST_IDEA = "pinterest_idea"


# Platform specifications
PLATFORM_SPECS = {
    SocialPlatform.INSTAGRAM_REEL: PlatformSpec(
        name="Instagram Reel",
        aspect_ratio=(9, 16),
        max_duration=90,
        min_duration=3,
        optimal_duration=15,
        fps=30,
        max_file_size_mb=100,
        safe_zones={"top": 0.1, "bottom": 0.15},
        features=["music", "effects", "text_overlay", "stickers", "polls"],
    ),
    SocialPlatform.INSTAGRAM_STORY: PlatformSpec(
        name="Instagram Story",
        aspect_ratio=(9, 16),
        max_duration=15,
        min_duration=1,
        optimal_duration=7,
        fps=30,
        max_file_size_mb=100,
        safe_zones={"top": 0.1, "bottom": 0.2},
        features=["stickers", "polls", "questions", "swipe_up", "music"],
    ),
    SocialPlatform.TIKTOK: PlatformSpec(
        name="TikTok",
        aspect_ratio=(9, 16),
        max_duration=180,  # 3 minutes
        min_duration=1,
        optimal_duration=30,
        fps=30,
        max_file_size_mb=287,
        safe_zones={"top": 0.15, "bottom": 0.1, "sides": 0.05},
        features=["music", "effects", "text_overlay", "duet", "stitch", "trending"],
    ),
    SocialPlatform.YOUTUBE_SHORTS: PlatformSpec(
        name="YouTube Shorts",
        aspect_ratio=(9, 16),
        max_duration=60,
        min_duration=1,
        optimal_duration=30,
        fps=30,
        max_file_size_mb=100,
        safe_zones={"top": 0.1, "bottom": 0.1},
        features=["music", "text_overlay", "chapters", "end_screen"],
    ),
    SocialPlatform.TWITTER_VIDEO: PlatformSpec(
        name="Twitter Video",
        aspect_ratio=(16, 9),
        max_duration=140,
        min_duration=0.5,
        optimal_duration=45,
        fps=30,
        max_file_size_mb=512,
        safe_zones={"all": 0.05},
        features=["captions", "preview_thumbnail"],
    ),
}


class SocialMediaTemplate(WorkflowTemplate):
    """Base template for social media content creation.

    This workflow:
    1. Analyzes content for platform fit
    2. Optimizes for platform specifications
    3. Adds platform-specific features
    4. Ensures engagement optimization
    5. Exports in platform format

    Parameters:
        platform: Target social platform
        images: List of image paths
        music_file: Optional music track
        caption: Post caption/description
        hashtags: List of hashtags
        style: Content style (trending, educational, entertaining)
        auto_optimize: Automatically optimize for engagement
    """

    def __init__(self):
        super().__init__(name="SocialMedia")
        self.platform_specs = PLATFORM_SPECS

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define social media workflow steps."""
        steps = []
        params = context.initial_params
        platform = SocialPlatform(params["platform"])
        spec = self.platform_specs[platform]

        # Step 1: Analyze content
        steps.append(WorkflowStep(
            name="analyze_content",
            provider="local",
            operation="analyze_for_social",
            parameters={
                "images": params["images"],
                "platform": platform.value,
                "detect_trends": True,
                "check_appropriateness": True,
                "suggest_optimizations": True,
            },
            cost_limit=0.0
        ))

        # Step 2: Optimize for platform
        steps.append(WorkflowStep(
            name="optimize_content",
            provider="local",
            operation="optimize_for_platform",
            parameters={
                "content_from": "analyze_content",
                "platform_spec": spec.__dict__,
                "aspect_ratio": spec.aspect_ratio,
                "duration": params.get("duration", spec.optimal_duration),
                "apply_safe_zones": True,
                "style": params.get("style", "trending"),
            },
            condition="analyze_content.success",
            cost_limit=0.0
        ))

        # Step 3: Add engagement features
        steps.append(WorkflowStep(
            name="add_engagement",
            provider="local",
            operation="add_engagement_features",
            parameters={
                "optimized_from": "optimize_content",
                "platform": platform.value,
                "hook_duration": self._get_hook_duration(platform),
                "call_to_action": params.get("cta"),
                "trending_elements": params.get("use_trends", True),
                "accessibility": True,  # Add captions
            },
            condition="optimize_content.success",
            cost_limit=0.0
        ))

        # Step 4: Apply platform styling
        steps.append(WorkflowStep(
            name="apply_styling",
            provider="local",
            operation="apply_platform_styling",
            parameters={
                "content_from": "add_engagement",
                "platform": platform.value,
                "music_file": params.get("music_file"),
                "text_overlays": self._prepare_text_overlays(params),
                "filters": params.get("filters", "auto"),
                "branding": params.get("branding", {}),
            },
            condition="add_engagement.success",
            cost_limit=0.0
        ))

        # Step 5: Export for platform
        steps.append(WorkflowStep(
            name="export_platform",
            provider="local",
            operation="export_for_social",
            parameters={
                "styled_from": "apply_styling",
                "platform": platform.value,
                "format": self._get_export_format(platform),
                "compression": "platform_optimized",
                "metadata": self._prepare_metadata(params, platform),
                "preview": True,
            },
            condition="apply_styling.success",
            cost_limit=0.0
        ))

        return steps

    def analyze_for_social(self, context: WorkflowContext) -> dict[str, Any]:
        """Analyze content for social media suitability."""
        params = context.get_step_params("analyze_content")
        images = params["images"]
        platform = params["platform"]

        analysis = {
            "total_content": len(images),
            "platform_fit": self._assess_platform_fit(images, platform),
            "trend_alignment": self._check_trend_alignment(images, platform),
            "engagement_potential": self._estimate_engagement(images, platform),
            "warnings": [],
            "optimizations": [],
        }

        # Check for potential issues
        if len(images) < 3:
            analysis["warnings"].append("Low content count may reduce engagement")

        # Suggest optimizations
        if platform in ["instagram_reel", "tiktok"]:
            analysis["optimizations"].append("Add trending audio for better reach")
            analysis["optimizations"].append("Include hook in first 3 seconds")

        return analysis

    def optimize_for_platform(self, context: WorkflowContext) -> dict[str, Any]:
        """Optimize content for platform specifications."""
        params = context.get_step_params("optimize_content")
        analysis = context.get_result("analyze_content")

        spec = params["platform_spec"]
        aspect_ratio = params["aspect_ratio"]
        duration = params["duration"]

        # Calculate optimal sequencing
        images_per_second = self._calculate_pacing(params["style"], spec["name"])
        total_images_needed = int(duration * images_per_second)

        # Prepare content sequence
        optimized = {
            "sequence": self._create_optimal_sequence(
                analysis["total_content"],
                total_images_needed,
                params["style"]
            ),
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "safe_zones_applied": True,
            "pacing": images_per_second,
        }

        return optimized

    def add_engagement_features(self, context: WorkflowContext) -> dict[str, Any]:
        """Add platform-specific engagement features."""
        params = context.get_step_params("add_engagement")
        optimized = context.get_result("optimize_content")
        platform = params["platform"]

        features = {
            "hook": {
                "type": self._select_hook_type(platform),
                "duration": params["hook_duration"],
                "position": "start",
            },
            "engagement_points": self._plan_engagement_points(
                optimized["duration"],
                platform
            ),
            "accessibility": {
                "captions": params["accessibility"],
                "caption_style": self._get_caption_style(platform),
            },
        }

        # Add CTA if provided
        if params.get("call_to_action"):
            features["cta"] = {
                "text": params["call_to_action"],
                "position": "end",
                "duration": 2.0,
            }

        # Add trending elements
        if params.get("trending_elements"):
            features["trends"] = self._get_trending_elements(platform)

        return features

    def apply_platform_styling(self, context: WorkflowContext) -> dict[str, Any]:
        """Apply platform-specific styling."""
        params = context.get_step_params("apply_styling")
        context.get_result("add_engagement")
        platform = params["platform"]

        styling = {
            "visual_style": self._get_platform_style(platform),
            "color_correction": "platform_optimized",
            "filters": self._select_filters(platform, params.get("filters")),
        }

        # Add text overlays
        if params.get("text_overlays"):
            styling["text"] = {
                "overlays": params["text_overlays"],
                "style": self._get_text_style(platform),
                "animations": self._get_text_animations(platform),
            }

        # Add music if provided
        if params.get("music_file"):
            styling["audio"] = {
                "music": params["music_file"],
                "sync_to_beat": platform in ["instagram_reel", "tiktok"],
                "volume_ducking": True,
            }

        # Add branding
        if params.get("branding"):
            styling["branding"] = self._apply_branding(params["branding"], platform)

        return styling

    def export_for_social(self, context: WorkflowContext) -> dict[str, Any]:
        """Export content in platform format."""
        params = context.get_step_params("export_platform")
        platform = params["platform"]
        spec = self.platform_specs[SocialPlatform(platform)]

        export = {
            "format": params["format"],
            "resolution": self._get_resolution(spec.aspect_ratio),
            "fps": spec.fps,
            "bitrate": "optimized",
            "file_size": f"<{spec.max_file_size_mb}MB",
        }

        # Add metadata
        export["metadata"] = params["metadata"]

        # Generate preview
        if params.get("preview"):
            export["preview"] = {
                "thumbnail": "auto_generated",
                "preview_points": [0, 0.25, 0.5, 0.75],
            }

        return export

    # Helper methods
    def _get_hook_duration(self, platform: SocialPlatform) -> float:
        """Get optimal hook duration for platform."""
        hook_durations = {
            SocialPlatform.INSTAGRAM_REEL: 3.0,
            SocialPlatform.TIKTOK: 3.0,
            SocialPlatform.YOUTUBE_SHORTS: 5.0,
            SocialPlatform.TWITTER_VIDEO: 5.0,
        }
        return hook_durations.get(platform, 3.0)

    def _prepare_text_overlays(self, params: dict) -> list[dict]:
        """Prepare text overlays from caption and hashtags."""
        overlays = []

        if params.get("caption"):
            # Split caption into readable chunks
            caption_parts = self._split_caption(params["caption"])
            for i, part in enumerate(caption_parts):
                overlays.append({
                    "text": part,
                    "position": "center",
                    "timing": i * 3.0,  # Show every 3 seconds
                    "duration": 2.5,
                })

        return overlays

    def _prepare_metadata(self, params: dict, platform: SocialPlatform) -> dict:
        """Prepare platform-specific metadata."""
        metadata = {
            "title": params.get("title", ""),
            "description": params.get("caption", ""),
            "tags": params.get("hashtags", []),
            "platform": platform.value,
        }

        # Platform-specific metadata
        if platform == SocialPlatform.YOUTUBE_SHORTS:
            metadata["category"] = params.get("category", "Entertainment")
            metadata["visibility"] = params.get("visibility", "public")

        return metadata

    def _get_export_format(self, platform: SocialPlatform) -> str:
        """Get export format for platform."""
        formats = {
            SocialPlatform.INSTAGRAM_REEL: "mp4",
            SocialPlatform.TIKTOK: "mp4",
            SocialPlatform.YOUTUBE_SHORTS: "mp4",
            SocialPlatform.TWITTER_VIDEO: "mp4",
        }
        return formats.get(platform, "mp4")

    def _assess_platform_fit(self, images: list[str], platform: str) -> float:
        """Assess how well content fits platform."""
        # Placeholder - would analyze content style
        return 0.8

    def _check_trend_alignment(self, images: list[str], platform: str) -> dict:
        """Check alignment with current trends."""
        # Placeholder - would check against trend database
        return {"aligned": True, "trends": ["minimalist", "authentic"]}

    def _estimate_engagement(self, images: list[str], platform: str) -> float:
        """Estimate engagement potential."""
        # Placeholder - would use ML model
        return 0.75

    def _calculate_pacing(self, style: str, platform: str) -> float:
        """Calculate images per second for style."""
        pacing_map = {
            "trending": 2.0,  # Fast cuts
            "educational": 0.5,  # Slower for comprehension
            "entertaining": 1.5,
            "aesthetic": 0.8,
            "tutorial": 0.3,
        }
        return pacing_map.get(style, 1.0)

    def _create_optimal_sequence(self, available: int, needed: int, style: str) -> list[int]:
        """Create optimal image sequence."""
        if available >= needed:
            # Select best images
            return list(range(needed))
        else:
            # Repeat some images
            sequence = []
            for i in range(needed):
                sequence.append(i % available)
            return sequence

    def _select_hook_type(self, platform: str) -> str:
        """Select hook type for platform."""
        hooks = {
            "instagram_reel": "visual_surprise",
            "tiktok": "question_hook",
            "youtube_shorts": "preview_hook",
        }
        return hooks.get(platform, "visual_hook")

    def _plan_engagement_points(self, duration: float, platform: str) -> list[dict]:
        """Plan engagement points throughout video."""
        points = []

        # Add engagement every 7-10 seconds
        interval = 8.0
        current = interval

        while current < duration - 2:
            points.append({
                "time": current,
                "type": "visual_change",
                "duration": 1.0,
            })
            current += interval

        return points

    def _get_caption_style(self, platform: str) -> dict:
        """Get caption style for platform."""
        styles = {
            "instagram_reel": {"position": "bottom", "style": "bold_outline"},
            "tiktok": {"position": "center", "style": "animated"},
            "youtube_shorts": {"position": "bottom", "style": "youtube_cc"},
        }
        return styles.get(platform, {"position": "bottom", "style": "simple"})

    def _get_trending_elements(self, platform: str) -> list[str]:
        """Get current trending elements."""
        # Placeholder - would fetch from trend API
        return ["trending_audio", "popular_effect", "viral_transition"]

    def _get_platform_style(self, platform: str) -> dict:
        """Get visual style for platform."""
        styles = {
            "instagram_reel": {"saturation": 1.1, "contrast": 1.05},
            "tiktok": {"brightness": 1.05, "vibrance": 1.1},
            "youtube_shorts": {"clarity": 1.1, "sharpness": 1.05},
        }
        return styles.get(platform, {})

    def _select_filters(self, platform: str, filter_pref: str) -> list[str]:
        """Select filters for platform."""
        if filter_pref == "auto":
            platform_filters = {
                "instagram_reel": ["clarendon", "juno"],
                "tiktok": ["vivid", "fresh"],
                "youtube_shorts": ["enhance", "pop"],
            }
            return platform_filters.get(platform, ["enhance"])
        return [filter_pref]

    def _get_text_style(self, platform: str) -> dict:
        """Get text style for platform."""
        styles = {
            "instagram_reel": {
                "font": "Arial Bold",
                "size": "large",
                "color": "white",
                "outline": "black",
            },
            "tiktok": {
                "font": "Impact",
                "size": "medium",
                "color": "white",
                "shadow": True,
            },
        }
        return styles.get(platform, {"font": "Arial", "color": "white"})

    def _get_text_animations(self, platform: str) -> list[str]:
        """Get text animations for platform."""
        animations = {
            "instagram_reel": ["fade_in", "bounce"],
            "tiktok": ["typewriter", "shake"],
            "youtube_shorts": ["slide_in", "fade"],
        }
        return animations.get(platform, ["fade_in"])

    def _apply_branding(self, branding: dict, platform: str) -> dict:
        """Apply branding elements."""
        return {
            "watermark": branding.get("watermark"),
            "position": "bottom_right",
            "opacity": 0.7,
            "size": "small",
        }

    def _get_resolution(self, aspect_ratio: tuple[int, int]) -> tuple[int, int]:
        """Get resolution for aspect ratio."""
        if aspect_ratio == (9, 16):  # Vertical
            return (1080, 1920)
        elif aspect_ratio == (16, 9):  # Horizontal
            return (1920, 1080)
        elif aspect_ratio == (1, 1):  # Square
            return (1080, 1080)
        return (1080, 1920)  # Default vertical

    def _split_caption(self, caption: str, max_length: int = 30) -> list[str]:
        """Split caption into readable chunks."""
        words = caption.split()
        chunks = []
        current = []

        for word in words:
            current.append(word)
            if len(" ".join(current)) > max_length:
                chunks.append(" ".join(current[:-1]))
                current = [word]

        if current:
            chunks.append(" ".join(current))

        return chunks


class InstagramReelTemplate(SocialMediaTemplate):
    """Specialized template for Instagram Reels."""

    def __init__(self):
        super().__init__()
        self.name = "InstagramReel"

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Add Instagram-specific steps."""
        steps = super().define_steps(context)

        # Insert Instagram-specific step after optimization
        instagram_step = WorkflowStep(
            name="add_instagram_features",
            provider="local",
            operation="add_reel_features",
            parameters={
                "content_from": "optimize_content",
                "add_music_sync": True,
                "add_effects": context.initial_params.get("effects", ["zoom", "transition"]),
                "add_stickers": context.initial_params.get("stickers", []),
                "remix_ready": True,
            },
            condition="optimize_content.success",
            cost_limit=0.0
        )

        # Insert after optimize step
        steps.insert(2, instagram_step)

        return steps


class TikTokTemplate(SocialMediaTemplate):
    """Specialized template for TikTok videos."""

    def __init__(self):
        super().__init__()
        self.name = "TikTok"

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Add TikTok-specific steps."""
        steps = super().define_steps(context)

        # Add trend integration step
        trend_step = WorkflowStep(
            name="integrate_trends",
            provider="local",
            operation="add_tiktok_trends",
            parameters={
                "content_from": "optimize_content",
                "trending_sounds": True,
                "trending_effects": True,
                "hashtag_challenges": context.initial_params.get("challenges", []),
                "duet_ready": context.initial_params.get("duet_ready", False),
            },
            condition="optimize_content.success",
            cost_limit=0.0
        )

        steps.insert(2, trend_step)

        return steps


class LinkedInVideoTemplate(SocialMediaTemplate):
    """Professional video template for LinkedIn."""

    def __init__(self):
        super().__init__()
        self.name = "LinkedInVideo"

        # Override platform specs for professional content
        self.platform_specs[SocialPlatform.LINKEDIN_VIDEO] = PlatformSpec(
            name="LinkedIn Video",
            aspect_ratio=(16, 9),  # Landscape preferred
            max_duration=600,  # 10 minutes
            min_duration=3,
            optimal_duration=60,  # 1 minute
            fps=30,
            max_file_size_mb=5000,
            safe_zones={"all": 0.05},
            features=["captions", "professional", "educational"],
        )

    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Add LinkedIn-specific professional touches."""
        steps = super().define_steps(context)

        # Add professional styling
        professional_step = WorkflowStep(
            name="add_professional_elements",
            provider="local",
            operation="add_linkedin_professional",
            parameters={
                "content_from": "optimize_content",
                "add_intro_card": True,
                "add_outro_cta": True,
                "professional_transitions": True,
                "corporate_safe": True,
                "add_subtitles": True,  # Important for silent autoplay
            },
            condition="optimize_content.success",
            cost_limit=0.0
        )

        steps.insert(2, professional_step)

        return steps
