"""Export-specific analytics and metrics."""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    EDL = "edl"
    XML = "xml"
    JSON = "json"
    CAPCUT = "capcut"


@dataclass
class ExportMetrics:
    """Metrics for a single export operation."""
    export_id: str
    timeline_id: str
    format: ExportFormat
    platform: str | None = None

    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration_seconds: float | None = None

    # Content metrics
    clip_count: int = 0
    total_duration: float = 0.0
    transition_count: int = 0
    effect_count: int = 0
    marker_count: int = 0

    # Quality metrics
    resolution: tuple[int, int] | None = None
    frame_rate: float = 30.0
    file_size_bytes: int | None = None

    # Platform-specific
    platform_optimizations: list[str] = field(default_factory=list)
    compatibility_score: float = 1.0  # 0-1, how well it fits platform

    # User interaction
    preview_count: int = 0
    edit_count: int = 0
    time_to_approval: float | None = None  # seconds

    # Performance
    export_speed_mbps: float | None = None
    memory_peak_mb: float | None = None

    # Success metrics
    successful: bool = False
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)

    # Usage tracking
    imported_to_editor: bool = False
    shared: bool = False
    published: bool = False

    # Feedback
    user_rating: int | None = None  # 1-5
    user_notes: str | None = None


class ExportAnalytics:
    """Analyze export patterns and performance."""

    def __init__(self, data_dir: Path | None = None):
        """Initialize export analytics.
        
        Args:
            data_dir: Directory for storing analytics data
        """
        self.data_dir = data_dir or (Path.home() / ".alice" / "analytics")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.exports_file = self.data_dir / "export_metrics.json"
        self.patterns_file = self.data_dir / "export_patterns.json"

        # Load historical data
        self.export_history = self._load_export_history()
        self.usage_patterns = self._load_usage_patterns()

    def track_export(self, metrics: ExportMetrics) -> None:
        """Track an export operation.
        
        Args:
            metrics: Export metrics to track
        """
        # Calculate duration if needed
        if metrics.end_time and not metrics.duration_seconds:
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()

        # Calculate export speed if possible
        if metrics.file_size_bytes and metrics.duration_seconds:
            mbps = (metrics.file_size_bytes / 1_000_000) / metrics.duration_seconds
            metrics.export_speed_mbps = mbps

        # Convert to dict and save
        metrics_dict = self._metrics_to_dict(metrics)
        self.export_history.append(metrics_dict)

        # Update patterns
        self._update_patterns(metrics)

        # Save to disk
        self._save_export_history()
        self._save_patterns()

        logger.info(f"Tracked export: {metrics.export_id} ({metrics.format.value})")

    def get_format_statistics(
        self,
        format: ExportFormat | None = None,
        time_range: timedelta | None = None
    ) -> dict[str, Any]:
        """Get statistics for export formats.
        
        Args:
            format: Specific format to analyze
            time_range: Time range to consider
            
        Returns:
            Format statistics
        """
        # Filter exports
        exports = self._filter_exports(format=format, time_range=time_range)

        if not exports:
            return {
                "total_exports": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "average_clip_count": 0.0,
                "common_platforms": {},
                "common_resolutions": {}
            }

        # Calculate statistics
        total = len(exports)
        successful = sum(1 for e in exports if e.get("successful", False))

        durations = [e["duration_seconds"] for e in exports if e.get("duration_seconds")]
        avg_duration = sum(durations) / len(durations) if durations else 0

        clip_counts = [e["clip_count"] for e in exports if e.get("clip_count")]
        avg_clips = sum(clip_counts) / len(clip_counts) if clip_counts else 0

        # Platform distribution
        platform_counts = defaultdict(int)
        for e in exports:
            if e.get("platform"):
                platform_counts[e["platform"]] += 1

        # Resolution distribution
        resolution_counts = defaultdict(int)
        for e in exports:
            if e.get("resolution"):
                res_str = f"{e['resolution'][0]}x{e['resolution'][1]}"
                resolution_counts[res_str] += 1

        return {
            "total_exports": total,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_duration": avg_duration,
            "average_clip_count": avg_clips,
            "common_platforms": dict(sorted(
                platform_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "common_resolutions": dict(sorted(
                resolution_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3])
        }

    def get_platform_performance(
        self,
        platform: str,
        time_range: timedelta | None = None
    ) -> dict[str, Any]:
        """Analyze performance for a specific platform.
        
        Args:
            platform: Platform to analyze
            time_range: Time range to consider
            
        Returns:
            Platform performance metrics
        """
        # Filter exports for platform
        exports = self._filter_exports(platform=platform, time_range=time_range)

        if not exports:
            return {
                "platform": platform,
                "total_exports": 0,
                "compatibility_score": 0.0,
                "common_optimizations": [],
                "average_edit_count": 0.0,
                "adoption_rate": 0.0
            }

        # Calculate metrics
        total = len(exports)

        compatibility_scores = [
            e["compatibility_score"] for e in exports
            if e.get("compatibility_score") is not None
        ]
        avg_compatibility = sum(compatibility_scores) / len(compatibility_scores) if compatibility_scores else 0

        # Optimization usage
        optimization_counts = defaultdict(int)
        for e in exports:
            for opt in e.get("platform_optimizations", []):
                optimization_counts[opt] += 1

        # Edit patterns
        edit_counts = [e["edit_count"] for e in exports if e.get("edit_count") is not None]
        avg_edits = sum(edit_counts) / len(edit_counts) if edit_counts else 0

        # Adoption (published exports)
        published = sum(1 for e in exports if e.get("published", False))
        adoption_rate = (published / total * 100) if total > 0 else 0

        return {
            "platform": platform,
            "total_exports": total,
            "compatibility_score": avg_compatibility,
            "common_optimizations": sorted(
                optimization_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "average_edit_count": avg_edits,
            "adoption_rate": adoption_rate
        }

    def get_workflow_insights(
        self,
        timeline_id: str | None = None
    ) -> dict[str, Any]:
        """Get insights about export workflows.
        
        Args:
            timeline_id: Specific timeline to analyze
            
        Returns:
            Workflow insights
        """
        # Filter exports
        if timeline_id:
            exports = [e for e in self.export_history if e.get("timeline_id") == timeline_id]
        else:
            exports = self.export_history

        if not exports:
            return {
                "total_timelines": 0,
                "exports_per_timeline": 0.0,
                "format_preferences": {},
                "time_to_final": 0.0,
                "iteration_patterns": []
            }

        # Group by timeline
        timeline_exports = defaultdict(list)
        for e in exports:
            if e.get("timeline_id"):
                timeline_exports[e["timeline_id"]].append(e)

        # Calculate metrics
        total_timelines = len(timeline_exports)
        total_exports = len(exports)
        exports_per_timeline = total_exports / total_timelines if total_timelines > 0 else 0

        # Format preferences
        format_counts = defaultdict(int)
        for e in exports:
            if e.get("format"):
                format_counts[e["format"]] += 1

        # Time to final export (first to last export per timeline)
        time_to_final_values = []
        for timeline_exports_list in timeline_exports.values():
            if len(timeline_exports_list) > 1:
                sorted_exports = sorted(
                    timeline_exports_list,
                    key=lambda x: datetime.fromisoformat(x["start_time"])
                )
                first_time = datetime.fromisoformat(sorted_exports[0]["start_time"])
                last_time = datetime.fromisoformat(sorted_exports[-1]["start_time"])
                time_to_final_values.append((last_time - first_time).total_seconds())

        avg_time_to_final = sum(time_to_final_values) / len(time_to_final_values) if time_to_final_values else 0

        # Iteration patterns (how many exports before final)
        iteration_counts = defaultdict(int)
        for timeline_exports_list in timeline_exports.values():
            count = len(timeline_exports_list)
            if count <= 5:
                iteration_counts[f"{count} exports"] += 1
            else:
                iteration_counts["6+ exports"] += 1

        return {
            "total_timelines": total_timelines,
            "exports_per_timeline": exports_per_timeline,
            "format_preferences": dict(sorted(
                format_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            "time_to_final": avg_time_to_final,
            "iteration_patterns": dict(iteration_counts)
        }

    def get_quality_trends(
        self,
        time_range: timedelta | None = None
    ) -> dict[str, Any]:
        """Analyze quality trends over time.
        
        Args:
            time_range: Time range to analyze
            
        Returns:
            Quality trend analysis
        """
        exports = self._filter_exports(time_range=time_range)

        if not exports:
            return {
                "resolution_trends": {},
                "duration_trends": {},
                "complexity_trends": {},
                "user_satisfaction": 0.0
            }

        # Sort by time
        sorted_exports = sorted(
            exports,
            key=lambda x: datetime.fromisoformat(x["start_time"])
        )

        # Group by week
        weekly_groups = defaultdict(list)
        for e in sorted_exports:
            week = datetime.fromisoformat(e["start_time"]).isocalendar()[:2]
            weekly_groups[week].append(e)

        # Analyze trends
        resolution_trends = {}
        duration_trends = {}
        complexity_trends = {}

        for week, week_exports in sorted(weekly_groups.items()):
            week_str = f"{week[0]}-W{week[1]}"

            # Resolution trend
            resolutions = [
                e["resolution"][0] * e["resolution"][1]
                for e in week_exports
                if e.get("resolution")
            ]
            if resolutions:
                resolution_trends[week_str] = sum(resolutions) / len(resolutions)

            # Duration trend
            durations = [e["total_duration"] for e in week_exports if e.get("total_duration")]
            if durations:
                duration_trends[week_str] = sum(durations) / len(durations)

            # Complexity trend (clips + transitions + effects)
            complexities = [
                e.get("clip_count", 0) + e.get("transition_count", 0) + e.get("effect_count", 0)
                for e in week_exports
            ]
            if complexities:
                complexity_trends[week_str] = sum(complexities) / len(complexities)

        # User satisfaction
        ratings = [e["user_rating"] for e in exports if e.get("user_rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        return {
            "resolution_trends": resolution_trends,
            "duration_trends": duration_trends,
            "complexity_trends": complexity_trends,
            "user_satisfaction": avg_rating
        }

    def suggest_improvements(self) -> list[dict[str, Any]]:
        """Suggest improvements based on export analytics.
        
        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Analyze recent exports
        recent_exports = self._filter_exports(time_range=timedelta(days=30))

        if not recent_exports:
            return suggestions

        # Check success rate
        successful = sum(1 for e in recent_exports if e.get("successful", False))
        success_rate = (successful / len(recent_exports) * 100) if recent_exports else 0

        if success_rate < 95:
            suggestions.append({
                "category": "reliability",
                "issue": f"Export success rate is {success_rate:.1f}%",
                "suggestion": "Review failed exports and improve error handling",
                "priority": "high"
            })

        # Check iteration count
        timeline_exports = defaultdict(list)
        for e in recent_exports:
            if e.get("timeline_id"):
                timeline_exports[e["timeline_id"]].append(e)

        high_iteration_timelines = [
            tid for tid, exports in timeline_exports.items()
            if len(exports) > 3
        ]

        if len(high_iteration_timelines) > len(timeline_exports) * 0.3:
            suggestions.append({
                "category": "efficiency",
                "issue": "Many timelines require multiple export attempts",
                "suggestion": "Improve preview accuracy and default settings",
                "priority": "medium"
            })

        # Check edit patterns
        high_edit_exports = [
            e for e in recent_exports
            if e.get("edit_count", 0) > 5
        ]

        if len(high_edit_exports) > len(recent_exports) * 0.2:
            suggestions.append({
                "category": "usability",
                "issue": "Exports require many manual edits",
                "suggestion": "Analyze common edits and automate them",
                "priority": "medium"
            })

        # Check platform adoption
        platform_stats = defaultdict(lambda: {"total": 0, "published": 0})
        for e in recent_exports:
            if e.get("platform"):
                platform_stats[e["platform"]]["total"] += 1
                if e.get("published"):
                    platform_stats[e["platform"]]["published"] += 1

        for platform, stats in platform_stats.items():
            if stats["total"] > 5:
                adoption_rate = (stats["published"] / stats["total"] * 100)
                if adoption_rate < 50:
                    suggestions.append({
                        "category": "platform_optimization",
                        "issue": f"{platform} exports have low adoption ({adoption_rate:.0f}%)",
                        "suggestion": f"Review {platform} export settings and optimizations",
                        "priority": "low"
                    })

        # Check export speed
        slow_exports = [
            e for e in recent_exports
            if e.get("export_speed_mbps", float('inf')) < 10
        ]

        if len(slow_exports) > len(recent_exports) * 0.1:
            suggestions.append({
                "category": "performance",
                "issue": "Some exports are running slowly",
                "suggestion": "Optimize export pipeline and consider caching",
                "priority": "low"
            })

        return suggestions

    def _filter_exports(
        self,
        format: ExportFormat | None = None,
        platform: str | None = None,
        time_range: timedelta | None = None
    ) -> list[dict[str, Any]]:
        """Filter exports based on criteria."""
        exports = self.export_history.copy()

        if format:
            exports = [e for e in exports if e.get("format") == format.value]

        if platform:
            exports = [e for e in exports if e.get("platform") == platform]

        if time_range:
            cutoff = datetime.now() - time_range
            exports = [
                e for e in exports
                if datetime.fromisoformat(e["start_time"]) > cutoff
            ]

        return exports

    def _update_patterns(self, metrics: ExportMetrics):
        """Update usage patterns based on new export."""
        # Update format usage
        format_key = metrics.format.value
        self.usage_patterns.setdefault("formats", {})
        self.usage_patterns["formats"][format_key] = \
            self.usage_patterns["formats"].get(format_key, 0) + 1

        # Update platform usage
        if metrics.platform:
            self.usage_patterns.setdefault("platforms", {})
            self.usage_patterns["platforms"][metrics.platform] = \
                self.usage_patterns["platforms"].get(metrics.platform, 0) + 1

        # Update time patterns (hour of day)
        hour = metrics.start_time.hour
        self.usage_patterns.setdefault("hours", {})
        self.usage_patterns["hours"][str(hour)] = \
            self.usage_patterns["hours"].get(str(hour), 0) + 1

        # Update day patterns
        day = metrics.start_time.strftime("%A")
        self.usage_patterns.setdefault("days", {})
        self.usage_patterns["days"][day] = \
            self.usage_patterns["days"].get(day, 0) + 1

    def _metrics_to_dict(self, metrics: ExportMetrics) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        data = asdict(metrics)

        # Convert datetime objects
        for key in ["start_time", "end_time"]:
            if data.get(key):
                data[key] = data[key].isoformat()

        # Convert enum
        if data.get("format"):
            data["format"] = data["format"].value

        return data

    def _load_export_history(self) -> list[dict[str, Any]]:
        """Load export history from disk."""
        if not self.exports_file.exists():
            return []

        try:
            with open(self.exports_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load export history: {e}")
            return []

    def _load_usage_patterns(self) -> dict[str, Any]:
        """Load usage patterns from disk."""
        if not self.patterns_file.exists():
            return {}

        try:
            with open(self.patterns_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load usage patterns: {e}")
            return {}

    def _save_export_history(self):
        """Save export history to disk."""
        try:
            # Keep only recent exports (last 500)
            if len(self.export_history) > 500:
                self.export_history = self.export_history[-500:]

            with open(self.exports_file, 'w') as f:
                json.dump(self.export_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save export history: {e}")

    def _save_patterns(self):
        """Save usage patterns to disk."""
        try:
            with open(self.patterns_file, 'w') as f:
                json.dump(self.usage_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage patterns: {e}")
