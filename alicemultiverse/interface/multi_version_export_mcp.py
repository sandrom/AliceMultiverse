"""MCP tools for multi-version export functionality."""

import json
import logging
from pathlib import Path
from typing import Any

from ..workflows.multi_version_export import PLATFORM_SPECS, MultiVersionExporter, Platform
from ..workflows.video_export import DaVinciResolveExporter, Timeline, TimelineClip

logger = logging.getLogger(__name__)

# Global exporter instance
_exporter: MultiVersionExporter | None = None


def get_exporter() -> MultiVersionExporter:
    """Get or create exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = MultiVersionExporter()
    return _exporter


async def create_platform_versions(
    timeline_data: dict[str, Any],
    platforms: list[str],
    smart_crop: bool = True,
    maintain_sync: bool = True
) -> dict[str, Any]:
    """
    Create platform-specific versions of a timeline.

    Args:
        timeline_data: Master timeline data
        platforms: List of platform names (instagram_reel, tiktok, etc.)
        smart_crop: Use AI to detect important regions
        maintain_sync: Try to keep music sync when adapting

    Returns:
        Platform versions with adapted timelines
    """
    try:
        exporter = get_exporter()

        # Convert timeline data to Timeline object
        from pathlib import Path

        clips = []
        for clip_data in timeline_data.get("clips", []):
            clip = TimelineClip(
                asset_path=Path(clip_data["asset_path"]),
                start_time=clip_data["start_time"],
                duration=clip_data["duration"],
                in_point=clip_data.get("in_point", 0.0),
                out_point=clip_data.get("out_point"),
                transition_in=clip_data.get("transition_in"),
                transition_in_duration=clip_data.get("transition_in_duration", 0.0),
                transition_out=clip_data.get("transition_out"),
                transition_out_duration=clip_data.get("transition_out_duration", 0.0),
                metadata=clip_data.get("metadata", {})
            )
            clips.append(clip)

        timeline = Timeline(
            name=timeline_data.get("name", "Timeline"),
            duration=timeline_data.get("duration", 0),
            frame_rate=timeline_data.get("frame_rate", 30),
            resolution=tuple(timeline_data.get("resolution", [1920, 1080])),
            clips=clips,
            markers=timeline_data.get("markers", []),
            audio_tracks=timeline_data.get("audio_tracks", []),
            metadata=timeline_data.get("metadata", {})
        )

        # Convert platform strings to enums
        platform_enums = []
        for platform_str in platforms:
            try:
                platform_enum = Platform(platform_str)
                platform_enums.append(platform_enum)
            except ValueError:
                logger.warning(f"Unknown platform: {platform_str}")

        if not platform_enums:
            return {
                "success": False,
                "error": "No valid platforms specified"
            }

        # Create versions
        versions = exporter.create_platform_versions(
            timeline=timeline,
            platforms=platform_enums,
            smart_crop=smart_crop,
            maintain_sync=maintain_sync
        )

        # Convert to response format
        result = {
            "success": True,
            "versions": {},
            "summary": {
                "platforms_created": len(versions),
                "master_duration": timeline.duration,
                "adaptations_applied": []
            }
        }

        for platform, version in versions.items():
            spec = version.spec

            # Convert timeline back to dict
            timeline_dict = {
                "name": version.timeline.name,
                "duration": version.timeline.duration,
                "frame_rate": version.timeline.frame_rate,
                "resolution": list(version.timeline.resolution),
                "clips": [
                    {
                        "asset_path": str(clip.asset_path),
                        "start_time": clip.start_time,
                        "duration": clip.duration,
                        "in_point": clip.in_point,
                        "out_point": clip.out_point,
                        "metadata": clip.metadata
                    }
                    for clip in version.timeline.clips
                ],
                "markers": version.timeline.markers,
                "metadata": version.timeline.metadata
            }

            # Add crop regions if any
            crop_regions = {}
            for clip_id, crop in version.crop_regions.items():
                crop_regions[clip_id] = {
                    "x": crop.x,
                    "y": crop.y,
                    "width": crop.width,
                    "height": crop.height,
                    "focus_point": crop.focus_point
                }

            result["versions"][platform.value] = {
                "platform_name": spec.name,
                "timeline": timeline_dict,
                "crop_regions": crop_regions,
                "specifications": {
                    "aspect_ratio": f"{spec.aspect_ratio[0]}:{spec.aspect_ratio[1]}",
                    "resolution": f"{spec.resolution[0]}x{spec.resolution[1]}",
                    "duration_range": f"{spec.min_duration}-{spec.max_duration}s",
                    "features": spec.features
                }
            }

            # Track adaptations
            if abs(version.timeline.duration - timeline.duration) > 0.1:
                result["summary"]["adaptations_applied"].append(
                    f"{platform.value}: Duration adjusted"
                )
            if crop_regions:
                result["summary"]["adaptations_applied"].append(
                    f"{platform.value}: Aspect ratio cropped"
                )

        return result

    except Exception as e:
        logger.error(f"Failed to create platform versions: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_platform_recommendations(
    timeline_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Get recommendations for each platform based on timeline analysis.

    Args:
        timeline_data: Timeline to analyze

    Returns:
        Platform-specific recommendations and suitability
    """
    try:
        exporter = get_exporter()

        # Convert to Timeline object (similar to above)
        from pathlib import Path

        clips = []
        for clip_data in timeline_data.get("clips", []):
            clip = TimelineClip(
                asset_path=Path(clip_data["asset_path"]),
                start_time=clip_data["start_time"],
                duration=clip_data["duration"],
                metadata=clip_data.get("metadata", {})
            )
            clips.append(clip)

        timeline = Timeline(
            name=timeline_data.get("name", "Timeline"),
            duration=timeline_data.get("duration", 0),
            resolution=tuple(timeline_data.get("resolution", [1920, 1080])),
            clips=clips,
            markers=timeline_data.get("markers", [])
        )

        # Get recommendations
        recommendations = exporter.get_platform_recommendations(timeline)

        # Format response
        result = {
            "success": True,
            "timeline_info": {
                "duration": timeline.duration,
                "resolution": f"{timeline.resolution[0]}x{timeline.resolution[1]}",
                "aspect_ratio": f"{timeline.resolution[0]/timeline.resolution[1]:.2f}",
                "clip_count": len(timeline.clips)
            },
            "recommendations": {}
        }

        for platform, rec in recommendations.items():
            result["recommendations"][platform.value] = {
                "platform_name": PLATFORM_SPECS[platform].name,
                "suitable": rec["suitable"],
                "adjustments_needed": rec["adjustments_needed"],
                "optimization_tips": rec["optimization_tips"],
                "specs": {
                    "target_aspect": f"{PLATFORM_SPECS[platform].aspect_ratio[0]}:{PLATFORM_SPECS[platform].aspect_ratio[1]}",
                    "duration_range": f"{PLATFORM_SPECS[platform].min_duration}-{PLATFORM_SPECS[platform].max_duration}s",
                    "preferred_duration": f"{PLATFORM_SPECS[platform].preferred_duration}s"
                }
            }

        # Add best platforms
        suitable_platforms = [
            p for p, r in result["recommendations"].items()
            if r["suitable"]
        ]

        result["summary"] = {
            "best_platforms": suitable_platforms[:3],
            "requires_major_changes": [
                p for p, r in result["recommendations"].items()
                if not r["suitable"]
            ]
        }

        return result

    except Exception as e:
        logger.error(f"Failed to get platform recommendations: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def export_platform_version(
    platform: str,
    timeline_data: dict[str, Any],
    output_dir: str | None = None,
    format: str = "json"
) -> dict[str, Any]:
    """
    Export a single platform version with proper naming.

    Args:
        platform: Target platform
        timeline_data: Platform-adapted timeline
        output_dir: Output directory
        format: Export format (json, edl, xml)

    Returns:
        Export result with file paths
    """
    try:
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path.cwd() / "exports"
            output_path.mkdir(exist_ok=True)

        # Generate filename
        timeline_name = timeline_data.get("name", "timeline").replace(" ", "_")
        timestamp = timeline_data.get("metadata", {}).get("export_timestamp", "")
        filename = f"{timeline_name}_{platform}_{timestamp}"

        if format == "json":
            # Export timeline data
            file_path = output_path / f"{filename}.json"
            with open(file_path, 'w') as f:
                json.dump(timeline_data, f, indent=2)

            return {
                "success": True,
                "format": "json",
                "file_path": str(file_path),
                "platform": platform
            }

        elif format == "edl":
            # Convert to Timeline object and export EDL
            from pathlib import Path

            from ..workflows.video_export import Timeline, TimelineClip

            clips = []
            for clip_data in timeline_data.get("clips", []):
                clips.append(TimelineClip(
                    asset_path=Path(clip_data["asset_path"]),
                    start_time=clip_data["start_time"],
                    duration=clip_data["duration"]
                ))

            timeline = Timeline(
                name=timeline_data.get("name", "Timeline"),
                duration=timeline_data.get("duration", 0),
                clips=clips
            )

            file_path = output_path / f"{filename}.edl"
            exporter = DaVinciResolveExporter()
            success = exporter.export_edl(timeline, file_path)

            return {
                "success": success,
                "format": "edl",
                "file_path": str(file_path),
                "platform": platform
            }

        else:
            return {
                "success": False,
                "error": f"Unsupported format: {format}"
            }

    except Exception as e:
        logger.error(f"Failed to export platform version: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def batch_export_all_platforms(
    timeline_data: dict[str, Any],
    platforms: list[str],
    output_dir: str | None = None,
    format: str = "json",
    create_master: bool = True
) -> dict[str, Any]:
    """
    Create and export all platform versions in one operation.

    Args:
        timeline_data: Master timeline
        platforms: List of platforms to export
        output_dir: Output directory
        format: Export format
        create_master: Also export master version

    Returns:
        Export results for all platforms
    """
    try:
        # Add timestamp for consistent naming
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        timeline_data.setdefault("metadata", {})["export_timestamp"] = timestamp

        # Create platform versions
        versions_result = await create_platform_versions(
            timeline_data=timeline_data,
            platforms=platforms,
            smart_crop=True,
            maintain_sync=True
        )

        if not versions_result["success"]:
            return versions_result

        # Export each version
        export_results = {}

        # Export master if requested
        if create_master:
            master_result = await export_platform_version(
                platform="master",
                timeline_data=timeline_data,
                output_dir=output_dir,
                format=format
            )
            export_results["master"] = master_result

        # Export platform versions
        for platform, version_data in versions_result["versions"].items():
            export_result = await export_platform_version(
                platform=platform,
                timeline_data=version_data["timeline"],
                output_dir=output_dir,
                format=format
            )
            export_results[platform] = export_result

        # Summary
        successful_exports = sum(
            1 for r in export_results.values() if r.get("success", False)
        )

        return {
            "success": successful_exports > 0,
            "exports": export_results,
            "summary": {
                "total_exports": len(export_results),
                "successful": successful_exports,
                "failed": len(export_results) - successful_exports,
                "output_directory": output_dir or "exports",
                "timestamp": timestamp
            }
        }

    except Exception as e:
        logger.error(f"Failed to batch export platforms: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_available_platforms() -> dict[str, Any]:
    """Get list of available platforms with their specifications."""
    platforms = {}

    for platform in Platform:
        spec = PLATFORM_SPECS[platform]
        platforms[platform.value] = {
            "name": spec.name,
            "aspect_ratio": f"{spec.aspect_ratio[0]}:{spec.aspect_ratio[1]}",
            "resolution": f"{spec.resolution[0]}x{spec.resolution[1]}",
            "duration": {
                "min": spec.min_duration,
                "max": spec.max_duration,
                "preferred": spec.preferred_duration
            },
            "features": spec.features,
            "file_size_limit_mb": spec.file_size_limit_mb
        }

    return {
        "success": True,
        "platforms": platforms,
        "categories": {
            "vertical_short": ["instagram_reel", "instagram_story", "tiktok", "youtube_shorts"],
            "square": ["instagram_post"],
            "horizontal": ["youtube", "twitter"],
            "archival": ["master"]
        }
    }
