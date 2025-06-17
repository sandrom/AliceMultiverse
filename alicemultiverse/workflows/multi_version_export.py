"""Multi-version export for platform-specific video adaptations.

This module automatically adapts video timelines for different social media platforms,
handling aspect ratios, durations, and platform-specific requirements.
"""

import copy
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..workflows.video_export import Timeline, TimelineClip

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported export platforms."""
    INSTAGRAM_REEL = "instagram_reel"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_POST = "instagram_post"
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_HORIZONTAL = "youtube"
    TWITTER = "twitter"
    MASTER = "master"  # Full resolution original


@dataclass
class PlatformSpec:
    """Platform-specific video specifications."""
    name: str
    aspect_ratio: tuple[int, int]  # width, height
    resolution: tuple[int, int]
    min_duration: float  # seconds
    max_duration: float
    preferred_duration: float
    safe_zones: dict[str, float] = field(default_factory=dict)  # Percentages
    features: list[str] = field(default_factory=list)
    fps: float = 30.0
    requires_audio: bool = True
    supports_hdr: bool = False
    file_size_limit_mb: int | None = None


# Platform specifications
PLATFORM_SPECS = {
    Platform.INSTAGRAM_REEL: PlatformSpec(
        name="Instagram Reel",
        aspect_ratio=(9, 16),
        resolution=(1080, 1920),
        min_duration=3.0,
        max_duration=90.0,
        preferred_duration=30.0,
        safe_zones={
            "top": 15,  # Account for UI elements
            "bottom": 10,
            "sides": 5
        },
        features=["vertical", "short_form", "loop_friendly"],
        file_size_limit_mb=100
    ),
    Platform.INSTAGRAM_STORY: PlatformSpec(
        name="Instagram Story",
        aspect_ratio=(9, 16),
        resolution=(1080, 1920),
        min_duration=1.0,
        max_duration=60.0,
        preferred_duration=15.0,
        safe_zones={
            "top": 20,  # More UI elements in stories
            "bottom": 15,
            "sides": 5
        },
        features=["vertical", "ephemeral", "interactive"],
        file_size_limit_mb=100
    ),
    Platform.INSTAGRAM_POST: PlatformSpec(
        name="Instagram Post",
        aspect_ratio=(1, 1),
        resolution=(1080, 1080),
        min_duration=3.0,
        max_duration=60.0,
        preferred_duration=30.0,
        safe_zones={"all": 5},
        features=["square", "feed_optimized"],
        file_size_limit_mb=100
    ),
    Platform.TIKTOK: PlatformSpec(
        name="TikTok",
        aspect_ratio=(9, 16),
        resolution=(1080, 1920),
        min_duration=3.0,
        max_duration=180.0,  # 3 minutes
        preferred_duration=15.0,
        safe_zones={
            "top": 10,
            "bottom": 15,  # Controls and captions
            "sides": 5
        },
        features=["vertical", "trend_friendly", "sound_sync"],
        file_size_limit_mb=287
    ),
    Platform.YOUTUBE_SHORTS: PlatformSpec(
        name="YouTube Shorts",
        aspect_ratio=(9, 16),
        resolution=(1080, 1920),
        min_duration=1.0,
        max_duration=60.0,
        preferred_duration=30.0,
        safe_zones={
            "top": 10,
            "bottom": 10,
            "sides": 5
        },
        features=["vertical", "discoverable", "shelf_eligible"],
        supports_hdr=True
    ),
    Platform.YOUTUBE_HORIZONTAL: PlatformSpec(
        name="YouTube",
        aspect_ratio=(16, 9),
        resolution=(1920, 1080),
        min_duration=1.0,
        max_duration=float('inf'),
        preferred_duration=600.0,  # 10 minutes
        safe_zones={"all": 5},
        features=["horizontal", "long_form", "monetizable"],
        supports_hdr=True,
        fps=60.0  # Supports higher frame rates
    ),
    Platform.TWITTER: PlatformSpec(
        name="Twitter/X",
        aspect_ratio=(16, 9),
        resolution=(1280, 720),
        min_duration=0.5,
        max_duration=140.0,
        preferred_duration=30.0,
        safe_zones={"all": 5},
        features=["horizontal", "quick_view"],
        file_size_limit_mb=512
    ),
    Platform.MASTER: PlatformSpec(
        name="Master Export",
        aspect_ratio=(16, 9),
        resolution=(3840, 2160),  # 4K
        min_duration=0.0,
        max_duration=float('inf'),
        preferred_duration=0.0,  # Keep original
        safe_zones={},
        features=["full_quality", "archival"],
        supports_hdr=True,
        fps=60.0
    )
}


@dataclass
class CropRegion:
    """Defines a crop region for aspect ratio adjustment."""
    x: float  # 0-1 normalized
    y: float
    width: float
    height: float
    focus_point: tuple[float, float] | None = None  # Important area to keep


@dataclass
class ExportVersion:
    """A platform-specific export version."""
    platform: Platform
    timeline: Timeline
    crop_regions: dict[str, CropRegion] = field(default_factory=dict)  # clip_id -> region
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def spec(self) -> PlatformSpec:
        """Get platform specification."""
        return PLATFORM_SPECS[self.platform]


class MultiVersionExporter:
    """Handles multi-platform timeline adaptations."""

    def __init__(self):
        """Initialize the exporter."""
        self.adaptation_strategies = {
            "duration": self._adapt_duration,
            "aspect_ratio": self._adapt_aspect_ratio,
            "pacing": self._adapt_pacing,
            "features": self._adapt_features
        }

    def create_platform_versions(
        self,
        timeline: Timeline,
        platforms: list[Platform],
        smart_crop: bool = True,
        maintain_sync: bool = True
    ) -> dict[Platform, ExportVersion]:
        """Create platform-specific versions from a master timeline.
        
        Args:
            timeline: Master timeline to adapt
            platforms: List of target platforms
            smart_crop: Use AI to detect important regions
            maintain_sync: Try to keep music sync when adapting
            
        Returns:
            Dictionary of platform versions
        """
        versions = {}

        for platform in platforms:
            logger.info(f"Creating {platform.value} version")

            # Create base version
            version = ExportVersion(
                platform=platform,
                timeline=copy.deepcopy(timeline)
            )

            # Apply adaptations
            version = self._adapt_timeline(version, smart_crop, maintain_sync)

            versions[platform] = version

        return versions

    def _adapt_timeline(
        self,
        version: ExportVersion,
        smart_crop: bool,
        maintain_sync: bool
    ) -> ExportVersion:
        """Apply all necessary adaptations for a platform."""
        spec = version.spec

        # Apply duration constraints
        version = self._adapt_duration(version, maintain_sync)

        # Adapt aspect ratio
        version = self._adapt_aspect_ratio(version, smart_crop)

        # Adjust pacing for platform
        version = self._adapt_pacing(version)

        # Add platform-specific features
        version = self._adapt_features(version)

        # Update metadata
        version.timeline.metadata.update({
            "platform": version.platform.value,
            "adapted_for": spec.name,
            "aspect_ratio": f"{spec.aspect_ratio[0]}:{spec.aspect_ratio[1]}",
            "resolution": f"{spec.resolution[0]}x{spec.resolution[1]}"
        })

        return version

    def _adapt_duration(self, version: ExportVersion, maintain_sync: bool) -> ExportVersion:
        """Adapt timeline duration for platform constraints."""
        spec = version.spec
        timeline = version.timeline
        current_duration = timeline.duration

        # Check if adaptation needed
        if spec.min_duration <= current_duration <= spec.max_duration:
            return version

        if current_duration < spec.min_duration:
            # Need to extend - loop or hold last frame
            logger.info(f"Extending timeline from {current_duration}s to {spec.min_duration}s")

            if maintain_sync and timeline.audio_tracks:
                # Loop the entire sequence
                self._loop_timeline(timeline, spec.min_duration)
            else:
                # Hold last frame
                self._extend_last_clip(timeline, spec.min_duration)

        elif current_duration > spec.max_duration:
            # Need to trim
            logger.info(f"Trimming timeline from {current_duration}s to {spec.max_duration}s")

            if maintain_sync:
                # Smart trim - find good cut points
                self._smart_trim(timeline, spec.max_duration)
            else:
                # Simple trim
                self._simple_trim(timeline, spec.max_duration)

        return version

    def _adapt_aspect_ratio(self, version: ExportVersion, smart_crop: bool) -> ExportVersion:
        """Adapt aspect ratio through intelligent cropping."""
        spec = version.spec
        timeline = version.timeline

        # Calculate target aspect ratio
        target_ratio = spec.aspect_ratio[0] / spec.aspect_ratio[1]
        current_ratio = timeline.resolution[0] / timeline.resolution[1]

        if abs(target_ratio - current_ratio) < 0.01:
            return version  # Already correct ratio

        # Calculate crop regions for each clip
        for i, clip in enumerate(timeline.clips):
            if smart_crop:
                # Would use AI to detect important regions
                crop = self._calculate_smart_crop(
                    clip,
                    current_ratio,
                    target_ratio,
                    spec.safe_zones
                )
            else:
                # Center crop
                crop = self._calculate_center_crop(
                    current_ratio,
                    target_ratio
                )

            version.crop_regions[f"clip_{i}"] = crop

        # Update timeline resolution
        timeline.resolution = spec.resolution

        return version

    def _adapt_pacing(self, version: ExportVersion) -> ExportVersion:
        """Adjust pacing for platform preferences."""
        spec = version.spec
        timeline = version.timeline

        # Platform-specific pacing adjustments
        if "short_form" in spec.features:
            # Faster cuts for short-form content
            self._increase_pace(timeline, factor=1.2)

        elif "long_form" in spec.features:
            # More breathing room for long-form
            self._decrease_pace(timeline, factor=0.9)

        if version.platform == Platform.TIKTOK:
            # TikTok favors very quick hooks
            self._optimize_hook(timeline, duration=3.0)

        return version

    def _adapt_features(self, version: ExportVersion) -> ExportVersion:
        """Add platform-specific features."""
        spec = version.spec
        timeline = version.timeline

        # Platform-specific enhancements
        if "loop_friendly" in spec.features:
            self._make_loopable(timeline)

        if "trend_friendly" in spec.features:
            # Add markers for trend sounds
            timeline.metadata["trend_sync_points"] = self._identify_trend_points(timeline)

        if "interactive" in spec.features:
            # Add interaction zones for stories
            timeline.metadata["tap_zones"] = self._calculate_tap_zones(spec.safe_zones)

        return version

    # Duration adaptation helpers

    def _loop_timeline(self, timeline: Timeline, target_duration: float):
        """Loop timeline to reach target duration."""
        original_clips = timeline.clips.copy()
        original_duration = timeline.duration

        loops_needed = int(target_duration / original_duration) + 1
        current_time = 0.0

        timeline.clips = []
        for loop in range(loops_needed):
            for clip in original_clips:
                new_clip = copy.deepcopy(clip)
                new_clip.start_time = current_time
                timeline.clips.append(new_clip)
                current_time += clip.duration

                if current_time >= target_duration:
                    break

            if current_time >= target_duration:
                break

        timeline.duration = target_duration

    def _extend_last_clip(self, timeline: Timeline, target_duration: float):
        """Extend the last clip to reach target duration."""
        if timeline.clips:
            last_clip = timeline.clips[-1]
            extension = target_duration - timeline.duration
            last_clip.duration += extension
            timeline.duration = target_duration

    def _smart_trim(self, timeline: Timeline, target_duration: float):
        """Intelligently trim timeline preserving key moments."""
        # Identify less important sections
        # This is simplified - would use AI to detect importance

        if not timeline.markers:
            return self._simple_trim(timeline, target_duration)

        # Keep clips near markers (assumed important)
        important_times = [m["time"] for m in timeline.markers]
        importance_scores = []

        for clip in timeline.clips:
            # Score based on proximity to markers
            min_distance = min(
                abs(clip.start_time - t) for t in important_times
            ) if important_times else float('inf')

            score = 1.0 / (1.0 + min_distance)
            importance_scores.append(score)

        # Remove least important clips first
        clips_with_scores = list(zip(timeline.clips, importance_scores, strict=False))
        clips_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Keep most important clips up to duration
        kept_clips = []
        current_duration = 0.0

        for clip, score in clips_with_scores:
            if current_duration + clip.duration <= target_duration:
                kept_clips.append(clip)
                current_duration += clip.duration

        # Re-sort by time and update positions
        kept_clips.sort(key=lambda c: c.start_time)
        current_time = 0.0
        for clip in kept_clips:
            clip.start_time = current_time
            current_time += clip.duration

        timeline.clips = kept_clips
        timeline.duration = current_duration

    def _simple_trim(self, timeline: Timeline, target_duration: float):
        """Simple trim to target duration."""
        current_time = 0.0
        kept_clips = []

        for clip in timeline.clips:
            if current_time + clip.duration <= target_duration:
                kept_clips.append(clip)
                current_time += clip.duration
            elif current_time < target_duration:
                # Partial clip
                remaining = target_duration - current_time
                clip.duration = remaining
                kept_clips.append(clip)
                break
            else:
                break

        timeline.clips = kept_clips
        timeline.duration = target_duration

    # Aspect ratio helpers

    def _calculate_smart_crop(
        self,
        clip: TimelineClip,
        current_ratio: float,
        target_ratio: float,
        safe_zones: dict[str, float]
    ) -> CropRegion:
        """Calculate intelligent crop region for clip."""
        # This would use AI to detect subjects/important areas
        # For now, return center crop with safe zones

        return self._calculate_center_crop(current_ratio, target_ratio)

    def _calculate_center_crop(
        self,
        current_ratio: float,
        target_ratio: float
    ) -> CropRegion:
        """Calculate center crop region."""
        if target_ratio > current_ratio:
            # Need to crop top/bottom
            new_height = 1.0 / target_ratio * current_ratio
            y_offset = (1.0 - new_height) / 2

            return CropRegion(
                x=0.0,
                y=y_offset,
                width=1.0,
                height=new_height,
                focus_point=(0.5, 0.5)
            )
        else:
            # Need to crop sides
            new_width = target_ratio / current_ratio
            x_offset = (1.0 - new_width) / 2

            return CropRegion(
                x=x_offset,
                y=0.0,
                width=new_width,
                height=1.0,
                focus_point=(0.5, 0.5)
            )

    # Pacing helpers

    def _increase_pace(self, timeline: Timeline, factor: float):
        """Increase pacing by reducing clip durations."""
        for clip in timeline.clips:
            clip.duration = clip.duration / factor

        # Recalculate positions
        current_time = 0.0
        for clip in timeline.clips:
            clip.start_time = current_time
            current_time += clip.duration

        timeline.duration = current_time

    def _decrease_pace(self, timeline: Timeline, factor: float):
        """Decrease pacing by extending clip durations."""
        self._increase_pace(timeline, 1.0 / factor)

    def _optimize_hook(self, timeline: Timeline, duration: float):
        """Optimize the opening hook for engagement."""
        # Make first few seconds more dynamic
        hook_clips = []
        current_time = 0.0

        for clip in timeline.clips:
            if current_time < duration:
                hook_clips.append(clip)
                current_time += clip.duration
            else:
                break

        # Make hook clips shorter and punchier
        for clip in hook_clips:
            clip.duration = min(clip.duration, 1.0)  # Max 1 second per clip

    # Feature helpers

    def _make_loopable(self, timeline: Timeline):
        """Make timeline loop seamlessly."""
        if len(timeline.clips) < 2:
            return

        # Match first and last clips for smooth loop
        first_clip = timeline.clips[0]
        last_clip = timeline.clips[-1]

        # Add transition metadata
        last_clip.metadata["loop_transition"] = True
        first_clip.metadata["loop_start"] = True

    def _identify_trend_points(self, timeline: Timeline) -> list[float]:
        """Identify points suitable for trend sound sync."""
        # Look for beat markers or significant moments
        trend_points = []

        for marker in timeline.markers:
            if marker.get("type") in ["beat", "drop", "hook"]:
                trend_points.append(marker["time"])

        return trend_points[:5]  # Limit to 5 sync points

    def _calculate_tap_zones(self, safe_zones: dict[str, float]) -> list[dict[str, Any]]:
        """Calculate interactive tap zones for stories."""
        zones = []

        # Poll zone (top)
        if "top" in safe_zones:
            zones.append({
                "type": "poll",
                "region": {
                    "x": 0.2,
                    "y": 0.1,
                    "width": 0.6,
                    "height": 0.15
                }
            })

        # Link zone (bottom)
        if "bottom" in safe_zones:
            zones.append({
                "type": "link",
                "region": {
                    "x": 0.2,
                    "y": 0.8,
                    "width": 0.6,
                    "height": 0.1
                }
            })

        return zones

    def get_platform_recommendations(
        self,
        timeline: Timeline
    ) -> dict[Platform, dict[str, Any]]:
        """Get recommendations for each platform based on timeline."""
        recommendations = {}

        for platform, spec in PLATFORM_SPECS.items():
            rec = {
                "suitable": True,
                "adjustments_needed": [],
                "optimization_tips": []
            }

            # Check duration
            if timeline.duration < spec.min_duration:
                rec["adjustments_needed"].append(
                    f"Extend to at least {spec.min_duration}s"
                )
            elif timeline.duration > spec.max_duration:
                rec["adjustments_needed"].append(
                    f"Trim to max {spec.max_duration}s"
                )

            # Check aspect ratio
            current_ratio = timeline.resolution[0] / timeline.resolution[1]
            target_ratio = spec.aspect_ratio[0] / spec.aspect_ratio[1]

            if abs(current_ratio - target_ratio) > 0.1:
                rec["adjustments_needed"].append(
                    f"Crop to {spec.aspect_ratio[0]}:{spec.aspect_ratio[1]}"
                )

            # Platform-specific tips
            if platform == Platform.TIKTOK:
                rec["optimization_tips"].append("Add trending sound sync points")
                rec["optimization_tips"].append("Optimize 3-second hook")
            elif platform == Platform.INSTAGRAM_REEL:
                rec["optimization_tips"].append("Keep key content in safe zones")
                rec["optimization_tips"].append("Add loop-friendly transitions")

            # Check if suitable
            if len(rec["adjustments_needed"]) > 3:
                rec["suitable"] = False

            recommendations[platform] = rec

        return recommendations
