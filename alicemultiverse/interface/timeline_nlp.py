"""Natural Language Processing for timeline edits.

This module enables chat-based timeline modifications using natural language commands
like "make the intro punchier" or "add breathing room after the drop".
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..workflows.video_export import Timeline, TimelineClip
from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class EditIntent(Enum):
    """Types of timeline edit intents."""
    PACE_CHANGE = "pace_change"  # Make faster/slower
    ADD_PAUSE = "add_pause"  # Add breathing room
    TRIM_SECTION = "trim_section"  # Shorten/extend parts
    REORDER = "reorder"  # Move clips around
    TRANSITION_CHANGE = "transition_change"  # Modify transitions
    SYNC_ADJUST = "sync_adjust"  # Align to beat/music
    REMOVE_CLIPS = "remove_clips"  # Delete clips
    DUPLICATE = "duplicate"  # Repeat clips/sections
    ENERGY_ADJUST = "energy_adjust"  # Change energy/intensity


@dataclass
class TimelineEdit:
    """Represents a parsed timeline edit command."""
    intent: EditIntent
    target_section: Optional[str] = None  # intro, outro, chorus, etc.
    target_clips: Optional[List[int]] = None  # Specific clip indices
    parameters: Dict[str, Any] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class TimelineNLPProcessor:
    """Process natural language commands for timeline editing."""
    
    # Command patterns for different intents
    PACE_PATTERNS = [
        (r"make (?:the )?(\w+) (faster|quicker|punchier|snappier)", "increase_pace"),
        (r"make (?:the )?(\w+) (slower|longer|breathe more)", "decrease_pace"),
        (r"speed up (?:the )?(\w+)", "increase_pace"),
        (r"slow down (?:the )?(\w+)", "decrease_pace"),
        (r"tighten (?:the )?(\w+)", "increase_pace"),
        (r"(faster|quicker) cuts? (?:in|for|during) (?:the )?(\w+)", "increase_pace"),
    ]
    
    PAUSE_PATTERNS = [
        (r"add (?:a )?(?:breathing room|pause|break|breather) (?:after|before) (?:the )?(\w+)", "add_pause"),
        (r"give (?:me |it )?(?:a moment|space|time) (?:after|before) (?:the )?(\w+)", "add_pause"),
        (r"hold on (?:the )?(\w+) (?:for )?(?:a bit)?(?:longer)?", "extend_hold"),
        (r"let (?:the )?(\w+) breathe", "add_pause"),
    ]
    
    SYNC_PATTERNS = [
        (r"(?:sync|align|match) (?:all )?cuts? to (?:the )?beat", "sync_to_beat"),
        (r"put (?:the )?(\w+) on (?:the )?beat", "sync_section_to_beat"),
        (r"hit (?:the )?beat (?:with|at) (?:the )?(\w+)", "sync_section_to_beat"),
        (r"make (?:it )?(?:more )?rhythmic", "sync_to_beat"),
    ]
    
    ENERGY_PATTERNS = [
        (r"(?:make|build) (?:more )?energy (?:in|during) (?:the )?(\w+)", "increase_energy"),
        (r"(?:add|create) (?:more )?(?:intensity|excitement) (?:in|to) (?:the )?(\w+)", "increase_energy"),
        (r"calm down (?:the )?(\w+)", "decrease_energy"),
        (r"(?:make )?(?:the )?(\w+) (?:more )?(?:chill|relaxed|mellow)", "decrease_energy"),
    ]
    
    SECTION_KEYWORDS = {
        "intro": ["intro", "introduction", "beginning", "start", "opening"],
        "outro": ["outro", "ending", "end", "conclusion", "finale"],
        "chorus": ["chorus", "hook", "refrain"],
        "verse": ["verse"],
        "bridge": ["bridge", "middle", "break"],
        "drop": ["drop", "beat drop", "bass drop"],
        "buildup": ["buildup", "build up", "build-up", "rise"],
    }
    
    def __init__(self):
        """Initialize the NLP processor."""
        self.section_map = self._build_section_map()
    
    def _build_section_map(self) -> Dict[str, str]:
        """Build a map of keywords to section names."""
        section_map = {}
        for section, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                section_map[keyword.lower()] = section
        return section_map
    
    def parse_command(self, command: str, timeline: Timeline) -> List[TimelineEdit]:
        """Parse a natural language command into timeline edits.
        
        Args:
            command: Natural language command
            timeline: Current timeline to edit
            
        Returns:
            List of parsed timeline edits
        """
        command = command.lower().strip()
        edits = []
        
        # Try to match pace change patterns
        for pattern, action in self.PACE_PATTERNS:
            match = re.search(pattern, command)
            if match:
                if len(match.groups()) == 2:
                    section = self._normalize_section(match.group(1))
                    modifier = match.group(2)
                else:
                    section = self._normalize_section(match.group(2) if len(match.groups()) > 1 else "all")
                    modifier = match.group(1) if match.groups() else action
                
                edits.append(TimelineEdit(
                    intent=EditIntent.PACE_CHANGE,
                    target_section=section,
                    parameters={
                        "action": action,
                        "modifier": modifier,
                        "factor": 1.5 if "faster" in modifier or "punchier" in modifier else 0.7
                    },
                    confidence=0.9
                ))
        
        # Try pause patterns
        for pattern, action in self.PAUSE_PATTERNS:
            match = re.search(pattern, command)
            if match:
                section = self._normalize_section(match.group(1))
                position = "after"  # Default
                
                if "before" in command:
                    position = "before"
                
                edits.append(TimelineEdit(
                    intent=EditIntent.ADD_PAUSE,
                    target_section=section,
                    parameters={
                        "action": action,
                        "position": position,
                        "duration": 1.0  # Default pause duration
                    },
                    confidence=0.85
                ))
        
        # Try sync patterns
        for pattern, action in self.SYNC_PATTERNS:
            match = re.search(pattern, command)
            if match:
                section = None
                if match.groups():
                    section = self._normalize_section(match.group(1))
                
                edits.append(TimelineEdit(
                    intent=EditIntent.SYNC_ADJUST,
                    target_section=section,
                    parameters={
                        "action": action,
                        "target": "beat"
                    },
                    confidence=0.9
                ))
        
        # Try energy patterns
        for pattern, action in self.ENERGY_PATTERNS:
            match = re.search(pattern, command)
            if match:
                section = self._normalize_section(match.group(1))
                
                edits.append(TimelineEdit(
                    intent=EditIntent.ENERGY_ADJUST,
                    target_section=section,
                    parameters={
                        "action": action,
                        "intensity": 1.5 if "increase" in action else 0.7
                    },
                    confidence=0.8
                ))
        
        # If no specific patterns matched, try generic interpretations
        if not edits:
            edits = self._parse_generic_command(command, timeline)
        
        return edits
    
    def _normalize_section(self, section_text: str) -> str:
        """Normalize section name from text."""
        section_text = section_text.lower().strip()
        
        # Check section map
        if section_text in self.section_map:
            return self.section_map[section_text]
        
        # Check if it's a direct section name
        for section in self.SECTION_KEYWORDS:
            if section_text == section:
                return section
        
        # Default to the text itself
        return section_text
    
    def _parse_generic_command(self, command: str, timeline: Timeline) -> List[TimelineEdit]:
        """Parse generic commands that don't match specific patterns."""
        edits = []
        
        # Check for transition requests
        if any(word in command for word in ["transition", "dissolve", "fade", "cut"]):
            transition_type = "cut"
            if "dissolve" in command:
                transition_type = "dissolve"
            elif "fade" in command:
                transition_type = "fade"
            
            edits.append(TimelineEdit(
                intent=EditIntent.TRANSITION_CHANGE,
                parameters={
                    "transition_type": transition_type,
                    "apply_to": "all" if "all" in command else "selected"
                },
                confidence=0.7
            ))
        
        # Check for removal requests
        if any(word in command for word in ["remove", "delete", "cut out", "take out"]):
            edits.append(TimelineEdit(
                intent=EditIntent.REMOVE_CLIPS,
                parameters={
                    "target": "selected"  # Would need UI selection
                },
                confidence=0.6
            ))
        
        # Check for duplication
        if any(word in command for word in ["duplicate", "repeat", "copy", "double"]):
            edits.append(TimelineEdit(
                intent=EditIntent.DUPLICATE,
                parameters={
                    "target": "selected"
                },
                confidence=0.7
            ))
        
        return edits
    
    def apply_edits(self, timeline: Timeline, edits: List[TimelineEdit]) -> Timeline:
        """Apply parsed edits to a timeline.
        
        Args:
            timeline: Timeline to modify
            edits: List of edits to apply
            
        Returns:
            Modified timeline
        """
        import copy
        modified_timeline = copy.deepcopy(timeline)
        
        for edit in edits:
            try:
                if edit.intent == EditIntent.PACE_CHANGE:
                    modified_timeline = self._apply_pace_change(modified_timeline, edit)
                elif edit.intent == EditIntent.ADD_PAUSE:
                    modified_timeline = self._apply_pause(modified_timeline, edit)
                elif edit.intent == EditIntent.SYNC_ADJUST:
                    modified_timeline = self._apply_sync_adjust(modified_timeline, edit)
                elif edit.intent == EditIntent.ENERGY_ADJUST:
                    modified_timeline = self._apply_energy_adjust(modified_timeline, edit)
                elif edit.intent == EditIntent.TRANSITION_CHANGE:
                    modified_timeline = self._apply_transition_change(modified_timeline, edit)
                else:
                    logger.warning(f"Unhandled edit intent: {edit.intent}")
            except Exception as e:
                logger.error(f"Failed to apply edit {edit.intent}: {e}")
        
        return modified_timeline
    
    def _apply_pace_change(self, timeline: Timeline, edit: TimelineEdit) -> Timeline:
        """Apply pace change to timeline."""
        factor = edit.parameters.get("factor", 1.0)
        target_clips = self._get_target_clips(timeline, edit)
        
        for clip_idx in target_clips:
            if 0 <= clip_idx < len(timeline.clips):
                clip = timeline.clips[clip_idx]
                # Adjust duration
                new_duration = clip.duration / factor
                
                # Ensure minimum duration
                new_duration = max(0.5, new_duration)
                
                # Update clip
                clip.duration = new_duration
                
                # Adjust subsequent clip positions
                if clip_idx < len(timeline.clips) - 1:
                    time_diff = clip.duration - (clip.end_time - clip.start_time)
                    for i in range(clip_idx + 1, len(timeline.clips)):
                        timeline.clips[i].start_time += time_diff
        
        # Update timeline duration
        if timeline.clips:
            timeline.duration = timeline.clips[-1].end_time
        
        return timeline
    
    def _apply_pause(self, timeline: Timeline, edit: TimelineEdit) -> Timeline:
        """Add pause to timeline."""
        pause_duration = edit.parameters.get("duration", 1.0)
        position = edit.parameters.get("position", "after")
        
        # Find target position
        target_clips = self._get_target_clips(timeline, edit)
        
        if target_clips and timeline.clips:
            if position == "after":
                # Add pause after the last target clip
                insert_after = max(target_clips)
                if insert_after < len(timeline.clips) - 1:
                    # Shift subsequent clips
                    for i in range(insert_after + 1, len(timeline.clips)):
                        timeline.clips[i].start_time += pause_duration
            else:  # before
                # Add pause before the first target clip
                insert_before = min(target_clips)
                if insert_before >= 0:
                    # Shift target and subsequent clips
                    for i in range(insert_before, len(timeline.clips)):
                        timeline.clips[i].start_time += pause_duration
        
        # Update timeline duration
        if timeline.clips:
            timeline.duration = timeline.clips[-1].end_time
        
        return timeline
    
    def _apply_sync_adjust(self, timeline: Timeline, edit: TimelineEdit) -> Timeline:
        """Adjust clips to sync with beats."""
        # This would require beat information from markers
        if not timeline.markers:
            logger.warning("No beat markers found in timeline")
            return timeline
        
        # Get beat markers
        beat_markers = [m for m in timeline.markers if m.get("type") == "beat"]
        if not beat_markers:
            logger.warning("No beat markers found")
            return timeline
        
        beat_times = [m["time"] for m in beat_markers]
        target_clips = self._get_target_clips(timeline, edit)
        
        for clip_idx in target_clips:
            if 0 <= clip_idx < len(timeline.clips):
                clip = timeline.clips[clip_idx]
                
                # Find nearest beat to clip start
                nearest_beat = min(beat_times, key=lambda b: abs(b - clip.start_time))
                
                # Adjust clip to start on beat
                time_shift = nearest_beat - clip.start_time
                clip.start_time = nearest_beat
                
                # Shift subsequent clips
                for i in range(clip_idx + 1, len(timeline.clips)):
                    timeline.clips[i].start_time += time_shift
        
        return timeline
    
    def _apply_energy_adjust(self, timeline: Timeline, edit: TimelineEdit) -> Timeline:
        """Adjust energy/intensity of section."""
        intensity = edit.parameters.get("intensity", 1.0)
        target_clips = self._get_target_clips(timeline, edit)
        
        # Energy adjustment through pace and transitions
        for clip_idx in target_clips:
            if 0 <= clip_idx < len(timeline.clips):
                clip = timeline.clips[clip_idx]
                
                if intensity > 1.0:  # Increase energy
                    # Shorter clips, faster transitions
                    clip.duration = clip.duration / 1.2
                    if clip.transition_out:
                        clip.transition_out_duration = max(0.2, clip.transition_out_duration * 0.7)
                else:  # Decrease energy
                    # Longer clips, slower transitions
                    clip.duration = clip.duration * 1.2
                    if clip.transition_out:
                        clip.transition_out_duration = min(2.0, clip.transition_out_duration * 1.3)
        
        return timeline
    
    def _apply_transition_change(self, timeline: Timeline, edit: TimelineEdit) -> Timeline:
        """Change transitions in timeline."""
        transition_type = edit.parameters.get("transition_type", "cut")
        apply_to = edit.parameters.get("apply_to", "all")
        
        if apply_to == "all":
            for i, clip in enumerate(timeline.clips):
                if i < len(timeline.clips) - 1:  # Not the last clip
                    clip.transition_out = transition_type
                    clip.transition_out_duration = 0.5 if transition_type != "cut" else 0.0
                if i > 0:  # Not the first clip
                    clip.transition_in = transition_type
                    clip.transition_in_duration = 0.5 if transition_type != "cut" else 0.0
        
        return timeline
    
    def _get_target_clips(self, timeline: Timeline, edit: TimelineEdit) -> List[int]:
        """Get indices of clips to target based on edit."""
        if edit.target_clips:
            return edit.target_clips
        
        if edit.target_section:
            # Map section names to clip ranges
            # This is simplified - in reality would need marker-based section detection
            total_clips = len(timeline.clips)
            
            if edit.target_section == "intro":
                # First 20% of clips
                return list(range(int(total_clips * 0.2)))
            elif edit.target_section == "outro":
                # Last 20% of clips
                return list(range(int(total_clips * 0.8), total_clips))
            elif edit.target_section == "all":
                return list(range(total_clips))
            else:
                # Middle sections - would need proper section detection
                return list(range(int(total_clips * 0.2), int(total_clips * 0.8)))
        
        # Default to all clips
        return list(range(len(timeline.clips)))
    
    def suggest_edits(self, timeline: Timeline) -> List[str]:
        """Suggest possible edits for the timeline.
        
        Args:
            timeline: Timeline to analyze
            
        Returns:
            List of suggested edit commands
        """
        suggestions = []
        
        # Analyze timeline characteristics
        avg_clip_duration = sum(c.duration for c in timeline.clips) / len(timeline.clips) if timeline.clips else 0
        has_transitions = any(c.transition_in or c.transition_out for c in timeline.clips)
        has_beat_markers = any(m.get("type") == "beat" for m in timeline.markers)
        
        # Suggest based on analysis
        if avg_clip_duration > 5.0:
            suggestions.append("Make the cuts faster for more energy")
            suggestions.append("Speed up the intro to grab attention")
        elif avg_clip_duration < 1.0:
            suggestions.append("Add breathing room after intense sections")
            suggestions.append("Slow down the pace for dramatic effect")
        
        if not has_transitions:
            suggestions.append("Add dissolve transitions for smoother flow")
        
        if has_beat_markers and not all(c.beat_aligned for c in timeline.clips):
            suggestions.append("Sync all cuts to the beat")
            suggestions.append("Match cuts to the rhythm")
        
        if len(timeline.clips) > 20:
            suggestions.append("Tighten the edit by removing weaker shots")
        
        return suggestions


def create_nlp_processor() -> TimelineNLPProcessor:
    """Create a timeline NLP processor instance."""
    return TimelineNLPProcessor()