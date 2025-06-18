"""MCP tools for natural language timeline editing."""

import logging
from typing import Any

from .timeline_nlp import TimelineNLPProcessor
from .timeline_preview_mcp import update_preview_timeline

logger = logging.getLogger(__name__)

# Global NLP processor instance
_nlp_processor: TimelineNLPProcessor | None = None


def get_nlp_processor() -> TimelineNLPProcessor:
    """Get or create NLP processor instance."""
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = TimelineNLPProcessor()
    return _nlp_processor


async def process_timeline_command(
    command: str,
    timeline_data: dict[str, Any],
    session_id: str | None = None,
    preview: bool = True
) -> dict[str, Any]:
    """
    Process a natural language command to edit a timeline.

    Args:
        command: Natural language command (e.g., "make the intro punchier")
        timeline_data: Timeline data dictionary
        session_id: Optional preview session ID to update
        preview: Whether to show preview of changes

    Returns:
        Result with applied edits and suggestions
    """
    try:
        processor = get_nlp_processor()

        # Convert dict to Timeline object
        from pathlib import Path

        from ..workflows.video_export import Timeline, TimelineClip

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

        # Parse command
        edits = processor.parse_command(command, timeline)

        if not edits:
            # Try to provide helpful suggestions
            suggestions = processor.suggest_edits(timeline)
            return {
                "success": False,
                "message": "I couldn't understand that command. Try one of these:",
                "suggestions": suggestions[:5],
                "original_command": command
            }

        # Apply edits
        modified_timeline = processor.apply_edits(timeline, edits)

        # Convert back to dict
        modified_data = {
            "name": modified_timeline.name,
            "duration": modified_timeline.duration,
            "frame_rate": modified_timeline.frame_rate,
            "resolution": list(modified_timeline.resolution),
            "clips": [
                {
                    "asset_path": str(clip.asset_path),
                    "start_time": clip.start_time,
                    "duration": clip.duration,
                    "in_point": clip.in_point,
                    "out_point": clip.out_point,
                    "transition_in": clip.transition_in,
                    "transition_in_duration": clip.transition_in_duration,
                    "transition_out": clip.transition_out,
                    "transition_out_duration": clip.transition_out_duration,
                    "metadata": clip.metadata
                }
                for clip in modified_timeline.clips
            ],
            "markers": modified_timeline.markers,
            "audio_tracks": modified_timeline.audio_tracks,
            "metadata": modified_timeline.metadata
        }

        # Update preview if session provided
        if session_id and preview:
            # Convert edits to preview operations
            # This is simplified - would need more sophisticated mapping
            preview_result = await update_preview_timeline(
                session_id=session_id,
                operation="natural_language",
                clips=[]  # Would need to convert edits to clip updates
            )

            return {
                "success": True,
                "message": f"Applied: {command}",
                "edits_applied": [
                    {
                        "intent": edit.intent.value,
                        "target": edit.target_section,
                        "confidence": edit.confidence
                    }
                    for edit in edits
                ],
                "timeline": modified_data,
                "preview_updated": preview_result.get("success", False)
            }
        else:
            return {
                "success": True,
                "message": f"Applied: {command}",
                "edits_applied": [
                    {
                        "intent": edit.intent.value,
                        "target": edit.target_section,
                        "confidence": edit.confidence
                    }
                    for edit in edits
                ],
                "timeline": modified_data
            }

    except Exception as e:
        logger.error(f"Failed to process timeline command: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command
        }


async def suggest_timeline_edits(
    timeline_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Get AI-powered suggestions for timeline improvements.

    Args:
        timeline_data: Timeline data dictionary

    Returns:
        Suggested edit commands and analysis
    """
    try:
        processor = get_nlp_processor()

        # Convert to Timeline object (similar to above)
        from pathlib import Path

        from ..workflows.video_export import Timeline, TimelineClip

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
            clips=clips,
            markers=timeline_data.get("markers", [])
        )

        # Get suggestions
        suggestions = processor.suggest_edits(timeline)

        # Analyze timeline
        average_clip_duration = sum(c.duration for c in timeline.clips) / len(timeline.clips) if timeline.clips else 0
        analysis = {
            "clip_count": len(timeline.clips),
            "total_duration": timeline.duration,
            "average_clip_duration": average_clip_duration,
            "has_transitions": Any(c.transition_in or c.transition_out for c in timeline.clips),
            "has_beat_markers": Any(m.get("type") == "beat" for m in timeline.markers),
            "pace": "fast" if average_clip_duration < 2 else "medium" if average_clip_duration < 4 else "slow"
        }

        return {
            "success": True,
            "suggestions": suggestions,
            "analysis": analysis,
            "example_commands": [
                "Make the intro faster",
                "Add breathing room after the drop",
                "Sync all cuts to the beat",
                "Add dissolve transitions",
                "Tighten the middle section"
            ]
        }

    except Exception as e:
        logger.error(f"Failed to suggest timeline edits: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def batch_timeline_edits(
    commands: list[str],
    timeline_data: dict[str, Any],
    session_id: str | None = None
) -> dict[str, Any]:
    """
    Apply multiple natural language commands in sequence.

    Args:
        commands: List of commands to apply
        timeline_data: Timeline data dictionary
        session_id: Optional preview session ID

    Returns:
        Result with all applied edits
    """
    results = []
    current_timeline = timeline_data

    for i, command in enumerate(commands):
        result = await process_timeline_command(
            command=command,
            timeline_data=current_timeline,
            session_id=session_id,
            preview=(i == len(commands) - 1)  # Only preview on last command
        )

        results.append({
            "command": command,
            "success": result["success"],
            "message": result.get("message", ""),
            "edits": result.get("edits_applied", [])
        })

        if result["success"]:
            current_timeline = result["timeline"]
        else:
            # Stop on first failure
            break

    return {
        "success": all(r["success"] for r in results),
        "commands_processed": len([r for r in results if r["success"]]),
        "total_commands": len(commands),
        "results": results,
        "final_timeline": current_timeline
    }


# Example usage patterns
EXAMPLE_COMMANDS = {
    "pace": [
        "Make the intro punchier",
        "Speed up the middle section",
        "Slow down the outro",
        "Tighten the entire edit",
        "Make faster cuts during the chorus"
    ],
    "rhythm": [
        "Sync all cuts to the beat",
        "Put the drops on the beat",
        "Make it more rhythmic",
        "Align transitions with the music"
    ],
    "energy": [
        "Build more energy in the buildup",
        "Add intensity to the chorus",
        "Calm down the bridge",
        "Make the outro more chill"
    ],
    "space": [
        "Add breathing room after the drop",
        "Give me a moment before the chorus",
        "Hold on the hero shot longer",
        "Let the intro breathe"
    ],
    "transitions": [
        "Add dissolve transitions",
        "Use cuts instead of fades",
        "Make all transitions faster",
        "Remove transitions"
    ]
}


def get_command_examples(category: str | None = None) -> dict[str, list[str]]:
    """Get example commands for natural language editing.

    Args:
        category: Optional category filter

    Returns:
        Dictionary of example commands by category
    """
    if category and category in EXAMPLE_COMMANDS:
        return {category: EXAMPLE_COMMANDS[category]}
    return EXAMPLE_COMMANDS
