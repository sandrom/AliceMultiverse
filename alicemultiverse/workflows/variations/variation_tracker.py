"""Track and analyze content variation performance."""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VariationMetrics:
    """Metrics for a content variation."""
    variation_id: str
    content_id: str
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    saves: int = 0
    play_duration: float = 0.0  # Average seconds watched
    engagement_rate: float = 0.0
    conversion_rate: float = 0.0
    revenue: float = 0.0
    tracked_since: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def calculate_engagement_rate(self):
        """Calculate engagement rate from metrics."""
        if self.views == 0:
            self.engagement_rate = 0.0
        else:
            interactions = self.likes + self.shares + self.comments + self.saves
            self.engagement_rate = interactions / self.views

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "variation_id": self.variation_id,
            "content_id": self.content_id,
            "views": self.views,
            "likes": self.likes,
            "shares": self.shares,
            "comments": self.comments,
            "saves": self.saves,
            "play_duration": self.play_duration,
            "engagement_rate": self.engagement_rate,
            "conversion_rate": self.conversion_rate,
            "revenue": self.revenue,
            "tracked_since": self.tracked_since.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VariationMetrics":
        """Create from dictionary."""
        data["tracked_since"] = datetime.fromisoformat(data["tracked_since"])
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)


@dataclass
class ContentGroup:
    """Group of related content variations."""
    group_id: str
    base_content_id: str
    variation_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


class VariationTracker:
    """Track performance of content variations."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize the variation tracker.

        Args:
            cache_dir: Directory for caching metrics
        """
        self.cache_dir = cache_dir or Path("data/variation_metrics")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory caches
        self.metrics: dict[str, VariationMetrics] = {}
        self.content_groups: dict[str, ContentGroup] = {}
        self.content_to_group: dict[str, str] = {}  # content_id -> group_id

        # Load existing data
        self._load_metrics()
        self._load_groups()

    def _load_metrics(self):
        """Load metrics from cache."""
        metrics_file = self.cache_dir / "variation_metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                data = json.load(f)
                for variation_id, metric_data in data.items():
                    self.metrics[variation_id] = VariationMetrics.from_dict(metric_data)

    def _load_groups(self):
        """Load content groups from cache."""
        groups_file = self.cache_dir / "content_groups.json"
        if groups_file.exists():
            with open(groups_file) as f:
                data = json.load(f)
                for group_id, group_data in data.items():
                    group = ContentGroup(
                        group_id=group_id,
                        base_content_id=group_data["base_content_id"],
                        variation_ids=group_data["variation_ids"],
                        created_at=datetime.fromisoformat(group_data["created_at"]),
                        tags=set(group_data.get("tags", [])),
                        metadata=group_data.get("metadata", {}),
                    )
                    self.content_groups[group_id] = group

                    # Build reverse mapping
                    self.content_to_group[group.base_content_id] = group_id
                    for var_id in group.variation_ids:
                        self.content_to_group[var_id] = group_id

    def _save_metrics(self):
        """Save metrics to cache."""
        data = {
            var_id: metrics.to_dict()
            for var_id, metrics in self.metrics.items()
        }

        with open(self.cache_dir / "variation_metrics.json", "w") as f:
            json.dump(data, f, indent=2)

    def _save_groups(self):
        """Save content groups to cache."""
        data = {}
        for group_id, group in self.content_groups.items():
            data[group_id] = {
                "base_content_id": group.base_content_id,
                "variation_ids": group.variation_ids,
                "created_at": group.created_at.isoformat(),
                "tags": list(group.tags),
                "metadata": group.metadata,
            }

        with open(self.cache_dir / "content_groups.json", "w") as f:
            json.dump(data, f, indent=2)

    def create_content_group(
        self,
        base_content_id: str,
        variation_ids: list[str],
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new content group.

        Args:
            base_content_id: ID of the base content
            variation_ids: IDs of variations
            tags: Optional tags for the group
            metadata: Optional metadata

        Returns:
            Group ID
        """
        # Use content-based ID: hash of base content + timestamp
        id_source = f"{base_content_id}:{datetime.now().isoformat()}"
        group_id = hashlib.sha256(id_source.encode()).hexdigest()[:16]

        group = ContentGroup(
            group_id=group_id,
            base_content_id=base_content_id,
            variation_ids=variation_ids,
            tags=tags or set(),
            metadata=metadata or {},
        )

        self.content_groups[group_id] = group

        # Update mappings
        self.content_to_group[base_content_id] = group_id
        for var_id in variation_ids:
            self.content_to_group[var_id] = group_id

        self._save_groups()

        return group_id

    def track_metrics(
        self,
        content_id: str,
        metrics_update: dict[str, Any],
    ):
        """Update metrics for a content variation.

        Args:
            content_id: Content or variation ID
            metrics_update: Dictionary of metric updates
        """
        # Get or create metrics
        if content_id not in self.metrics:
            self.metrics[content_id] = VariationMetrics(
                variation_id=content_id,
                content_id=content_id,
            )

        metrics = self.metrics[content_id]

        # Update metrics
        for key, value in metrics_update.items():
            if hasattr(metrics, key):
                if key in ["views", "likes", "shares", "comments", "saves"]:
                    # Increment counters
                    setattr(metrics, key, getattr(metrics, key) + value)
                else:
                    # Set values
                    setattr(metrics, key, value)

        # Recalculate rates
        metrics.calculate_engagement_rate()
        metrics.last_updated = datetime.now()

        self._save_metrics()

    def get_variation_performance(
        self,
        variation_id: str,
    ) -> VariationMetrics | None:
        """Get performance metrics for a variation.

        Args:
            variation_id: Variation ID

        Returns:
            Metrics or None if not found
        """
        return self.metrics.get(variation_id)

    def get_group_performance(
        self,
        group_id: str,
    ) -> dict[str, Any]:
        """Get aggregated performance for a content group.

        Args:
            group_id: Group ID

        Returns:
            Aggregated performance data
        """
        if group_id not in self.content_groups:
            return {}

        group = self.content_groups[group_id]

        # Collect metrics for all variations
        all_metrics = []
        for content_id in [group.base_content_id] + group.variation_ids:
            if content_id in self.metrics:
                all_metrics.append(self.metrics[content_id])

        if not all_metrics:
            return {}

        # Calculate aggregated stats
        total_views = sum(m.views for m in all_metrics)
        total_engagement = sum(m.likes + m.shares + m.comments + m.saves for m in all_metrics)

        # Find best performer
        best_performer = max(all_metrics, key=lambda m: m.engagement_rate)

        # Calculate improvement
        base_metrics = self.metrics.get(group.base_content_id)
        improvement = 0.0
        if base_metrics and base_metrics.engagement_rate > 0:
            improvement = (
                (best_performer.engagement_rate - base_metrics.engagement_rate)
                / base_metrics.engagement_rate * 100
            )

        return {
            "group_id": group_id,
            "total_variations": len(group.variation_ids),
            "total_views": total_views,
            "average_engagement_rate": total_engagement / total_views if total_views > 0 else 0,
            "best_performer": {
                "content_id": best_performer.content_id,
                "engagement_rate": best_performer.engagement_rate,
                "views": best_performer.views,
            },
            "improvement_percentage": improvement,
            "metrics_by_content": {
                m.content_id: {
                    "views": m.views,
                    "engagement_rate": m.engagement_rate,
                    "play_duration": m.play_duration,
                }
                for m in all_metrics
            },
        }

    def find_top_variations(
        self,
        metric: str = "engagement_rate",
        limit: int = 10,
        min_views: int = 100,
    ) -> list[tuple[str, VariationMetrics]]:
        """Find top performing variations.

        Args:
            metric: Metric to sort by
            limit: Maximum results
            min_views: Minimum views threshold

        Returns:
            List of (content_id, metrics) tuples
        """
        # Filter by minimum views
        qualified_metrics = [
            (content_id, metrics)
            for content_id, metrics in self.metrics.items()
            if metrics.views >= min_views
        ]

        # Sort by metric
        qualified_metrics.sort(
            key=lambda x: getattr(x[1], metric, 0),
            reverse=True
        )

        return qualified_metrics[:limit]

    def get_variation_insights(
        self,
        time_window: timedelta | None = None,
    ) -> dict[str, Any]:
        """Get insights about variation performance.

        Args:
            time_window: Optional time window for analysis

        Returns:
            Insights dictionary
        """
        insights = {
            "total_variations_tracked": len(self.metrics),
            "total_groups": len(self.content_groups),
            "average_improvement": 0.0,
            "best_variation_types": [],
            "trending_up": [],
            "trending_down": [],
        }

        # Filter by time window if specified
        if time_window:
            cutoff = datetime.now() - time_window
            relevant_metrics = [
                m for m in self.metrics.values()
                if m.tracked_since >= cutoff
            ]
        else:
            relevant_metrics = list(self.metrics.values())

        if not relevant_metrics:
            return insights

        # Calculate average improvement
        improvements = []
        for group in self.content_groups.values():
            perf = self.get_group_performance(group.group_id)
            if perf and "improvement_percentage" in perf:
                improvements.append(perf["improvement_percentage"])

        if improvements:
            insights["average_improvement"] = sum(improvements) / len(improvements)

        # Find trending content
        recent_window = timedelta(days=7)
        recent_cutoff = datetime.now() - recent_window

        for metrics in relevant_metrics:
            if metrics.last_updated >= recent_cutoff:
                # Simple trend detection based on engagement
                if metrics.engagement_rate > 0.1:  # High engagement
                    insights["trending_up"].append({
                        "content_id": metrics.content_id,
                        "engagement_rate": metrics.engagement_rate,
                        "views": metrics.views,
                    })
                elif metrics.engagement_rate < 0.02:  # Low engagement
                    insights["trending_down"].append({
                        "content_id": metrics.content_id,
                        "engagement_rate": metrics.engagement_rate,
                        "views": metrics.views,
                    })

        # Sort trending lists
        insights["trending_up"].sort(
            key=lambda x: x["engagement_rate"],
            reverse=True
        )
        insights["trending_down"].sort(
            key=lambda x: x["views"],
            reverse=True
        )

        # Limit trending lists
        insights["trending_up"] = insights["trending_up"][:5]
        insights["trending_down"] = insights["trending_down"][:5]

        return insights

    def export_analytics(
        self,
        output_path: Path | None = None,
    ) -> Path:
        """Export analytics data for external analysis.

        Args:
            output_path: Optional output path

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.cache_dir / f"analytics_export_{timestamp}.json"

        export_data = {
            "export_date": datetime.now().isoformat(),
            "metrics": {
                content_id: metrics.to_dict()
                for content_id, metrics in self.metrics.items()
            },
            "groups": {},
            "insights": self.get_variation_insights(),
        }

        # Add group performance
        for group_id, group in self.content_groups.items():
            export_data["groups"][group_id] = {
                "base_content_id": group.base_content_id,
                "variation_ids": group.variation_ids,
                "tags": list(group.tags),
                "performance": self.get_group_performance(group_id),
            }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported analytics to {output_path}")
        return output_path
