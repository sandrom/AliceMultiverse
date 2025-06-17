"""Timeline manipulation operations."""

import copy
from dataclasses import asdict

from ...workflows.video_export import Timeline


class TimelineOperationsMixin:
    """Mixin for timeline manipulation operations."""

    def _timeline_to_dict(self, timeline: Timeline) -> dict:
        """Convert Timeline object to dictionary."""
        result = asdict(timeline)
        # Convert Path objects to strings
        for clip in result.get("clips", []):
            if "asset_path" in clip:
                clip["asset_path"] = str(clip["asset_path"])
        return result

    def _apply_timeline_operation(self, timeline: Timeline, operation: str, clip_updates: list[dict]) -> Timeline:
        """Apply an operation to the timeline."""
        # Create a copy of the timeline
        new_timeline = copy.deepcopy(timeline)

        if operation == "reorder":
            # Reorder clips based on new positions
            clip_map = {i: clip for i, clip in enumerate(new_timeline.clips)}
            new_clips = []

            for update in clip_updates:
                old_index = update.get("old_index")
                new_index = update.get("new_index")
                if old_index is not None and old_index in clip_map:
                    clip = clip_map[old_index]
                    # Update start time based on new position
                    if new_index > 0 and new_index <= len(new_clips):
                        prev_clip = new_clips[new_index - 1]
                        clip.start_time = prev_clip.end_time
                    else:
                        clip.start_time = 0
                    new_clips.insert(new_index, clip)

            new_timeline.clips = new_clips

        elif operation == "trim":
            # Trim clip durations
            for update in clip_updates:
                clip_index = update.get("index")
                if 0 <= clip_index < len(new_timeline.clips):
                    clip = new_timeline.clips[clip_index]
                    if "in_point" in update:
                        clip.in_point = update["in_point"]
                    if "out_point" in update:
                        clip.out_point = update["out_point"]
                    if "duration" in update:
                        clip.duration = update["duration"]

        elif operation == "add_transition":
            # Add transitions between clips
            for update in clip_updates:
                clip_index = update.get("index")
                if 0 <= clip_index < len(new_timeline.clips):
                    clip = new_timeline.clips[clip_index]
                    if "transition_in" in update:
                        clip.transition_in = update["transition_in"]
                        clip.transition_in_duration = update.get("transition_in_duration", 1.0)
                    if "transition_out" in update:
                        clip.transition_out = update["transition_out"]
                        clip.transition_out_duration = update.get("transition_out_duration", 1.0)

        elif operation == "adjust_timing":
            # Adjust clip timing
            for update in clip_updates:
                clip_index = update.get("index")
                if 0 <= clip_index < len(new_timeline.clips):
                    clip = new_timeline.clips[clip_index]
                    if "start_time" in update:
                        clip.start_time = update["start_time"]
                    if "speed" in update:
                        clip.speed = update["speed"]
                        # Adjust duration based on speed
                        if clip.speed != 1.0:
                            clip.duration = clip.duration / clip.speed

        elif operation == "add_effect":
            # Add effects to clips
            for update in clip_updates:
                clip_index = update.get("index")
                if 0 <= clip_index < len(new_timeline.clips):
                    clip = new_timeline.clips[clip_index]
                    if "effects" not in clip.metadata:
                        clip.metadata["effects"] = []

                    effect = update.get("effect", {})
                    if effect:
                        clip.metadata["effects"].append(effect)

        elif operation == "remove_clip":
            # Remove clips
            indices_to_remove = sorted([u.get("index") for u in clip_updates if "index" in u], reverse=True)
            for index in indices_to_remove:
                if 0 <= index < len(new_timeline.clips):
                    del new_timeline.clips[index]

        elif operation == "duplicate_clip":
            # Duplicate clips
            for update in clip_updates:
                clip_index = update.get("index")
                if 0 <= clip_index < len(new_timeline.clips):
                    original_clip = new_timeline.clips[clip_index]
                    duplicated_clip = copy.deepcopy(original_clip)
                    # Place after original
                    duplicated_clip.start_time = original_clip.end_time
                    new_timeline.clips.insert(clip_index + 1, duplicated_clip)

        # Recalculate timeline duration
        if new_timeline.clips:
            new_timeline.duration = max(clip.end_time for clip in new_timeline.clips)

        return new_timeline
