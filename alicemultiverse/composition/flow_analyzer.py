"""Timeline flow analyzer for detecting pacing and rhythm issues."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from ..core.unified_cache import UnifiedCache
from ..understanding.providers import get_vision_provider
from ..workflows.models import Timeline, TimelineClip

logger = logging.getLogger(__name__)


class FlowIssueType(Enum):
    """Types of flow issues in timelines."""
    PACING_TOO_FAST = "pacing_too_fast"
    PACING_TOO_SLOW = "pacing_too_slow"
    INCONSISTENT_RHYTHM = "inconsistent_rhythm"
    JARRING_TRANSITION = "jarring_transition"
    COLOR_DISCONTINUITY = "color_discontinuity"
    STYLE_MISMATCH = "style_mismatch"
    MOTION_CONFLICT = "motion_conflict"
    NARRATIVE_BREAK = "narrative_break"
    ENERGY_DROP = "energy_drop"
    ENERGY_SPIKE = "energy_spike"
    REPETITIVE_SEQUENCE = "repetitive_sequence"
    MISSING_CLIMAX = "missing_climax"


class SuggestionType(Enum):
    """Types of suggestions for improvement."""
    REORDER_CLIPS = "reorder_clips"
    ADJUST_DURATION = "adjust_duration"
    ADD_TRANSITION = "add_transition"
    CHANGE_TRANSITION = "change_transition"
    INSERT_CLIP = "insert_clip"
    REMOVE_CLIP = "remove_clip"
    SPLIT_CLIP = "split_clip"
    MERGE_CLIPS = "merge_clips"
    ADD_EFFECT = "add_effect"
    ADJUST_TIMING = "adjust_timing"


@dataclass
class FlowIssue:
    """A detected issue in timeline flow."""
    issue_type: FlowIssueType
    severity: float  # 0-1, higher is more severe
    start_time: float
    end_time: float
    affected_clips: list[int]  # Clip indices
    description: str
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class FlowSuggestion:
    """A suggestion for improving timeline flow."""
    suggestion_type: SuggestionType
    priority: float  # 0-1, higher is more important
    target_clips: list[int]
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    expected_improvement: float = 0.0


@dataclass
class ClipAnalysis:
    """Analysis data for a single clip."""
    clip_index: int
    dominant_colors: list[tuple[int, int, int]]
    brightness: float
    contrast: float
    motion_level: float  # 0-1
    complexity: float  # 0-1
    mood_score: float  # -1 to 1 (negative to positive)
    energy_level: float  # 0-1
    style_vector: np.ndarray  # Style embedding
    semantic_tags: list[str]


class FlowAnalyzer:
    """Analyze timeline flow and suggest improvements."""

    # Ideal pacing parameters
    IDEAL_CLIP_DURATION = {
        "fast": (0.5, 2.0),
        "medium": (2.0, 5.0),
        "slow": (5.0, 10.0),
    }

    # Energy curve templates
    ENERGY_CURVES = {
        "rising_action": lambda t: t ** 1.5,  # Gradual build
        "falling_action": lambda t: 1 - (t ** 2),  # Quick drop
        "wave": lambda t: 0.5 + 0.5 * np.sin(2 * np.pi * t),  # Oscillating
        "steady": lambda t: 0.5,  # Constant
        "climactic": lambda t: t ** 3 if t < 0.8 else 1.0,  # Build to climax
    }

    def __init__(
        self,
        metadata_cache: UnifiedCache | None = None,
        vision_provider: str | None = None,
    ):
        """Initialize the flow analyzer.
        
        Args:
            metadata_cache: Cache for clip metadata
            vision_provider: Vision provider for analysis
        """
        self.metadata_cache = metadata_cache or UnifiedCache(Path.cwd())
        self.vision_provider = vision_provider

        # Analysis cache
        self.clip_analyses: dict[str, ClipAnalysis] = {}

    async def analyze_timeline_flow(
        self,
        timeline: Timeline,
        target_mood: str | None = None,
        target_energy: str | None = None,
    ) -> tuple[list[FlowIssue], list[FlowSuggestion]]:
        """Analyze timeline flow and generate suggestions.
        
        Args:
            timeline: Timeline to analyze
            target_mood: Target mood (e.g., "upbeat", "dramatic")
            target_energy: Target energy curve
            
        Returns:
            Tuple of (issues, suggestions)
        """
        # Analyze all clips
        clip_analyses = await self._analyze_all_clips(timeline)

        # Detect flow issues
        issues = []

        # Check pacing
        pacing_issues = self._analyze_pacing(timeline, clip_analyses)
        issues.extend(pacing_issues)

        # Check visual continuity
        continuity_issues = self._analyze_continuity(timeline, clip_analyses)
        issues.extend(continuity_issues)

        # Check energy flow
        energy_issues = self._analyze_energy_flow(
            timeline, clip_analyses, target_energy
        )
        issues.extend(energy_issues)

        # Check narrative structure
        narrative_issues = self._analyze_narrative(timeline, clip_analyses)
        issues.extend(narrative_issues)

        # Generate suggestions based on issues
        suggestions = self._generate_suggestions(timeline, issues, clip_analyses)

        # Sort by severity/priority
        issues.sort(key=lambda i: i.severity, reverse=True)
        suggestions.sort(key=lambda s: s.priority, reverse=True)

        return issues, suggestions

    async def _analyze_all_clips(
        self,
        timeline: Timeline,
    ) -> list[ClipAnalysis]:
        """Analyze all clips in the timeline."""
        analyses = []

        for i, clip in enumerate(timeline.clips):
            # Check cache first
            cache_key = str(clip.asset_path)
            if cache_key in self.clip_analyses:
                analyses.append(self.clip_analyses[cache_key])
                continue

            # Analyze clip
            analysis = await self._analyze_clip(clip, i)
            self.clip_analyses[cache_key] = analysis
            analyses.append(analysis)

        return analyses

    async def _analyze_clip(
        self,
        clip: TimelineClip,
        clip_index: int,
    ) -> ClipAnalysis:
        """Analyze a single clip."""
        # Get basic metadata
        metadata = self.metadata_cache.get_metadata(str(clip.asset_path))

        # Default values
        dominant_colors = [(128, 128, 128)]  # Gray
        brightness = 0.5
        contrast = 0.5
        motion_level = 0.3
        complexity = 0.5
        mood_score = 0.0
        energy_level = 0.5
        style_vector = np.zeros(128)  # Placeholder embedding
        semantic_tags = []

        if metadata:
            # Extract from metadata
            if "dominant_colors" in metadata:
                dominant_colors = metadata["dominant_colors"]

            if "brightness" in metadata:
                brightness = metadata["brightness"]

            if "semantic_tags" in metadata:
                semantic_tags = metadata["semantic_tags"]

                # Infer mood from tags
                positive_tags = ["happy", "bright", "cheerful", "vibrant"]
                negative_tags = ["dark", "moody", "somber", "melancholic"]

                mood_score = sum(1 for tag in semantic_tags if tag in positive_tags)
                mood_score -= sum(1 for tag in semantic_tags if tag in negative_tags)
                mood_score = max(-1, min(1, mood_score / 3))  # Normalize

                # Infer energy from tags
                high_energy_tags = ["action", "dynamic", "fast", "explosive"]
                low_energy_tags = ["calm", "peaceful", "still", "quiet"]

                energy_level = 0.5
                energy_level += sum(0.2 for tag in semantic_tags if tag in high_energy_tags)
                energy_level -= sum(0.2 for tag in semantic_tags if tag in low_energy_tags)
                energy_level = max(0, min(1, energy_level))

        # Use vision provider for deeper analysis if available
        if self.vision_provider and clip.asset_path.suffix.lower() in [".jpg", ".png", ".webp"]:
            try:
                provider = get_vision_provider(self.vision_provider)

                # Analyze for motion and complexity
                analysis_prompt = """Analyze this image and provide scores (0-1):
1. Motion level: How much movement/action is implied
2. Visual complexity: How complex/busy vs simple
3. Overall energy: Dynamic vs calm

Format: motion=X.X, complexity=X.X, energy=X.X"""

                result = await provider.analyze_image(
                    str(clip.asset_path),
                    analysis_prompt
                )

                # Parse results
                if "motion=" in result:
                    motion_level = float(result.split("motion=")[1].split(",")[0])
                if "complexity=" in result:
                    complexity = float(result.split("complexity=")[1].split(",")[0])
                if "energy=" in result:
                    energy_level = float(result.split("energy=")[1].split(",")[0])

            except Exception as e:
                logger.warning(f"Vision analysis failed for {clip.asset_path}: {e}")

        return ClipAnalysis(
            clip_index=clip_index,
            dominant_colors=dominant_colors,
            brightness=brightness,
            contrast=contrast,
            motion_level=motion_level,
            complexity=complexity,
            mood_score=mood_score,
            energy_level=energy_level,
            style_vector=style_vector,
            semantic_tags=semantic_tags,
        )

    def _analyze_pacing(
        self,
        timeline: Timeline,
        analyses: list[ClipAnalysis],
    ) -> list[FlowIssue]:
        """Analyze timeline pacing."""
        issues = []

        # Calculate average energy to determine expected pacing
        avg_energy = np.mean([a.energy_level for a in analyses])

        if avg_energy > 0.7:
            expected_pacing = "fast"
        elif avg_energy > 0.4:
            expected_pacing = "medium"
        else:
            expected_pacing = "slow"

        min_duration, max_duration = self.IDEAL_CLIP_DURATION[expected_pacing]

        # Check each clip duration
        for i, clip in enumerate(timeline.clips):
            if clip.duration < min_duration:
                issues.append(FlowIssue(
                    issue_type=FlowIssueType.PACING_TOO_FAST,
                    severity=0.6,
                    start_time=clip.start_time,
                    end_time=clip.start_time + clip.duration,
                    affected_clips=[i],
                    description=f"Clip {i+1} is too short ({clip.duration:.1f}s) for {expected_pacing} pacing",
                    metrics={"duration": clip.duration, "min_duration": min_duration},
                ))

            elif clip.duration > max_duration:
                issues.append(FlowIssue(
                    issue_type=FlowIssueType.PACING_TOO_SLOW,
                    severity=0.5,
                    start_time=clip.start_time,
                    end_time=clip.start_time + clip.duration,
                    affected_clips=[i],
                    description=f"Clip {i+1} is too long ({clip.duration:.1f}s) for {expected_pacing} pacing",
                    metrics={"duration": clip.duration, "max_duration": max_duration},
                ))

        # Check rhythm consistency
        durations = [c.duration for c in timeline.clips]
        if len(durations) > 2:
            duration_variance = np.var(durations)
            if duration_variance > 4.0:  # High variance threshold
                issues.append(FlowIssue(
                    issue_type=FlowIssueType.INCONSISTENT_RHYTHM,
                    severity=0.7,
                    start_time=0,
                    end_time=timeline.duration,
                    affected_clips=list(range(len(timeline.clips))),
                    description="Clip durations vary too much, creating inconsistent rhythm",
                    metrics={"variance": duration_variance},
                ))

        return issues

    def _analyze_continuity(
        self,
        timeline: Timeline,
        analyses: list[ClipAnalysis],
    ) -> list[FlowIssue]:
        """Analyze visual continuity between clips."""
        issues = []

        for i in range(len(analyses) - 1):
            curr = analyses[i]
            next = analyses[i + 1]

            # Check color continuity
            if curr.dominant_colors and next.dominant_colors:
                # Calculate color distance
                color_dist = self._color_distance(
                    curr.dominant_colors[0],
                    next.dominant_colors[0]
                )

                if color_dist > 150:  # Significant color jump
                    issues.append(FlowIssue(
                        issue_type=FlowIssueType.COLOR_DISCONTINUITY,
                        severity=0.5,
                        start_time=timeline.clips[i].start_time + timeline.clips[i].duration,
                        end_time=timeline.clips[i+1].start_time,
                        affected_clips=[i, i+1],
                        description=f"Large color shift between clips {i+1} and {i+2}",
                        metrics={"color_distance": color_dist},
                    ))

            # Check brightness continuity
            brightness_diff = abs(curr.brightness - next.brightness)
            if brightness_diff > 0.5:
                issues.append(FlowIssue(
                    issue_type=FlowIssueType.JARRING_TRANSITION,
                    severity=0.6,
                    start_time=timeline.clips[i].start_time + timeline.clips[i].duration,
                    end_time=timeline.clips[i+1].start_time,
                    affected_clips=[i, i+1],
                    description=f"Large brightness change between clips {i+1} and {i+2}",
                    metrics={"brightness_diff": brightness_diff},
                ))

            # Check motion continuity
            motion_diff = abs(curr.motion_level - next.motion_level)
            if motion_diff > 0.6:
                issues.append(FlowIssue(
                    issue_type=FlowIssueType.MOTION_CONFLICT,
                    severity=0.5,
                    start_time=timeline.clips[i].start_time + timeline.clips[i].duration,
                    end_time=timeline.clips[i+1].start_time,
                    affected_clips=[i, i+1],
                    description=f"Motion level conflict between clips {i+1} and {i+2}",
                    metrics={"motion_diff": motion_diff},
                ))

        return issues

    def _analyze_energy_flow(
        self,
        timeline: Timeline,
        analyses: list[ClipAnalysis],
        target_energy: str | None = None,
    ) -> list[FlowIssue]:
        """Analyze energy flow throughout timeline."""
        issues = []

        # Extract energy levels
        energy_levels = [a.energy_level for a in analyses]

        # Check for energy drops
        for i in range(1, len(energy_levels)):
            if energy_levels[i] < energy_levels[i-1] - 0.4:
                issues.append(FlowIssue(
                    issue_type=FlowIssueType.ENERGY_DROP,
                    severity=0.6,
                    start_time=timeline.clips[i].start_time,
                    end_time=timeline.clips[i].start_time + timeline.clips[i].duration,
                    affected_clips=[i-1, i],
                    description=f"Significant energy drop at clip {i+1}",
                    metrics={
                        "prev_energy": energy_levels[i-1],
                        "curr_energy": energy_levels[i],
                    },
                ))

        # Check against target energy curve
        if target_energy and target_energy in self.ENERGY_CURVES:
            curve_func = self.ENERGY_CURVES[target_energy]

            # Sample expected energy at each clip
            for i, (clip, analysis) in enumerate(zip(timeline.clips, analyses, strict=False)):
                # Normalize time position
                t = (clip.start_time + clip.duration / 2) / timeline.duration
                expected_energy = curve_func(t)

                energy_diff = abs(analysis.energy_level - expected_energy)
                if energy_diff > 0.3:
                    issues.append(FlowIssue(
                        issue_type=FlowIssueType.INCONSISTENT_RHYTHM,
                        severity=0.5 * energy_diff,
                        start_time=clip.start_time,
                        end_time=clip.start_time + clip.duration,
                        affected_clips=[i],
                        description=f"Clip {i+1} energy doesn't match {target_energy} curve",
                        metrics={
                            "actual_energy": analysis.energy_level,
                            "expected_energy": expected_energy,
                        },
                    ))

        # Check for missing climax in longer timelines
        if timeline.duration > 30 and max(energy_levels) < 0.7:
            issues.append(FlowIssue(
                issue_type=FlowIssueType.MISSING_CLIMAX,
                severity=0.7,
                start_time=0,
                end_time=timeline.duration,
                affected_clips=list(range(len(timeline.clips))),
                description="Timeline lacks a high-energy climax moment",
                metrics={"max_energy": max(energy_levels)},
            ))

        return issues

    def _analyze_narrative(
        self,
        timeline: Timeline,
        analyses: list[ClipAnalysis],
    ) -> list[FlowIssue]:
        """Analyze narrative flow and coherence."""
        issues = []

        # Check for repetitive sequences
        for i in range(len(analyses) - 2):
            # Compare semantic similarity
            if analyses[i].semantic_tags and analyses[i+2].semantic_tags:
                overlap = set(analyses[i].semantic_tags) & set(analyses[i+2].semantic_tags)
                if len(overlap) > len(analyses[i].semantic_tags) * 0.8:
                    issues.append(FlowIssue(
                        issue_type=FlowIssueType.REPETITIVE_SEQUENCE,
                        severity=0.4,
                        start_time=timeline.clips[i].start_time,
                        end_time=timeline.clips[i+2].start_time + timeline.clips[i+2].duration,
                        affected_clips=[i, i+2],
                        description=f"Clips {i+1} and {i+3} are too similar",
                        metrics={"tag_overlap": len(overlap)},
                    ))

        # Check for style consistency
        if len(analyses) > 3:
            # Simple style check based on tags
            style_tags = ["realistic", "abstract", "cartoon", "artistic", "photographic"]
            clip_styles = []

            for analysis in analyses:
                found_styles = [tag for tag in analysis.semantic_tags if tag in style_tags]
                clip_styles.append(found_styles[0] if found_styles else "unknown")

            # Find style changes
            for i in range(1, len(clip_styles)):
                if clip_styles[i] != "unknown" and clip_styles[i-1] != "unknown":
                    if clip_styles[i] != clip_styles[i-1]:
                        issues.append(FlowIssue(
                            issue_type=FlowIssueType.STYLE_MISMATCH,
                            severity=0.5,
                            start_time=timeline.clips[i].start_time,
                            end_time=timeline.clips[i].start_time + timeline.clips[i].duration,
                            affected_clips=[i-1, i],
                            description=f"Style change from {clip_styles[i-1]} to {clip_styles[i]}",
                            metrics={},
                        ))

        return issues

    def _generate_suggestions(
        self,
        timeline: Timeline,
        issues: list[FlowIssue],
        analyses: list[ClipAnalysis],
    ) -> list[FlowSuggestion]:
        """Generate suggestions based on detected issues."""
        suggestions = []

        # Group issues by type
        issue_groups = {}
        for issue in issues:
            if issue.issue_type not in issue_groups:
                issue_groups[issue.issue_type] = []
            issue_groups[issue.issue_type].append(issue)

        # Generate suggestions for pacing issues
        if FlowIssueType.PACING_TOO_FAST in issue_groups:
            for issue in issue_groups[FlowIssueType.PACING_TOO_FAST]:
                suggestions.append(FlowSuggestion(
                    suggestion_type=SuggestionType.ADJUST_DURATION,
                    priority=issue.severity,
                    target_clips=issue.affected_clips,
                    description=f"Extend clip {issue.affected_clips[0]+1} to at least {issue.metrics['min_duration']:.1f}s",
                    parameters={
                        "new_duration": issue.metrics["min_duration"],
                        "method": "slow_motion",
                    },
                    expected_improvement=0.3,
                ))

        if FlowIssueType.PACING_TOO_SLOW in issue_groups:
            for issue in issue_groups[FlowIssueType.PACING_TOO_SLOW]:
                suggestions.append(FlowSuggestion(
                    suggestion_type=SuggestionType.ADJUST_DURATION,
                    priority=issue.severity,
                    target_clips=issue.affected_clips,
                    description=f"Shorten clip {issue.affected_clips[0]+1} to {issue.metrics['max_duration']:.1f}s",
                    parameters={
                        "new_duration": issue.metrics["max_duration"],
                        "method": "trim",
                    },
                    expected_improvement=0.2,
                ))

        # Generate suggestions for continuity issues
        if FlowIssueType.COLOR_DISCONTINUITY in issue_groups:
            for issue in issue_groups[FlowIssueType.COLOR_DISCONTINUITY]:
                suggestions.append(FlowSuggestion(
                    suggestion_type=SuggestionType.ADD_TRANSITION,
                    priority=issue.severity * 0.8,
                    target_clips=issue.affected_clips,
                    description=f"Add color fade transition between clips {issue.affected_clips[0]+1} and {issue.affected_clips[1]+1}",
                    parameters={
                        "transition_type": "cross_fade",
                        "duration": 1.0,
                    },
                    expected_improvement=0.4,
                ))

        if FlowIssueType.JARRING_TRANSITION in issue_groups:
            for issue in issue_groups[FlowIssueType.JARRING_TRANSITION]:
                suggestions.append(FlowSuggestion(
                    suggestion_type=SuggestionType.ADD_EFFECT,
                    priority=issue.severity,
                    target_clips=[issue.affected_clips[0]],
                    description=f"Add fade-out to clip {issue.affected_clips[0]+1}",
                    parameters={
                        "effect": "brightness_fade",
                        "duration": 0.5,
                    },
                    expected_improvement=0.3,
                ))

        # Generate suggestions for energy flow
        if FlowIssueType.ENERGY_DROP in issue_groups:
            for issue in issue_groups[FlowIssueType.ENERGY_DROP]:
                # Suggest reordering if possible
                if issue.affected_clips[1] < len(timeline.clips) - 1:
                    suggestions.append(FlowSuggestion(
                        suggestion_type=SuggestionType.REORDER_CLIPS,
                        priority=issue.severity * 0.9,
                        target_clips=issue.affected_clips,
                        description=f"Move high-energy clip after clip {issue.affected_clips[1]+1}",
                        parameters={
                            "move_to": issue.affected_clips[1] + 1,
                        },
                        expected_improvement=0.5,
                    ))

        if FlowIssueType.MISSING_CLIMAX in issue_groups:
            # Find potential climax position (around 70-80% through)
            climax_time = timeline.duration * 0.75
            climax_clip = 0
            for i, clip in enumerate(timeline.clips):
                if clip.start_time <= climax_time <= clip.start_time + clip.duration:
                    climax_clip = i
                    break

            suggestions.append(FlowSuggestion(
                suggestion_type=SuggestionType.INSERT_CLIP,
                priority=0.8,
                target_clips=[climax_clip],
                description=f"Insert high-energy clip at position {climax_clip+1} for climax",
                parameters={
                    "clip_type": "high_energy",
                    "duration": 3.0,
                },
                expected_improvement=0.6,
            ))

        # Generate suggestions for narrative issues
        if FlowIssueType.REPETITIVE_SEQUENCE in issue_groups:
            for issue in issue_groups[FlowIssueType.REPETITIVE_SEQUENCE]:
                suggestions.append(FlowSuggestion(
                    suggestion_type=SuggestionType.REMOVE_CLIP,
                    priority=issue.severity * 0.7,
                    target_clips=[issue.affected_clips[1]],
                    description=f"Remove repetitive clip {issue.affected_clips[1]+1}",
                    parameters={},
                    expected_improvement=0.3,
                ))

        return suggestions

    def _color_distance(
        self,
        color1: tuple[int, int, int],
        color2: tuple[int, int, int],
    ) -> float:
        """Calculate Euclidean distance between colors."""
        return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2, strict=False)))

    def generate_flow_report(
        self,
        issues: list[FlowIssue],
        suggestions: list[FlowSuggestion],
    ) -> dict[str, Any]:
        """Generate a comprehensive flow analysis report."""
        report = {
            "summary": {
                "total_issues": len(issues),
                "critical_issues": sum(1 for i in issues if i.severity > 0.7),
                "total_suggestions": len(suggestions),
                "high_priority_suggestions": sum(1 for s in suggestions if s.priority > 0.7),
            },
            "issues_by_type": {},
            "suggestions_by_type": {},
            "timeline_health_score": 0.0,
        }

        # Group issues by type
        for issue in issues:
            issue_type = issue.issue_type.value
            if issue_type not in report["issues_by_type"]:
                report["issues_by_type"][issue_type] = {
                    "count": 0,
                    "avg_severity": 0.0,
                    "instances": [],
                }

            report["issues_by_type"][issue_type]["count"] += 1
            report["issues_by_type"][issue_type]["instances"].append({
                "clips": issue.affected_clips,
                "severity": issue.severity,
                "description": issue.description,
            })

        # Calculate average severities
        for issue_type, data in report["issues_by_type"].items():
            if data["count"] > 0:
                avg_severity = sum(
                    inst["severity"] for inst in data["instances"]
                ) / data["count"]
                data["avg_severity"] = avg_severity

        # Group suggestions by type
        for suggestion in suggestions:
            sug_type = suggestion.suggestion_type.value
            if sug_type not in report["suggestions_by_type"]:
                report["suggestions_by_type"][sug_type] = {
                    "count": 0,
                    "avg_priority": 0.0,
                    "total_improvement": 0.0,
                }

            report["suggestions_by_type"][sug_type]["count"] += 1
            report["suggestions_by_type"][sug_type]["total_improvement"] += suggestion.expected_improvement

        # Calculate timeline health score (0-100)
        if issues:
            total_severity = sum(i.severity for i in issues)
            avg_severity = total_severity / len(issues)
            report["timeline_health_score"] = max(0, (1 - avg_severity) * 100)
        else:
            report["timeline_health_score"] = 100.0

        return report
