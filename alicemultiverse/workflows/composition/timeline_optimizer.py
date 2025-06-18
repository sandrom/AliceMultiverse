"""Timeline optimizer that applies composition feedback to improve flow."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..video_export import Timeline, TimelineClip
from .composition_analyzer import CompositionAnalyzer
from .flow_analyzer import FlowAnalyzer, FlowSuggestion, SuggestionType

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Strategies for timeline optimization."""
    MINIMAL = "minimal"  # Only critical fixes
    BALANCED = "balanced"  # Balance between fixes and original vision
    AGGRESSIVE = "aggressive"  # Maximum optimization
    PRESERVE_INTENT = "preserve_intent"  # Maintain original artistic intent
    ENERGY_FOCUSED = "energy_focused"  # Optimize for energy flow
    NARRATIVE_FOCUSED = "narrative_focused"  # Optimize for story flow


@dataclass
class OptimizationResult:
    """Result of timeline optimization."""
    optimized_timeline: Timeline
    changes_made: list[str]
    improvement_score: float
    preserved_elements: list[str]
    warnings: list[str]


class TimelineOptimizer:
    """Optimize timelines based on composition and flow analysis."""

    def __init__(
        self,
        flow_analyzer: FlowAnalyzer | None = None,
        composition_analyzer: CompositionAnalyzer | None = None,
    ):
        """Initialize the timeline optimizer.

        Args:
            flow_analyzer: Flow analyzer instance
            composition_analyzer: Composition analyzer instance
        """
        self.flow_analyzer = flow_analyzer or FlowAnalyzer()
        self.composition_analyzer = composition_analyzer or CompositionAnalyzer()

    async def optimize_timeline(
        self,
        timeline: Timeline,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
        preserve_clips: list[int] | None = None,
        target_duration: float | None = None,
    ) -> OptimizationResult:
        """Optimize timeline based on composition analysis.

        Args:
            timeline: Timeline to optimize
            strategy: Optimization strategy
            preserve_clips: Indices of clips to preserve
            target_duration: Target duration to achieve

        Returns:
            Optimization result
        """
        # Analyze current timeline
        issues, suggestions = await self.flow_analyzer.analyze_timeline_flow(timeline)

        # Create a copy to modify
        optimized = self._copy_timeline(timeline)

        # Track changes
        changes_made = []
        preserved_elements = []
        warnings = []

        # Apply optimizations based on strategy
        if strategy == OptimizationStrategy.MINIMAL:
            # Only fix critical issues
            critical_suggestions = [s for s in suggestions if s.priority > 0.8]
            changes_made.extend(
                await self._apply_suggestions(
                    optimized, critical_suggestions, preserve_clips
                )
            )

        elif strategy == OptimizationStrategy.AGGRESSIVE:
            # Apply all suggestions
            changes_made.extend(
                await self._apply_suggestions(
                    optimized, suggestions, preserve_clips
                )
            )

        elif strategy == OptimizationStrategy.BALANCED:
            # Apply suggestions with priority > 0.5
            balanced_suggestions = [s for s in suggestions if s.priority > 0.5]
            changes_made.extend(
                await self._apply_suggestions(
                    optimized, balanced_suggestions, preserve_clips
                )
            )

        elif strategy == OptimizationStrategy.PRESERVE_INTENT:
            # Only apply non-destructive suggestions
            safe_suggestions = [
                s for s in suggestions
                if s.suggestion_type not in [
                    SuggestionType.REMOVE_CLIP,
                    SuggestionType.REORDER_CLIPS,
                ]
            ]
            changes_made.extend(
                await self._apply_suggestions(
                    optimized, safe_suggestions, preserve_clips
                )
            )
            preserved_elements.append("Original clip order maintained")

        elif strategy == OptimizationStrategy.ENERGY_FOCUSED:
            # Focus on energy flow optimizations
            energy_suggestions = [
                s for s in suggestions
                if any(issue.issue_type.value.startswith("energy")
                      for issue in issues
                      if any(clip in s.target_clips for clip in issue.affected_clips))
            ]
            changes_made.extend(
                await self._apply_suggestions(
                    optimized, energy_suggestions, preserve_clips
                )
            )

        elif strategy == OptimizationStrategy.NARRATIVE_FOCUSED:
            # Focus on narrative flow
            narrative_suggestions = [
                s for s in suggestions
                if any(issue.issue_type.value in ["narrative_break", "style_mismatch", "repetitive_sequence"]
                      for issue in issues
                      if any(clip in s.target_clips for clip in issue.affected_clips))
            ]
            changes_made.extend(
                await self._apply_suggestions(
                    optimized, narrative_suggestions, preserve_clips
                )
            )

        # Adjust for target duration if specified
        if target_duration:
            duration_changes = self._adjust_duration(
                optimized, target_duration, preserve_clips
            )
            changes_made.extend(duration_changes)

        # Validate timeline consistency
        validation_warnings = self._validate_timeline(optimized)
        warnings.extend(validation_warnings)

        # Calculate improvement score
        improvement_score = await self._calculate_improvement(timeline, optimized)

        # Record preserved elements
        if preserve_clips:
            preserved_elements.append(
                f"Preserved {len(preserve_clips)} clips as requested"
            )

        return OptimizationResult(
            optimized_timeline=optimized,
            changes_made=changes_made,
            improvement_score=improvement_score,
            preserved_elements=preserved_elements,
            warnings=warnings,
        )

    def _copy_timeline(self, timeline: Timeline) -> Timeline:
        """Create a deep copy of timeline."""
        new_timeline = Timeline(
            name=f"{timeline.name}_optimized",
            duration=timeline.duration,
            frame_rate=timeline.frame_rate,
            resolution=timeline.resolution,
        )

        # Copy clips
        for clip in timeline.clips:
            new_clip = TimelineClip(
                asset_path=clip.asset_path,
                start_time=clip.start_time,
                duration=clip.duration,
                transition_in=clip.transition_in,
                transition_in_duration=clip.transition_in_duration,
                transition_out=clip.transition_out,
                transition_out_duration=clip.transition_out_duration,
                effects=clip.effects.copy() if clip.effects else [],
            )
            new_timeline.clips.append(new_clip)

        # Copy other attributes
        new_timeline.audio_track = timeline.audio_track
        new_timeline.markers = timeline.markers.copy() if timeline.markers else []
        new_timeline.metadata = timeline.metadata.copy() if timeline.metadata else {}

        return new_timeline

    async def _apply_suggestions(
        self,
        timeline: Timeline,
        suggestions: list[FlowSuggestion],
        preserve_clips: list[int] | None = None,
    ) -> list[str]:
        """Apply suggestions to timeline."""
        changes = []
        preserve_clips = preserve_clips or []

        # Sort suggestions by type to apply in logical order
        # 1. Duration adjustments
        # 2. Transitions
        # 3. Effects
        # 4. Reordering
        # 5. Clip removal/addition

        suggestion_order = [
            SuggestionType.ADJUST_DURATION,
            SuggestionType.ADD_TRANSITION,
            SuggestionType.CHANGE_TRANSITION,
            SuggestionType.ADD_EFFECT,
            SuggestionType.ADJUST_TIMING,
            SuggestionType.SPLIT_CLIP,
            SuggestionType.MERGE_CLIPS,
            SuggestionType.REORDER_CLIPS,
            SuggestionType.INSERT_CLIP,
            SuggestionType.REMOVE_CLIP,
        ]

        for sug_type in suggestion_order:
            type_suggestions = [s for s in suggestions if s.suggestion_type == sug_type]

            for suggestion in type_suggestions:
                # Check if affects preserved clips
                if any(clip_idx in preserve_clips for clip_idx in suggestion.target_clips):
                    continue

                # Apply suggestion
                change = self._apply_single_suggestion(timeline, suggestion)
                if change:
                    changes.append(change)

        return changes

    def _apply_single_suggestion(
        self,
        timeline: Timeline,
        suggestion: FlowSuggestion,
    ) -> str | None:
        """Apply a single suggestion to timeline."""
        try:
            if suggestion.suggestion_type == SuggestionType.ADJUST_DURATION:
                clip_idx = suggestion.target_clips[0]
                if 0 <= clip_idx < len(timeline.clips):
                    old_duration = timeline.clips[clip_idx].duration
                    new_duration = suggestion.parameters.get("new_duration", old_duration)
                    timeline.clips[clip_idx].duration = new_duration

                    # Adjust subsequent clip times
                    time_diff = new_duration - old_duration
                    for i in range(clip_idx + 1, len(timeline.clips)):
                        timeline.clips[i].start_time += time_diff

                    timeline.duration += time_diff
                    return f"Adjusted clip {clip_idx+1} duration from {old_duration:.1f}s to {new_duration:.1f}s"

            elif suggestion.suggestion_type == SuggestionType.ADD_TRANSITION:
                if len(suggestion.target_clips) >= 2:
                    clip1_idx, clip2_idx = suggestion.target_clips[:2]
                    if 0 <= clip1_idx < len(timeline.clips) and 0 <= clip2_idx < len(timeline.clips):
                        transition_type = suggestion.parameters.get("transition_type", "fade")
                        duration = suggestion.parameters.get("duration", 1.0)

                        timeline.clips[clip1_idx].transition_out = transition_type
                        timeline.clips[clip1_idx].transition_out_duration = duration
                        timeline.clips[clip2_idx].transition_in = transition_type
                        timeline.clips[clip2_idx].transition_in_duration = duration

                        return f"Added {transition_type} transition between clips {clip1_idx+1} and {clip2_idx+1}"

            elif suggestion.suggestion_type == SuggestionType.ADD_EFFECT:
                clip_idx = suggestion.target_clips[0]
                if 0 <= clip_idx < len(timeline.clips):
                    effect = suggestion.parameters.get("effect", "")
                    if effect:
                        if not timeline.clips[clip_idx].effects:
                            timeline.clips[clip_idx].effects = []
                        timeline.clips[clip_idx].effects.append(effect)
                        return f"Added {effect} effect to clip {clip_idx+1}"

            elif suggestion.suggestion_type == SuggestionType.REORDER_CLIPS:
                if len(suggestion.target_clips) >= 1:
                    from_idx = suggestion.target_clips[0]
                    to_idx = suggestion.parameters.get("move_to", from_idx)

                    if (0 <= from_idx < len(timeline.clips) and
                        0 <= to_idx <= len(timeline.clips) and
                        from_idx != to_idx):

                        # Remove and reinsert clip
                        clip = timeline.clips.pop(from_idx)
                        if to_idx > from_idx:
                            to_idx -= 1
                        timeline.clips.insert(to_idx, clip)

                        # Recalculate all times
                        current_time = 0
                        for clip in timeline.clips:
                            clip.start_time = current_time
                            current_time += clip.duration

                        return f"Moved clip {from_idx+1} to position {to_idx+1}"

            elif suggestion.suggestion_type == SuggestionType.REMOVE_CLIP:
                clip_idx = suggestion.target_clips[0]
                if 0 <= clip_idx < len(timeline.clips):
                    removed_duration = timeline.clips[clip_idx].duration
                    timeline.clips.pop(clip_idx)

                    # Adjust subsequent times
                    for i in range(clip_idx, len(timeline.clips)):
                        timeline.clips[i].start_time -= removed_duration

                    timeline.duration -= removed_duration
                    return f"Removed clip {clip_idx+1}"

            elif suggestion.suggestion_type == SuggestionType.SPLIT_CLIP:
                clip_idx = suggestion.target_clips[0]
                if 0 <= clip_idx < len(timeline.clips):
                    original_clip = timeline.clips[clip_idx]
                    split_point = original_clip.duration / 2

                    # Create two new clips
                    clip1 = TimelineClip(
                        asset_path=original_clip.asset_path,
                        start_time=original_clip.start_time,
                        duration=split_point,
                        transition_in=original_clip.transition_in,
                        transition_in_duration=original_clip.transition_in_duration,
                    )

                    clip2 = TimelineClip(
                        asset_path=original_clip.asset_path,
                        start_time=original_clip.start_time + split_point,
                        duration=original_clip.duration - split_point,
                        transition_out=original_clip.transition_out,
                        transition_out_duration=original_clip.transition_out_duration,
                    )

                    # Replace original with split clips
                    timeline.clips[clip_idx] = clip1
                    timeline.clips.insert(clip_idx + 1, clip2)

                    return f"Split clip {clip_idx+1} into two parts"

            elif suggestion.suggestion_type == SuggestionType.MERGE_CLIPS:
                if len(suggestion.target_clips) >= 2:
                    idx1, idx2 = suggestion.target_clips[:2]
                    if (0 <= idx1 < len(timeline.clips) and
                        0 <= idx2 < len(timeline.clips) and
                        abs(idx1 - idx2) == 1):

                        first_idx = min(idx1, idx2)
                        clip1 = timeline.clips[first_idx]
                        clip2 = timeline.clips[first_idx + 1]

                        # Create merged clip
                        merged_clip = TimelineClip(
                            asset_path=clip1.asset_path,  # Use first clip's asset
                            start_time=clip1.start_time,
                            duration=clip1.duration + clip2.duration,
                            transition_in=clip1.transition_in,
                            transition_in_duration=clip1.transition_in_duration,
                            transition_out=clip2.transition_out,
                            transition_out_duration=clip2.transition_out_duration,
                        )

                        # Replace with merged clip
                        timeline.clips[first_idx] = merged_clip
                        timeline.clips.pop(first_idx + 1)

                        return f"Merged clips {first_idx+1} and {first_idx+2}"

        except Exception as e:
            logger.warning(f"Failed to apply suggestion: {e}")

        return None

    def _adjust_duration(
        self,
        timeline: Timeline,
        target_duration: float,
        preserve_clips: list[int] | None = None,
    ) -> list[str]:
        """Adjust timeline to match target duration."""
        changes = []
        preserve_clips = preserve_clips or []

        current_duration = timeline.duration
        if abs(current_duration - target_duration) < 0.1:
            return changes  # Close enough

        # Calculate scale factor
        scale_factor = target_duration / current_duration

        # Get clips that can be adjusted
        adjustable_clips = [
            (i, clip) for i, clip in enumerate(timeline.clips)
            if i not in preserve_clips
        ]

        if not adjustable_clips:
            changes.append("Cannot adjust duration - all clips are preserved")
            return changes

        # Distribute duration change across adjustable clips
        total_adjustable_duration = sum(clip.duration for _, clip in adjustable_clips)
        total_adjustable_duration * scale_factor

        # Apply proportional scaling
        current_time = 0
        for i, clip in enumerate(timeline.clips):
            if i in preserve_clips:
                clip.start_time = current_time
                current_time += clip.duration
            else:
                old_duration = clip.duration
                new_duration = clip.duration * scale_factor

                # Apply reasonable limits
                new_duration = max(0.5, min(30.0, new_duration))

                clip.start_time = current_time
                clip.duration = new_duration
                current_time += new_duration

                if abs(new_duration - old_duration) > 0.1:
                    changes.append(
                        f"Adjusted clip {i+1} duration from {old_duration:.1f}s to {new_duration:.1f}s"
                    )

        timeline.duration = current_time
        changes.insert(0, f"Adjusted total duration from {current_duration:.1f}s to {timeline.duration:.1f}s")

        return changes

    def _validate_timeline(self, timeline: Timeline) -> list[str]:
        """Validate timeline consistency."""
        warnings = []

        # Check clip times
        expected_time = 0
        for i, clip in enumerate(timeline.clips):
            if abs(clip.start_time - expected_time) > 0.01:
                warnings.append(
                    f"Clip {i+1} start time mismatch: expected {expected_time:.2f}, got {clip.start_time:.2f}"
                )
            expected_time = clip.start_time + clip.duration

        # Check total duration
        if abs(timeline.duration - expected_time) > 0.01:
            warnings.append(
                f"Timeline duration mismatch: stated {timeline.duration:.2f}, calculated {expected_time:.2f}"
            )

        # Check for very short clips
        for i, clip in enumerate(timeline.clips):
            if clip.duration < 0.5:
                warnings.append(f"Clip {i+1} is very short ({clip.duration:.2f}s)")

        # Check for missing transitions
        for i in range(len(timeline.clips) - 1):
            if (not timeline.clips[i].transition_out and
                not timeline.clips[i+1].transition_in):
                warnings.append(f"No transition between clips {i+1} and {i+2}")

        return warnings

    async def _calculate_improvement(
        self,
        original: Timeline,
        optimized: Timeline,
    ) -> float:
        """Calculate improvement score between timelines."""
        # Re-analyze both timelines
        orig_issues, _ = await self.flow_analyzer.analyze_timeline_flow(original)
        opt_issues, _ = await self.flow_analyzer.analyze_timeline_flow(optimized)

        # Calculate severity reduction
        orig_severity = sum(issue.severity for issue in orig_issues) if orig_issues else 0
        opt_severity = sum(issue.severity for issue in opt_issues) if opt_issues else 0

        if orig_severity > 0:
            improvement = (orig_severity - opt_severity) / orig_severity
        else:
            improvement = 0.0

        # Ensure non-negative
        return max(0.0, min(1.0, improvement))

    def generate_optimization_report(
        self,
        result: OptimizationResult,
        original_timeline: Timeline,
    ) -> dict[str, Any]:
        """Generate detailed optimization report."""
        report = {
            "summary": {
                "original_duration": original_timeline.duration,
                "optimized_duration": result.optimized_timeline.duration,
                "clip_count_change": len(result.optimized_timeline.clips) - len(original_timeline.clips),
                "improvement_score": result.improvement_score,
                "changes_made": len(result.changes_made),
            },
            "changes": result.changes_made,
            "preserved": result.preserved_elements,
            "warnings": result.warnings,
            "timeline_comparison": {
                "original": {
                    "clips": len(original_timeline.clips),
                    "duration": original_timeline.duration,
                    "transitions": sum(
                        1 for clip in original_timeline.clips
                        if clip.transition_in or clip.transition_out
                    ),
                },
                "optimized": {
                    "clips": len(result.optimized_timeline.clips),
                    "duration": result.optimized_timeline.duration,
                    "transitions": sum(
                        1 for clip in result.optimized_timeline.clips
                        if clip.transition_in or clip.transition_out
                    ),
                },
            },
        }

        return report
