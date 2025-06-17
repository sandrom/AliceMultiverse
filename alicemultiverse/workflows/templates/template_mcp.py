"""MCP tools for workflow templates."""

import logging
from typing import Any

from ..base import WorkflowContext
from ..executor import WorkflowExecutor
from .social_media import (
    InstagramReelTemplate,
    LinkedInVideoTemplate,
    SocialMediaTemplate,
    TikTokTemplate,
)
from .story_arc import DocumentaryStoryTemplate, StoryArcTemplate

logger = logging.getLogger(__name__)


async def create_story_arc_video(
    images: list[str],
    structure: str = "three_act",
    duration: float = 60.0,
    narrative_tags: dict[str, list[str]] | None = None,
    emotion_curve: str = "standard",
    music_file: str | None = None,
    voiceover_markers: bool = False,
    export_formats: list[str] | None = None
) -> dict[str, Any]:
    """Create a narrative-driven video using story arc template.
    
    Args:
        images: List of image paths
        structure: Story structure (three_act, five_act, heros_journey, kishoten, circular)
        duration: Target video duration in seconds
        narrative_tags: Tags describing story elements per image
        emotion_curve: Emotional progression (standard, intense, gentle)
        music_file: Optional music for pacing
        voiceover_markers: Add markers for voiceover timing
        export_formats: Export formats (edl, xml, json)
        
    Returns:
        Workflow execution results with timeline
    """
    try:
        # Create template
        template = StoryArcTemplate()

        # Prepare parameters
        params = {
            "images": images,
            "structure": structure,
            "duration": duration,
            "narrative_tags": narrative_tags or {},
            "emotion_curve": emotion_curve,
            "export_formats": export_formats or ["edl", "xml"]
        }

        if music_file:
            params["music_file"] = music_file

        if voiceover_markers:
            params["voiceover_markers"] = True

        # Create context and executor
        context = WorkflowContext(
            workflow_id=f"story_arc_{structure}",
            initial_params=params
        )

        executor = WorkflowExecutor()

        # Execute workflow
        result = await executor.execute_workflow(template, context)

        # Extract key results
        if result.success:
            timeline = result.results.get("generate_timeline", {})
            return {
                "success": True,
                "timeline": timeline.get("timeline", {}),
                "exports": timeline.get("exports", {}),
                "summary": timeline.get("summary", {}),
                "structure": structure,
                "duration": duration
            }
        else:
            return {
                "success": False,
                "error": result.error or "Workflow failed",
                "failed_step": result.failed_step
            }

    except Exception as e:
        logger.error(f"Failed to create story arc video: {e}")
        return {"success": False, "error": str(e)}


async def create_documentary_video(
    images: list[str],
    duration: float = 120.0,
    narrative_tags: dict[str, list[str]] | None = None,
    music_file: str | None = None,
    voiceover_markers: bool = True,
    export_formats: list[str] | None = None
) -> dict[str, Any]:
    """Create a documentary-style video.
    
    Args:
        images: List of image paths
        duration: Target video duration in seconds
        narrative_tags: Tags describing evidence/testimony per image
        music_file: Optional background music
        voiceover_markers: Add markers for narration (default True)
        export_formats: Export formats
        
    Returns:
        Workflow execution results
    """
    try:
        template = DocumentaryStoryTemplate()

        params = {
            "images": images,
            "structure": "three_act",  # Documentary uses simplified structure
            "duration": duration,
            "narrative_tags": narrative_tags or {},
            "emotion_curve": "gentle",  # Documentaries are more measured
            "voiceover_markers": voiceover_markers,
            "export_formats": export_formats or ["edl", "xml"]
        }

        if music_file:
            params["music_file"] = music_file

        context = WorkflowContext(
            workflow_id="documentary",
            initial_params=params
        )

        executor = WorkflowExecutor()
        result = await executor.execute_workflow(template, context)

        if result.success:
            timeline = result.results.get("generate_timeline", {})
            return {
                "success": True,
                "timeline": timeline.get("timeline", {}),
                "exports": timeline.get("exports", {}),
                "type": "documentary"
            }
        else:
            return {
                "success": False,
                "error": result.error or "Workflow failed"
            }

    except Exception as e:
        logger.error(f"Failed to create documentary video: {e}")
        return {"success": False, "error": str(e)}


async def create_social_media_video(
    platform: str,
    images: list[str],
    music_file: str | None = None,
    caption: str | None = None,
    hashtags: list[str] | None = None,
    style: str = "trending",
    duration: float | None = None,
    auto_optimize: bool = True
) -> dict[str, Any]:
    """Create a social media optimized video.
    
    Args:
        platform: Target platform (instagram_reel, tiktok, youtube_shorts, etc.)
        images: List of image paths
        music_file: Optional music track
        caption: Post caption/description
        hashtags: List of hashtags
        style: Content style (trending, educational, entertaining)
        duration: Optional duration (uses platform optimal if not set)
        auto_optimize: Automatically optimize for engagement
        
    Returns:
        Workflow execution results with platform export
    """
    try:
        # Select appropriate template
        if platform == "instagram_reel":
            template = InstagramReelTemplate()
        elif platform == "tiktok":
            template = TikTokTemplate()
        elif platform == "linkedin_video":
            template = LinkedInVideoTemplate()
        else:
            template = SocialMediaTemplate()

        params = {
            "platform": platform,
            "images": images,
            "style": style,
            "auto_optimize": auto_optimize
        }

        if music_file:
            params["music_file"] = music_file

        if caption:
            params["caption"] = caption

        if hashtags:
            params["hashtags"] = hashtags

        if duration:
            params["duration"] = duration

        context = WorkflowContext(
            workflow_id=f"social_{platform}",
            initial_params=params
        )

        executor = WorkflowExecutor()
        result = await executor.execute_workflow(template, context)

        if result.success:
            export = result.results.get("export_platform", {})
            return {
                "success": True,
                "export": export,
                "platform": platform,
                "optimizations": result.results.get("analyze_content", {}).get("optimizations", []),
                "preview": export.get("preview", {})
            }
        else:
            return {
                "success": False,
                "error": result.error or "Workflow failed"
            }

    except Exception as e:
        logger.error(f"Failed to create social media video: {e}")
        return {"success": False, "error": str(e)}


async def create_instagram_reel(
    images: list[str],
    music_file: str,
    caption: str | None = None,
    hashtags: list[str] | None = None,
    effects: list[str] | None = None,
    duration: float = 15.0
) -> dict[str, Any]:
    """Create an Instagram Reel with optimizations.
    
    Args:
        images: List of image paths
        music_file: Music track (required for Reels)
        caption: Reel caption
        hashtags: Hashtags for discovery
        effects: Instagram effects to apply
        duration: Reel duration (max 90 seconds)
        
    Returns:
        Reel export with Instagram features
    """
    params = {
        "effects": effects or ["zoom", "transition"],
        "stickers": [],
        "duration": min(duration, 90)  # Max 90 seconds
    }

    return await create_social_media_video(
        platform="instagram_reel",
        images=images,
        music_file=music_file,
        caption=caption,
        hashtags=hashtags,
        style="trending",
        **params
    )


async def create_tiktok_video(
    images: list[str],
    music_file: str | None = None,
    caption: str | None = None,
    hashtags: list[str] | None = None,
    challenges: list[str] | None = None,
    duet_ready: bool = False,
    duration: float = 30.0
) -> dict[str, Any]:
    """Create a TikTok video with trend integration.
    
    Args:
        images: List of image paths
        music_file: Optional trending sound
        caption: Video caption
        hashtags: Trending hashtags
        challenges: Hashtag challenges to join
        duet_ready: Prepare for duet format
        duration: Video duration (max 180 seconds)
        
    Returns:
        TikTok optimized export
    """
    params = {
        "challenges": challenges or [],
        "duet_ready": duet_ready,
        "duration": min(duration, 180)  # Max 3 minutes
    }

    return await create_social_media_video(
        platform="tiktok",
        images=images,
        music_file=music_file,
        caption=caption,
        hashtags=hashtags,
        style="trending",
        **params
    )


async def get_platform_specifications(
    platform: str | None = None
) -> dict[str, Any]:
    """Get specifications for social media platforms.
    
    Args:
        platform: Specific platform or None for all
        
    Returns:
        Platform specifications
    """
    from .social_media import PLATFORM_SPECS, SocialPlatform

    if platform:
        try:
            platform_enum = SocialPlatform(platform)
            spec = PLATFORM_SPECS.get(platform_enum)

            if spec:
                return {
                    "platform": platform,
                    "spec": {
                        "name": spec.name,
                        "aspect_ratio": spec.aspect_ratio,
                        "max_duration": spec.max_duration,
                        "optimal_duration": spec.optimal_duration,
                        "fps": spec.fps,
                        "max_file_size_mb": spec.max_file_size_mb,
                        "safe_zones": spec.safe_zones,
                        "features": spec.features,
                        "audio_required": spec.audio_required
                    }
                }
            else:
                return {"error": f"No specifications for {platform}"}

        except ValueError:
            return {"error": f"Unknown platform: {platform}"}
    else:
        # Return all platforms
        all_specs = {}
        for platform_enum, spec in PLATFORM_SPECS.items():
            all_specs[platform_enum.value] = {
                "name": spec.name,
                "aspect_ratio": spec.aspect_ratio,
                "optimal_duration": spec.optimal_duration,
                "features": spec.features
            }

        return {"platforms": all_specs}


async def suggest_story_structure(
    images: list[str],
    theme: str | None = None
) -> dict[str, Any]:
    """Suggest appropriate story structure based on content.
    
    Args:
        images: List of image paths
        theme: Optional theme hint
        
    Returns:
        Structure suggestions with reasoning
    """
    suggestions = []

    image_count = len(images)

    # Three act for most narratives
    if image_count >= 6:
        suggestions.append({
            "structure": "three_act",
            "reason": "Classic structure works well for most stories",
            "image_distribution": "25% setup, 50% confrontation, 25% resolution"
        })

    # Five act for complex narratives
    if image_count >= 15:
        suggestions.append({
            "structure": "five_act",
            "reason": "Complex narrative with multiple turning points",
            "image_distribution": "More nuanced pacing with climax emphasis"
        })

    # Hero's journey for adventure themes
    if theme and "adventure" in theme.lower():
        suggestions.append({
            "structure": "heros_journey",
            "reason": "Perfect for adventure and transformation stories",
            "image_distribution": "50% dedicated to trials and challenges"
        })

    # Circular for reflective pieces
    if theme and any(word in theme.lower() for word in ["reflect", "journey", "growth"]):
        suggestions.append({
            "structure": "circular",
            "reason": "Shows transformation by returning to beginning",
            "image_distribution": "Balanced with transformation emphasis"
        })

    return {
        "suggestions": suggestions,
        "image_count": image_count,
        "recommended": suggestions[0] if suggestions else None
    }


# Tool definitions for MCP registration
TEMPLATE_TOOLS = [
    {
        "name": "create_story_arc_video",
        "description": "Create a narrative-driven video with story structure",
        "input_schema": {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image paths"
                },
                "structure": {
                    "type": "string",
                    "description": "Story structure type",
                    "enum": ["three_act", "five_act", "heros_journey", "kishoten", "circular"],
                    "default": "three_act"
                },
                "duration": {
                    "type": "number",
                    "description": "Target duration in seconds",
                    "default": 60.0
                },
                "narrative_tags": {
                    "type": "object",
                    "description": "Story elements per image"
                },
                "emotion_curve": {
                    "type": "string",
                    "description": "Emotional progression",
                    "default": "standard"
                },
                "music_file": {
                    "type": "string",
                    "description": "Optional music file"
                },
                "voiceover_markers": {
                    "type": "boolean",
                    "description": "Add voiceover timing markers",
                    "default": False
                },
                "export_formats": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Export formats (edl, xml, json)"
                }
            },
            "required": ["images"]
        }
    },
    {
        "name": "create_documentary_video",
        "description": "Create a documentary-style video",
        "input_schema": {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image paths"
                },
                "duration": {
                    "type": "number",
                    "description": "Target duration in seconds",
                    "default": 120.0
                },
                "narrative_tags": {
                    "type": "object",
                    "description": "Evidence/testimony tags"
                },
                "music_file": {
                    "type": "string",
                    "description": "Optional background music"
                },
                "voiceover_markers": {
                    "type": "boolean",
                    "description": "Add narration markers",
                    "default": True
                },
                "export_formats": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Export formats"
                }
            },
            "required": ["images"]
        }
    },
    {
        "name": "create_social_media_video",
        "description": "Create a social media optimized video",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Target platform",
                    "enum": ["instagram_reel", "instagram_story", "tiktok", "youtube_shorts", "twitter_video", "linkedin_video"]
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image paths"
                },
                "music_file": {
                    "type": "string",
                    "description": "Optional music track"
                },
                "caption": {
                    "type": "string",
                    "description": "Post caption"
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hashtags"
                },
                "style": {
                    "type": "string",
                    "description": "Content style",
                    "enum": ["trending", "educational", "entertaining", "aesthetic", "tutorial"],
                    "default": "trending"
                },
                "duration": {
                    "type": "number",
                    "description": "Duration (uses platform optimal if not set)"
                },
                "auto_optimize": {
                    "type": "boolean",
                    "description": "Auto-optimize for engagement",
                    "default": True
                }
            },
            "required": ["platform", "images"]
        }
    },
    {
        "name": "create_instagram_reel",
        "description": "Create an Instagram Reel with optimizations",
        "input_schema": {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image paths"
                },
                "music_file": {
                    "type": "string",
                    "description": "Music track (required)"
                },
                "caption": {
                    "type": "string",
                    "description": "Reel caption"
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hashtags"
                },
                "effects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Effects to apply"
                },
                "duration": {
                    "type": "number",
                    "description": "Duration (max 90 seconds)",
                    "default": 15.0
                }
            },
            "required": ["images", "music_file"]
        }
    },
    {
        "name": "create_tiktok_video",
        "description": "Create a TikTok video with trend integration",
        "input_schema": {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image paths"
                },
                "music_file": {
                    "type": "string",
                    "description": "Trending sound"
                },
                "caption": {
                    "type": "string",
                    "description": "Video caption"
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hashtags"
                },
                "challenges": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Challenges to join"
                },
                "duet_ready": {
                    "type": "boolean",
                    "description": "Prepare for duet",
                    "default": False
                },
                "duration": {
                    "type": "number",
                    "description": "Duration (max 180 seconds)",
                    "default": 30.0
                }
            },
            "required": ["images"]
        }
    },
    {
        "name": "get_platform_specifications",
        "description": "Get social media platform specifications",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Platform name or None for all"
                }
            }
        }
    },
    {
        "name": "suggest_story_structure",
        "description": "Suggest story structure based on content",
        "input_schema": {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image paths"
                },
                "theme": {
                    "type": "string",
                    "description": "Optional theme hint"
                }
            },
            "required": ["images"]
        }
    }
]
