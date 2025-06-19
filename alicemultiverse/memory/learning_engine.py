"""Style learning engine for pattern detection and improvement."""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from ..core.structured_logging import get_logger
from .preference_tracker import PreferenceTracker
from .style_memory import PreferenceType, StyleMemory, StylePreference

logger = get_logger(__name__)


@dataclass
class StylePattern:
    """A detected style pattern."""
    pattern_id: str
    pattern_type: str
    confidence: float

    # Pattern details
    preferences: list[str]  # Preference IDs
    frequency: int
    success_rate: float

    # Context
    projects: list[str] = field(default_factory=list)
    time_patterns: dict[str, Any] = field(default_factory=dict)

    # Learning data
    first_detected: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    reinforcement_count: int = 0


@dataclass
class LearningInsight:
    """An insight derived from learning."""
    insight_type: str
    title: str
    description: str
    confidence: float

    # Supporting data
    evidence: list[dict[str, Any]] = field(default_factory=list)
    affected_preferences: list[str] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    validated: bool = False


class StyleLearningEngine:
    """Learns from style preferences and usage patterns."""

    def __init__(
        self,
        style_memory: StyleMemory,
        preference_tracker: PreferenceTracker | None = None
    ):
        """Initialize learning engine.

        Args:
            style_memory: StyleMemory instance
            preference_tracker: Optional PreferenceTracker
        """
        self.style_memory = style_memory
        self.preference_tracker = preference_tracker

        # Pattern storage
        self.patterns: dict[str, StylePattern] = {}
        self.insights: list[LearningInsight] = []

        # Learning parameters
        self.min_pattern_frequency = 3
        self.min_confidence = 0.6
        self.learning_window = timedelta(days=30)

    def analyze_patterns(self, force_full: bool = False) -> list[StylePattern]:
        """Analyze usage patterns and detect trends.

        Args:
            force_full: Force full analysis instead of incremental

        Returns:
            List of detected patterns
        """
        logger.info("Starting pattern analysis")

        patterns = []

        # Analyze co-occurrence patterns
        patterns.extend(self._analyze_cooccurrence())

        # Analyze temporal patterns
        patterns.extend(self._analyze_temporal_patterns())

        # Analyze project-specific patterns
        patterns.extend(self._analyze_project_patterns())

        # Analyze evolution patterns
        patterns.extend(self._analyze_evolution_patterns())

        # Store patterns
        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern

        logger.info(f"Detected {len(patterns)} patterns")
        return patterns

    # TODO: Review unreachable code - def generate_insights(self) -> list[LearningInsight]:
    # TODO: Review unreachable code - """Generate actionable insights from patterns.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of learning insights
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - insights = []

    # TODO: Review unreachable code - # Style convergence insights
    # TODO: Review unreachable code - insights.extend(self._generate_convergence_insights())

    # TODO: Review unreachable code - # Improvement opportunity insights
    # TODO: Review unreachable code - insights.extend(self._generate_improvement_insights())

    # TODO: Review unreachable code - # Time-based insights
    # TODO: Review unreachable code - insights.extend(self._generate_temporal_insights())

    # TODO: Review unreachable code - # Workflow optimization insights
    # TODO: Review unreachable code - if self.preference_tracker:
    # TODO: Review unreachable code - insights.extend(self._generate_workflow_insights())

    # TODO: Review unreachable code - # Store insights
    # TODO: Review unreachable code - self.insights.extend(insights)

    # TODO: Review unreachable code - # Sort by priority
    # TODO: Review unreachable code - priority_order = {"high": 0, "medium": 1, "low": 2}
    # TODO: Review unreachable code - insights.sort(key=lambda i: priority_order.get(i.priority, 1))

    # TODO: Review unreachable code - logger.info(f"Generated {len(insights)} insights")
    # TODO: Review unreachable code - return insights

    # TODO: Review unreachable code - def predict_preferences(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - context: dict[str, Any],
    # TODO: Review unreachable code - preference_types: list[PreferenceType] | None = None
    # TODO: Review unreachable code - ) -> dict[PreferenceType, list[tuple[Any, float]]]:
    # TODO: Review unreachable code - """Predict likely preferences based on context and history.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - context: Current context
    # TODO: Review unreachable code - preference_types: Types to predict

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Predictions with confidence scores
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - predictions = {}
    # TODO: Review unreachable code - types_to_predict = preference_types or list(PreferenceType)

    # TODO: Review unreachable code - for pref_type in types_to_predict:
    # TODO: Review unreachable code - # Get historical preferences
    # TODO: Review unreachable code - history = self.style_memory.profile.preferences.get(pref_type, [])

    # TODO: Review unreachable code - if not history:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Score each preference
    # TODO: Review unreachable code - scored_prefs = []

    # TODO: Review unreachable code - for pref in history:
    # TODO: Review unreachable code - score = self._score_preference_likelihood(pref, context)
    # TODO: Review unreachable code - if score > self.min_confidence:
    # TODO: Review unreachable code - scored_prefs.append((pref.value, score))

    # TODO: Review unreachable code - # Sort by score
    # TODO: Review unreachable code - scored_prefs.sort(key=lambda x: x[1], reverse=True)

    # TODO: Review unreachable code - # Take top predictions
    # TODO: Review unreachable code - predictions[pref_type] = scored_prefs[:5]

    # TODO: Review unreachable code - return predictions

    # TODO: Review unreachable code - def suggest_combinations(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - base_preferences: list[str],
    # TODO: Review unreachable code - context: dict[str, Any] | None = None
    # TODO: Review unreachable code - ) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Suggest preference combinations based on learning.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - base_preferences: Starting preferences
    # TODO: Review unreachable code - context: Optional context

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of combination suggestions with scores
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - suggestions = []

    # TODO: Review unreachable code - # Get co-occurrence patterns
    # TODO: Review unreachable code - relevant_patterns = []
    # TODO: Review unreachable code - for pattern in self.patterns.values():
    # TODO: Review unreachable code - if pattern.pattern_type == "cooccurrence":
    # TODO: Review unreachable code - # Check if any base preference is in pattern
    # TODO: Review unreachable code - if any(bp in pattern.preferences for bp in base_preferences):
    # TODO: Review unreachable code - relevant_patterns.append(pattern)

    # TODO: Review unreachable code - # Generate suggestions from patterns
    # TODO: Review unreachable code - for pattern in relevant_patterns:
    # TODO: Review unreachable code - # Get preferences not in base
    # TODO: Review unreachable code - additional = [
    # TODO: Review unreachable code - p for p in pattern.preferences
    # TODO: Review unreachable code - if p not in base_preferences
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - if additional:
    # TODO: Review unreachable code - suggestion = {
    # TODO: Review unreachable code - "combination": base_preferences + additional,
    # TODO: Review unreachable code - "confidence": pattern.confidence,
    # TODO: Review unreachable code - "success_rate": pattern.success_rate,
    # TODO: Review unreachable code - "frequency": pattern.frequency,
    # TODO: Review unreachable code - "reason": f"Frequently used together ({pattern.frequency} times)"
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - suggestions.append(suggestion)

    # TODO: Review unreachable code - # Sort by confidence * success_rate
    # TODO: Review unreachable code - suggestions.sort(
    # TODO: Review unreachable code - key=lambda s: s["confidence"] * s["success_rate"],
    # TODO: Review unreachable code - reverse=True
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return suggestions[:10]

    # TODO: Review unreachable code - def reinforce_pattern(self, preference_ids: list[str], successful: bool):
    # TODO: Review unreachable code - """Reinforce or weaken a pattern based on outcome.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - preference_ids: Preferences used
    # TODO: Review unreachable code - successful: Whether outcome was successful
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - ",".join(sorted(preference_ids))

    # TODO: Review unreachable code - # Find matching patterns
    # TODO: Review unreachable code - for pattern in self.patterns.values():
    # TODO: Review unreachable code - if sorted(pattern.preferences) == sorted(preference_ids):
    # TODO: Review unreachable code - pattern.last_seen = datetime.now()
    # TODO: Review unreachable code - pattern.reinforcement_count += 1

    # TODO: Review unreachable code - # Update success rate
    # TODO: Review unreachable code - if successful:
    # TODO: Review unreachable code - # Weighted update towards success
    # TODO: Review unreachable code - pattern.success_rate = (
    # TODO: Review unreachable code - pattern.success_rate * 0.9 + 1.0 * 0.1
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Weighted update towards failure
    # TODO: Review unreachable code - pattern.success_rate = (
    # TODO: Review unreachable code - pattern.success_rate * 0.9 + 0.0 * 0.1
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Update confidence based on consistency
    # TODO: Review unreachable code - pattern.confidence = min(
    # TODO: Review unreachable code - 1.0,
    # TODO: Review unreachable code - pattern.confidence + 0.05 if successful else pattern.confidence - 0.02
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _analyze_cooccurrence(self) -> list[StylePattern]:
    # TODO: Review unreachable code - """Analyze co-occurrence patterns."""
    # TODO: Review unreachable code - patterns = []

    # TODO: Review unreachable code - # Get co-occurrence data from style memory
    # TODO: Review unreachable code - cooccurrence = self.style_memory.patterns.get("co_occurrence", {})

    # TODO: Review unreachable code - # Find strong co-occurrences
    # TODO: Review unreachable code - analyzed_pairs = set()

    # TODO: Review unreachable code - for pref1, related in cooccurrence.items():
    # TODO: Review unreachable code - for pref2, count in related.items():
    # TODO: Review unreachable code - # Avoid duplicates
    # TODO: Review unreachable code - pair = tuple(sorted([pref1, pref2]))
    # TODO: Review unreachable code - if pair in analyzed_pairs:
    # TODO: Review unreachable code - continue
    # TODO: Review unreachable code - analyzed_pairs.add(pair)

    # TODO: Review unreachable code - if count >= self.min_pattern_frequency:
    # TODO: Review unreachable code - # Calculate success rate for this combination
    # TODO: Review unreachable code - combo_key = ",".join(sorted([pref1, pref2]))
    # TODO: Review unreachable code - success_data = self.style_memory.patterns.get(
    # TODO: Review unreachable code - "success_patterns", {}
    # TODO: Review unreachable code - ).get(combo_key, {"success": 0, "total": 0})

    # TODO: Review unreachable code - success_rate = (
    # TODO: Review unreachable code - success_data["success"] / success_data["total"]
    # TODO: Review unreachable code - if success_data is not None and success_data["total"] > 0 else 0.5
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if success_rate > 0.6:  # Only keep successful patterns
    # TODO: Review unreachable code - pattern = StylePattern(
    # TODO: Review unreachable code - pattern_id=f"cooccur_{pair[0]}_{pair[1]}",
    # TODO: Review unreachable code - pattern_type="cooccurrence",
    # TODO: Review unreachable code - preferences=list(pair),
    # TODO: Review unreachable code - frequency=count,
    # TODO: Review unreachable code - success_rate=success_rate,
    # TODO: Review unreachable code - confidence=min(1.0, count / 10)  # Confidence grows with usage
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - patterns.append(pattern)

    # TODO: Review unreachable code - return patterns

    # TODO: Review unreachable code - def _analyze_temporal_patterns(self) -> list[StylePattern]:
    # TODO: Review unreachable code - """Analyze time-based patterns."""
    # TODO: Review unreachable code - patterns = []

    # TODO: Review unreachable code - # Analyze time-of-day preferences
    # TODO: Review unreachable code - time_prefs = self.style_memory.profile.time_of_day_preferences

    # TODO: Review unreachable code - for hour, pref_ids in time_prefs.items():
    # TODO: Review unreachable code - if len(pref_ids) >= self.min_pattern_frequency:
    # TODO: Review unreachable code - # Count most common preferences for this hour
    # TODO: Review unreachable code - pref_counter = Counter(pref_ids)

    # TODO: Review unreachable code - for pref_id, count in pref_counter.most_common(3):
    # TODO: Review unreachable code - if count >= self.min_pattern_frequency:
    # TODO: Review unreachable code - pattern = StylePattern(
    # TODO: Review unreachable code - pattern_id=f"temporal_hour{hour}_{pref_id}",
    # TODO: Review unreachable code - pattern_type="temporal",
    # TODO: Review unreachable code - preferences=[pref_id],
    # TODO: Review unreachable code - frequency=count,
    # TODO: Review unreachable code - success_rate=0.7,  # Default, could calculate from history
    # TODO: Review unreachable code - confidence=min(1.0, count / 10),
    # TODO: Review unreachable code - time_patterns={"hour": hour}
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - patterns.append(pattern)

    # TODO: Review unreachable code - return patterns

    # TODO: Review unreachable code - def _analyze_project_patterns(self) -> list[StylePattern]:
    # TODO: Review unreachable code - """Analyze project-specific patterns."""
    # TODO: Review unreachable code - patterns = []

    # TODO: Review unreachable code - # Group preferences by project
    # TODO: Review unreachable code - project_prefs = defaultdict(list)

    # TODO: Review unreachable code - for pref in self.style_memory.all_preferences.values():
    # TODO: Review unreachable code - for project, count in pref.project_associations.items():
    # TODO: Review unreachable code - if count >= self.min_pattern_frequency:
    # TODO: Review unreachable code - project_prefs[project].append((pref.preference_id, count))

    # TODO: Review unreachable code - # Find patterns per project
    # TODO: Review unreachable code - for project, prefs in project_prefs.items():
    # TODO: Review unreachable code - # Sort by count
    # TODO: Review unreachable code - prefs.sort(key=lambda x: x[1], reverse=True)

    # TODO: Review unreachable code - # Take top preferences
    # TODO: Review unreachable code - top_prefs = [p[0] for p in prefs[:5]]

    # TODO: Review unreachable code - if len(top_prefs) >= 2:
    # TODO: Review unreachable code - pattern = StylePattern(
    # TODO: Review unreachable code - pattern_id=f"project_{project}_style",
    # TODO: Review unreachable code - pattern_type="project",
    # TODO: Review unreachable code - preferences=top_prefs,
    # TODO: Review unreachable code - frequency=sum(p[1] for p in prefs[:5]),
    # TODO: Review unreachable code - success_rate=0.8,  # Projects tend to have consistent styles
    # TODO: Review unreachable code - confidence=0.8,
    # TODO: Review unreachable code - projects=[project]
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - patterns.append(pattern)

    # TODO: Review unreachable code - return patterns

    # TODO: Review unreachable code - def _analyze_evolution_patterns(self) -> list[StylePattern]:
    # TODO: Review unreachable code - """Analyze style evolution over time."""
    # TODO: Review unreachable code - patterns = []

    # TODO: Review unreachable code - # Get evolution data
    # TODO: Review unreachable code - evolution = self.style_memory.get_style_evolution(
    # TODO: Review unreachable code - time_range=self.learning_window
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if len(evolution) < 2:
    # TODO: Review unreachable code - return patterns

    # TODO: Review unreachable code - # Look for trends
    # TODO: Review unreachable code - for i in range(1, len(evolution)):
    # TODO: Review unreachable code - prev_week = evolution[i-1]
    # TODO: Review unreachable code - curr_week = evolution[i]

    # TODO: Review unreachable code - # Check for significant changes
    # TODO: Review unreachable code - if (curr_week["average_score"] - prev_week["average_score"]) > 0.1:
    # TODO: Review unreachable code - # Improving trend
    # TODO: Review unreachable code - new_prefs = [
    # TODO: Review unreachable code - val["value"] for val in curr_week["top_values"]
    # TODO: Review unreachable code - if val not in prev_week["top_values"]
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - if new_prefs:
    # TODO: Review unreachable code - pattern = StylePattern(
    # TODO: Review unreachable code - pattern_id=f"evolution_{curr_week['week']}",
    # TODO: Review unreachable code - pattern_type="evolution",
    # TODO: Review unreachable code - preferences=new_prefs,
    # TODO: Review unreachable code - frequency=curr_week["new_preferences"],
    # TODO: Review unreachable code - success_rate=curr_week["average_score"],
    # TODO: Review unreachable code - confidence=0.7,
    # TODO: Review unreachable code - time_patterns={"week": curr_week["week"]}
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - patterns.append(pattern)

    # TODO: Review unreachable code - return patterns

    # TODO: Review unreachable code - def _generate_convergence_insights(self) -> list[LearningInsight]:
    # TODO: Review unreachable code - """Generate insights about style convergence."""
    # TODO: Review unreachable code - insights = []

    # TODO: Review unreachable code - # Check if preferences are converging
    # TODO: Review unreachable code - recent_prefs = []
    # TODO: Review unreachable code - for pref in self.style_memory.all_preferences.values():
    # TODO: Review unreachable code - if (datetime.now() - pref.last_used).days <= 7:
    # TODO: Review unreachable code - recent_prefs.append(pref)

    # TODO: Review unreachable code - if len(recent_prefs) >= 10:
    # TODO: Review unreachable code - # Cluster preferences by type
    # TODO: Review unreachable code - type_clusters = defaultdict(list)
    # TODO: Review unreachable code - for pref in recent_prefs:
    # TODO: Review unreachable code - type_clusters[pref.preference_type].append(pref)

    # TODO: Review unreachable code - for pref_type, prefs in type_clusters.items():
    # TODO: Review unreachable code - if len(prefs) >= 5:
    # TODO: Review unreachable code - # Check if converging to few values
    # TODO: Review unreachable code - unique_values = set(p.value for p in prefs)

    # TODO: Review unreachable code - if len(unique_values) <= 3:
    # TODO: Review unreachable code - top_values = Counter(p.value for p in prefs).most_common(3)

    # TODO: Review unreachable code - insight = LearningInsight(
    # TODO: Review unreachable code - insight_type="style_convergence",
    # TODO: Review unreachable code - title=f"Converging {pref_type.value} preferences",
    # TODO: Review unreachable code - description=(
    # TODO: Review unreachable code - f"Your {pref_type.value} choices are converging to "
    # TODO: Review unreachable code - f"{len(unique_values)} main options"
    # TODO: Review unreachable code - ),
    # TODO: Review unreachable code - confidence=0.8,
    # TODO: Review unreachable code - evidence=[
    # TODO: Review unreachable code - {"value": val, "count": count}
    # TODO: Review unreachable code - for val, count in top_values
    # TODO: Review unreachable code - ],
    # TODO: Review unreachable code - affected_preferences=[p.preference_id for p in prefs],
    # TODO: Review unreachable code - recommendations=[
    # TODO: Review unreachable code - f"Consider setting '{top_values[0][0]}' as default",
    # TODO: Review unreachable code - "Create templates with these preferred values"
    # TODO: Review unreachable code - ],
    # TODO: Review unreachable code - priority="medium"
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - insights.append(insight)

    # TODO: Review unreachable code - return insights

    # TODO: Review unreachable code - def _generate_improvement_insights(self) -> list[LearningInsight]:
    # TODO: Review unreachable code - """Generate insights about improvement opportunities."""
    # TODO: Review unreachable code - insights = []

    # TODO: Review unreachable code - # Find low success rate patterns
    # TODO: Review unreachable code - for pattern in self.patterns.values():
    # TODO: Review unreachable code - if pattern.success_rate < 0.5 and pattern.frequency >= 5:
    # TODO: Review unreachable code - insight = LearningInsight(
    # TODO: Review unreachable code - insight_type="improvement_opportunity",
    # TODO: Review unreachable code - title=f"Low success pattern: {pattern.pattern_type}",
    # TODO: Review unreachable code - description=(
    # TODO: Review unreachable code - f"This combination has only {pattern.success_rate:.0%} "
    # TODO: Review unreachable code - f"success rate despite being used {pattern.frequency} times"
    # TODO: Review unreachable code - ),
    # TODO: Review unreachable code - confidence=0.9,
    # TODO: Review unreachable code - evidence=[{
    # TODO: Review unreachable code - "pattern": pattern.preferences,
    # TODO: Review unreachable code - "success_rate": pattern.success_rate,
    # TODO: Review unreachable code - "frequency": pattern.frequency
    # TODO: Review unreachable code - }],
    # TODO: Review unreachable code - affected_preferences=pattern.preferences,
    # TODO: Review unreachable code - recommendations=[
    # TODO: Review unreachable code - "Review why this combination fails",
    # TODO: Review unreachable code - "Try alternative combinations",
    # TODO: Review unreachable code - "Adjust parameters when using together"
    # TODO: Review unreachable code - ],
    # TODO: Review unreachable code - priority="high"
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - insights.append(insight)

    # TODO: Review unreachable code - return insights

    # TODO: Review unreachable code - def _generate_temporal_insights(self) -> list[LearningInsight]:
    # TODO: Review unreachable code - """Generate time-based insights."""
    # TODO: Review unreachable code - insights = []

    # TODO: Review unreachable code - # Analyze productivity by time
    # TODO: Review unreachable code - time_patterns = defaultdict(list)

    # TODO: Review unreachable code - for pattern in self.patterns.values():
    # TODO: Review unreachable code - if pattern.pattern_type == "temporal":
    # TODO: Review unreachable code - hour = pattern.time_patterns.get("hour")
    # TODO: Review unreachable code - if hour is not None:
    # TODO: Review unreachable code - time_patterns[hour].append(pattern)

    # TODO: Review unreachable code - # Find most productive times
    # TODO: Review unreachable code - productive_hours = []
    # TODO: Review unreachable code - for hour, patterns in time_patterns.items():
    # TODO: Review unreachable code - avg_success = np.mean([p.success_rate for p in patterns])
    # TODO: Review unreachable code - if avg_success > 0.75:
    # TODO: Review unreachable code - productive_hours.append((hour, avg_success))

    # TODO: Review unreachable code - if productive_hours:
    # TODO: Review unreachable code - productive_hours.sort(key=lambda x: x[1], reverse=True)

    # TODO: Review unreachable code - insight = LearningInsight(
    # TODO: Review unreachable code - insight_type="temporal_optimization",
    # TODO: Review unreachable code - title="Most productive creative hours",
    # TODO: Review unreachable code - description=(
    # TODO: Review unreachable code - f"You achieve best results during hours: "
    # TODO: Review unreachable code - f"{', '.join(str(h[0]) for h in productive_hours[:3])}"
    # TODO: Review unreachable code - ),
    # TODO: Review unreachable code - confidence=0.85,
    # TODO: Review unreachable code - evidence=[{
    # TODO: Review unreachable code - "hour": hour,
    # TODO: Review unreachable code - "success_rate": rate
    # TODO: Review unreachable code - } for hour, rate in productive_hours[:5]],
    # TODO: Review unreachable code - recommendations=[
    # TODO: Review unreachable code - "Schedule important work during these hours",
    # TODO: Review unreachable code - "Save routine tasks for other times"
    # TODO: Review unreachable code - ],
    # TODO: Review unreachable code - priority="medium"
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - insights.append(insight)

    # TODO: Review unreachable code - return insights

    # TODO: Review unreachable code - def _generate_workflow_insights(self) -> list[LearningInsight]:
    # TODO: Review unreachable code - """Generate workflow-specific insights."""
    # TODO: Review unreachable code - if not self.preference_tracker:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - insights = []

    # TODO: Review unreachable code - # Get improvement areas
    # TODO: Review unreachable code - improvements = self.preference_tracker.get_improvement_areas()

    # TODO: Review unreachable code - for improvement in improvements[:3]:  # Top 3
    # TODO: Review unreachable code - insight = LearningInsight(
    # TODO: Review unreachable code - insight_type="workflow_optimization",
    # TODO: Review unreachable code - title=f"Workflow improvement: {improvement['area']}",
    # TODO: Review unreachable code - description=improvement['issue'],
    # TODO: Review unreachable code - confidence=0.9,
    # TODO: Review unreachable code - evidence=[improvement],
    # TODO: Review unreachable code - recommendations=[improvement['suggestion']],
    # TODO: Review unreachable code - priority="high" if improvement['count'] > 10 else "medium"
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - insights.append(insight)

    # TODO: Review unreachable code - return insights

    # TODO: Review unreachable code - def _score_preference_likelihood(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - preference: StylePreference,
    # TODO: Review unreachable code - context: dict[str, Any]
    # TODO: Review unreachable code - ) -> float:
    # TODO: Review unreachable code - """Score how likely a preference is given context.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - preference: Preference to score
    # TODO: Review unreachable code - context: Current context

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Likelihood score (0-1)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - score = preference.preference_score  # Base score

    # TODO: Review unreachable code - # Boost for matching project
    # TODO: Review unreachable code - if context is not None and "project" in context:
    # TODO: Review unreachable code - if context is not None and context["project"] in preference.project_associations:
    # TODO: Review unreachable code - project_uses = preference.project_associations[context["project"]]
    # TODO: Review unreachable code - score *= (1 + min(0.5, project_uses / 10))

    # TODO: Review unreachable code - # Boost for matching time
    # TODO: Review unreachable code - if context is not None and "hour" in context:
    # TODO: Review unreachable code - hour = context["hour"]
    # TODO: Review unreachable code - hour_prefs = self.style_memory.profile.time_of_day_preferences.get(hour, [])
    # TODO: Review unreachable code - if preference.preference_id in hour_prefs:
    # TODO: Review unreachable code - score *= 1.3

    # TODO: Review unreachable code - # Boost for recent usage
    # TODO: Review unreachable code - days_since_use = (datetime.now() - preference.last_used).days
    # TODO: Review unreachable code - recency_boost = 1.0 / (1.0 + days_since_use / 7)
    # TODO: Review unreachable code - score *= (0.7 + 0.3 * recency_boost)

    # TODO: Review unreachable code - # Boost for high confidence
    # TODO: Review unreachable code - score *= (0.5 + 0.5 * preference.confidence)

    # TODO: Review unreachable code - return min(1.0, score)
