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

    def generate_insights(self) -> list[LearningInsight]:
        """Generate actionable insights from patterns.
        
        Returns:
            List of learning insights
        """
        insights = []

        # Style convergence insights
        insights.extend(self._generate_convergence_insights())

        # Improvement opportunity insights
        insights.extend(self._generate_improvement_insights())

        # Time-based insights
        insights.extend(self._generate_temporal_insights())

        # Workflow optimization insights
        if self.preference_tracker:
            insights.extend(self._generate_workflow_insights())

        # Store insights
        self.insights.extend(insights)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda i: priority_order.get(i.priority, 1))

        logger.info(f"Generated {len(insights)} insights")
        return insights

    def predict_preferences(
        self,
        context: dict[str, Any],
        preference_types: list[PreferenceType] | None = None
    ) -> dict[PreferenceType, list[tuple[Any, float]]]:
        """Predict likely preferences based on context and history.
        
        Args:
            context: Current context
            preference_types: Types to predict
            
        Returns:
            Predictions with confidence scores
        """
        predictions = {}
        types_to_predict = preference_types or list(PreferenceType)

        for pref_type in types_to_predict:
            # Get historical preferences
            history = self.style_memory.profile.preferences.get(pref_type, [])

            if not history:
                continue

            # Score each preference
            scored_prefs = []

            for pref in history:
                score = self._score_preference_likelihood(pref, context)
                if score > self.min_confidence:
                    scored_prefs.append((pref.value, score))

            # Sort by score
            scored_prefs.sort(key=lambda x: x[1], reverse=True)

            # Take top predictions
            predictions[pref_type] = scored_prefs[:5]

        return predictions

    def suggest_combinations(
        self,
        base_preferences: list[str],
        context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Suggest preference combinations based on learning.
        
        Args:
            base_preferences: Starting preferences
            context: Optional context
            
        Returns:
            List of combination suggestions with scores
        """
        suggestions = []

        # Get co-occurrence patterns
        relevant_patterns = []
        for pattern in self.patterns.values():
            if pattern.pattern_type == "cooccurrence":
                # Check if any base preference is in pattern
                if any(bp in pattern.preferences for bp in base_preferences):
                    relevant_patterns.append(pattern)

        # Generate suggestions from patterns
        for pattern in relevant_patterns:
            # Get preferences not in base
            additional = [
                p for p in pattern.preferences
                if p not in base_preferences
            ]

            if additional:
                suggestion = {
                    "combination": base_preferences + additional,
                    "confidence": pattern.confidence,
                    "success_rate": pattern.success_rate,
                    "frequency": pattern.frequency,
                    "reason": f"Frequently used together ({pattern.frequency} times)"
                }
                suggestions.append(suggestion)

        # Sort by confidence * success_rate
        suggestions.sort(
            key=lambda s: s["confidence"] * s["success_rate"],
            reverse=True
        )

        return suggestions[:10]

    def reinforce_pattern(self, preference_ids: list[str], successful: bool):
        """Reinforce or weaken a pattern based on outcome.
        
        Args:
            preference_ids: Preferences used
            successful: Whether outcome was successful
        """
        ",".join(sorted(preference_ids))

        # Find matching patterns
        for pattern in self.patterns.values():
            if sorted(pattern.preferences) == sorted(preference_ids):
                pattern.last_seen = datetime.now()
                pattern.reinforcement_count += 1

                # Update success rate
                if successful:
                    # Weighted update towards success
                    pattern.success_rate = (
                        pattern.success_rate * 0.9 + 1.0 * 0.1
                    )
                else:
                    # Weighted update towards failure
                    pattern.success_rate = (
                        pattern.success_rate * 0.9 + 0.0 * 0.1
                    )

                # Update confidence based on consistency
                pattern.confidence = min(
                    1.0,
                    pattern.confidence + 0.05 if successful else pattern.confidence - 0.02
                )

    def _analyze_cooccurrence(self) -> list[StylePattern]:
        """Analyze co-occurrence patterns."""
        patterns = []

        # Get co-occurrence data from style memory
        cooccurrence = self.style_memory.patterns.get("co_occurrence", {})

        # Find strong co-occurrences
        analyzed_pairs = set()

        for pref1, related in cooccurrence.items():
            for pref2, count in related.items():
                # Avoid duplicates
                pair = tuple(sorted([pref1, pref2]))
                if pair in analyzed_pairs:
                    continue
                analyzed_pairs.add(pair)

                if count >= self.min_pattern_frequency:
                    # Calculate success rate for this combination
                    combo_key = ",".join(sorted([pref1, pref2]))
                    success_data = self.style_memory.patterns.get(
                        "success_patterns", {}
                    ).get(combo_key, {"success": 0, "total": 0})

                    success_rate = (
                        success_data["success"] / success_data["total"]
                        if success_data["total"] > 0 else 0.5
                    )

                    if success_rate > 0.6:  # Only keep successful patterns
                        pattern = StylePattern(
                            pattern_id=f"cooccur_{pair[0]}_{pair[1]}",
                            pattern_type="cooccurrence",
                            preferences=list(pair),
                            frequency=count,
                            success_rate=success_rate,
                            confidence=min(1.0, count / 10)  # Confidence grows with usage
                        )
                        patterns.append(pattern)

        return patterns

    def _analyze_temporal_patterns(self) -> list[StylePattern]:
        """Analyze time-based patterns."""
        patterns = []

        # Analyze time-of-day preferences
        time_prefs = self.style_memory.profile.time_of_day_preferences

        for hour, pref_ids in time_prefs.items():
            if len(pref_ids) >= self.min_pattern_frequency:
                # Count most common preferences for this hour
                pref_counter = Counter(pref_ids)

                for pref_id, count in pref_counter.most_common(3):
                    if count >= self.min_pattern_frequency:
                        pattern = StylePattern(
                            pattern_id=f"temporal_hour{hour}_{pref_id}",
                            pattern_type="temporal",
                            preferences=[pref_id],
                            frequency=count,
                            success_rate=0.7,  # Default, could calculate from history
                            confidence=min(1.0, count / 10),
                            time_patterns={"hour": hour}
                        )
                        patterns.append(pattern)

        return patterns

    def _analyze_project_patterns(self) -> list[StylePattern]:
        """Analyze project-specific patterns."""
        patterns = []

        # Group preferences by project
        project_prefs = defaultdict(list)

        for pref in self.style_memory.all_preferences.values():
            for project, count in pref.project_associations.items():
                if count >= self.min_pattern_frequency:
                    project_prefs[project].append((pref.preference_id, count))

        # Find patterns per project
        for project, prefs in project_prefs.items():
            # Sort by count
            prefs.sort(key=lambda x: x[1], reverse=True)

            # Take top preferences
            top_prefs = [p[0] for p in prefs[:5]]

            if len(top_prefs) >= 2:
                pattern = StylePattern(
                    pattern_id=f"project_{project}_style",
                    pattern_type="project",
                    preferences=top_prefs,
                    frequency=sum(p[1] for p in prefs[:5]),
                    success_rate=0.8,  # Projects tend to have consistent styles
                    confidence=0.8,
                    projects=[project]
                )
                patterns.append(pattern)

        return patterns

    def _analyze_evolution_patterns(self) -> list[StylePattern]:
        """Analyze style evolution over time."""
        patterns = []

        # Get evolution data
        evolution = self.style_memory.get_style_evolution(
            time_range=self.learning_window
        )

        if len(evolution) < 2:
            return patterns

        # Look for trends
        for i in range(1, len(evolution)):
            prev_week = evolution[i-1]
            curr_week = evolution[i]

            # Check for significant changes
            if (curr_week["average_score"] - prev_week["average_score"]) > 0.1:
                # Improving trend
                new_prefs = [
                    val["value"] for val in curr_week["top_values"]
                    if val not in prev_week["top_values"]
                ]

                if new_prefs:
                    pattern = StylePattern(
                        pattern_id=f"evolution_{curr_week['week']}",
                        pattern_type="evolution",
                        preferences=new_prefs,
                        frequency=curr_week["new_preferences"],
                        success_rate=curr_week["average_score"],
                        confidence=0.7,
                        time_patterns={"week": curr_week["week"]}
                    )
                    patterns.append(pattern)

        return patterns

    def _generate_convergence_insights(self) -> list[LearningInsight]:
        """Generate insights about style convergence."""
        insights = []

        # Check if preferences are converging
        recent_prefs = []
        for pref in self.style_memory.all_preferences.values():
            if (datetime.now() - pref.last_used).days <= 7:
                recent_prefs.append(pref)

        if len(recent_prefs) >= 10:
            # Cluster preferences by type
            type_clusters = defaultdict(list)
            for pref in recent_prefs:
                type_clusters[pref.preference_type].append(pref)

            for pref_type, prefs in type_clusters.items():
                if len(prefs) >= 5:
                    # Check if converging to few values
                    unique_values = set(p.value for p in prefs)

                    if len(unique_values) <= 3:
                        top_values = Counter(p.value for p in prefs).most_common(3)

                        insight = LearningInsight(
                            insight_type="style_convergence",
                            title=f"Converging {pref_type.value} preferences",
                            description=(
                                f"Your {pref_type.value} choices are converging to "
                                f"{len(unique_values)} main options"
                            ),
                            confidence=0.8,
                            evidence=[
                                {"value": val, "count": count}
                                for val, count in top_values
                            ],
                            affected_preferences=[p.preference_id for p in prefs],
                            recommendations=[
                                f"Consider setting '{top_values[0][0]}' as default",
                                "Create templates with these preferred values"
                            ],
                            priority="medium"
                        )
                        insights.append(insight)

        return insights

    def _generate_improvement_insights(self) -> list[LearningInsight]:
        """Generate insights about improvement opportunities."""
        insights = []

        # Find low success rate patterns
        for pattern in self.patterns.values():
            if pattern.success_rate < 0.5 and pattern.frequency >= 5:
                insight = LearningInsight(
                    insight_type="improvement_opportunity",
                    title=f"Low success pattern: {pattern.pattern_type}",
                    description=(
                        f"This combination has only {pattern.success_rate:.0%} "
                        f"success rate despite being used {pattern.frequency} times"
                    ),
                    confidence=0.9,
                    evidence=[{
                        "pattern": pattern.preferences,
                        "success_rate": pattern.success_rate,
                        "frequency": pattern.frequency
                    }],
                    affected_preferences=pattern.preferences,
                    recommendations=[
                        "Review why this combination fails",
                        "Try alternative combinations",
                        "Adjust parameters when using together"
                    ],
                    priority="high"
                )
                insights.append(insight)

        return insights

    def _generate_temporal_insights(self) -> list[LearningInsight]:
        """Generate time-based insights."""
        insights = []

        # Analyze productivity by time
        time_patterns = defaultdict(list)

        for pattern in self.patterns.values():
            if pattern.pattern_type == "temporal":
                hour = pattern.time_patterns.get("hour")
                if hour is not None:
                    time_patterns[hour].append(pattern)

        # Find most productive times
        productive_hours = []
        for hour, patterns in time_patterns.items():
            avg_success = np.mean([p.success_rate for p in patterns])
            if avg_success > 0.75:
                productive_hours.append((hour, avg_success))

        if productive_hours:
            productive_hours.sort(key=lambda x: x[1], reverse=True)

            insight = LearningInsight(
                insight_type="temporal_optimization",
                title="Most productive creative hours",
                description=(
                    f"You achieve best results during hours: "
                    f"{', '.join(str(h[0]) for h in productive_hours[:3])}"
                ),
                confidence=0.85,
                evidence=[{
                    "hour": hour,
                    "success_rate": rate
                } for hour, rate in productive_hours[:5]],
                recommendations=[
                    "Schedule important work during these hours",
                    "Save routine tasks for other times"
                ],
                priority="medium"
            )
            insights.append(insight)

        return insights

    def _generate_workflow_insights(self) -> list[LearningInsight]:
        """Generate workflow-specific insights."""
        if not self.preference_tracker:
            return []

        insights = []

        # Get improvement areas
        improvements = self.preference_tracker.get_improvement_areas()

        for improvement in improvements[:3]:  # Top 3
            insight = LearningInsight(
                insight_type="workflow_optimization",
                title=f"Workflow improvement: {improvement['area']}",
                description=improvement['issue'],
                confidence=0.9,
                evidence=[improvement],
                recommendations=[improvement['suggestion']],
                priority="high" if improvement['count'] > 10 else "medium"
            )
            insights.append(insight)

        return insights

    def _score_preference_likelihood(
        self,
        preference: StylePreference,
        context: dict[str, Any]
    ) -> float:
        """Score how likely a preference is given context.
        
        Args:
            preference: Preference to score
            context: Current context
            
        Returns:
            Likelihood score (0-1)
        """
        score = preference.preference_score  # Base score

        # Boost for matching project
        if "project" in context:
            if context["project"] in preference.project_associations:
                project_uses = preference.project_associations[context["project"]]
                score *= (1 + min(0.5, project_uses / 10))

        # Boost for matching time
        if "hour" in context:
            hour = context["hour"]
            hour_prefs = self.style_memory.profile.time_of_day_preferences.get(hour, [])
            if preference.preference_id in hour_prefs:
                score *= 1.3

        # Boost for recent usage
        days_since_use = (datetime.now() - preference.last_used).days
        recency_boost = 1.0 / (1.0 + days_since_use / 7)
        score *= (0.7 + 0.3 * recency_boost)

        # Boost for high confidence
        score *= (0.5 + 0.5 * preference.confidence)

        return min(1.0, score)
