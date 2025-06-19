"""Style memory system for tracking preferences and patterns."""

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class PreferenceType(Enum):
    """Types of style preferences."""
    COLOR_PALETTE = "color_palette"
    COMPOSITION = "composition"
    LIGHTING = "lighting"
    TEXTURE = "texture"
    MOOD = "mood"
    SUBJECT = "subject"
    TECHNIQUE = "technique"
    TRANSITION = "transition"
    PACING = "pacing"
    EFFECT = "effect"


@dataclass
class StylePreference:
    """A single style preference record."""
    preference_id: str
    preference_type: PreferenceType
    value: Any
    context: dict[str, Any] = field(default_factory=dict)

    # Usage tracking
    first_seen: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_count: int = 0

    # Scoring
    preference_score: float = 0.0  # 0-1, how much user prefers this
    confidence: float = 0.0  # 0-1, how confident we are

    # Associations
    related_preferences: list[str] = field(default_factory=list)
    negative_associations: list[str] = field(default_factory=list)
    project_associations: dict[str, int] = field(default_factory=dict)

    # Metadata
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    auto_detected: bool = True

    def update_usage(self, successful: bool = True, project: str | None = None):
        """Update usage statistics."""
        self.usage_count += 1
        self.last_used = datetime.now()

        if successful:
            self.success_count += 1

        if project:
            self.project_associations[project] = \
                self.project_associations.get(project, 0) + 1

        # Update preference score
        success_rate = self.success_count / self.usage_count if self.usage_count > 0 else 0
        recency_weight = 1.0 / (1.0 + (datetime.now() - self.last_used).days / 7)

        self.preference_score = success_rate * 0.7 + recency_weight * 0.3
        self.confidence = min(1.0, self.usage_count / 10)  # Full confidence at 10 uses

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['preference_type'] = self.preference_type.value
        data['first_seen'] = self.first_seen.isoformat()
        data['last_used'] = self.last_used.isoformat()
        return data

    # TODO: Review unreachable code - @classmethod
    # TODO: Review unreachable code - def from_dict(cls, data: dict[str, Any]) -> 'StylePreference':
    # TODO: Review unreachable code - """Create from dictionary."""
    # TODO: Review unreachable code - data = data.copy()
    # TODO: Review unreachable code - data['preference_type'] = PreferenceType(data['preference_type'])
    # TODO: Review unreachable code - data['first_seen'] = datetime.fromisoformat(data['first_seen'])
    # TODO: Review unreachable code - data['last_used'] = datetime.fromisoformat(data['last_used'])
    # TODO: Review unreachable code - return cls(**data)


@dataclass
class StyleProfile:
    """Complete style profile for a user."""
    profile_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Preference collections by type
    preferences: dict[PreferenceType, list[StylePreference]] = field(default_factory=dict)

    # Global patterns
    favorite_combinations: list[list[str]] = field(default_factory=list)
    avoided_combinations: list[list[str]] = field(default_factory=list)

    # Time-based patterns
    time_of_day_preferences: dict[int, list[str]] = field(default_factory=dict)  # hour -> prefs
    seasonal_preferences: dict[str, list[str]] = field(default_factory=dict)  # season -> prefs

    # Project patterns
    project_styles: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Evolution tracking
    style_evolution: list[dict[str, Any]] = field(default_factory=list)
    milestone_changes: list[dict[str, Any]] = field(default_factory=list)

    def add_preference(self, preference: StylePreference):
        """Add a preference to the profile."""
        pref_type = preference.preference_type
        if pref_type not in self.preferences:
            self.preferences[pref_type] = []

        # Check if already exists
        for existing in self.preferences[pref_type]:
            if existing.value == preference.value:
                existing.update_usage()
                return

        # TODO: Review unreachable code - self.preferences[pref_type].append(preference)
        # TODO: Review unreachable code - self.updated_at = datetime.now()

    def get_top_preferences(
        self,
        preference_type: PreferenceType | None = None,
        limit: int = 10,
        min_confidence: float = 0.3
    ) -> list[StylePreference]:
        """Get top preferences by score."""
        if preference_type:
            prefs = self.preferences.get(preference_type, [])
        else:
            prefs = []
            for pref_list in self.preferences.values():
                prefs.extend(pref_list)

        # Filter by confidence
        prefs = [p for p in prefs if p.confidence >= min_confidence]

        # Sort by preference score
        prefs.sort(key=lambda p: p.preference_score, reverse=True)

        return prefs[:limit]

    # TODO: Review unreachable code - def track_combination(self, preference_ids: list[str], successful: bool = True):
    # TODO: Review unreachable code - """Track preference combinations."""
    # TODO: Review unreachable code - combo = sorted(preference_ids)

    # TODO: Review unreachable code - if successful:
    # TODO: Review unreachable code - # Add to favorites if used multiple times
    # TODO: Review unreachable code - combo_str = ",".join(combo)
    # TODO: Review unreachable code - found = False

    # TODO: Review unreachable code - for fav in self.favorite_combinations:
    # TODO: Review unreachable code - if ",".join(sorted(fav)) == combo_str:
    # TODO: Review unreachable code - found = True
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - if not found and len(combo) > 1:
    # TODO: Review unreachable code - self.favorite_combinations.append(combo)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Add to avoided if failed
    # TODO: Review unreachable code - if combo not in self.avoided_combinations:
    # TODO: Review unreachable code - self.avoided_combinations.append(combo)

    # TODO: Review unreachable code - self.updated_at = datetime.now()


class StyleMemory:
    """Main style memory system."""

    def __init__(self, data_dir: Path | None = None):
        """Initialize style memory.

        Args:
            data_dir: Directory for storing memory data
        """
        self.data_dir = data_dir or (Path.home() / ".alice" / "memory")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.profile_file = self.data_dir / "style_profile.json"
        self.preferences_file = self.data_dir / "preferences.json"
        self.patterns_file = self.data_dir / "patterns.json"

        # Load data
        self.profile = self._load_profile()
        self.all_preferences = self._load_preferences()
        self.patterns = self._load_patterns()

        # Active session tracking
        self.session_preferences: list[str] = []
        self.session_start = datetime.now()

    def track_style_choice(
        self,
        preference_type: PreferenceType,
        value: Any,
        context: dict[str, Any] | None = None,
        project: str | None = None,
        tags: list[str] | None = None
    ) -> StylePreference:
        """Track a style choice.

        Args:
            preference_type: Type of preference
            value: The chosen value
            context: Additional context
            project: Associated project
            tags: Descriptive tags

        Returns:
            Created or updated preference
        """
        # Create preference ID
        pref_id = f"{preference_type.value}:{value!s}"

        # Check if exists
        if pref_id in self.all_preferences:
            preference = self.all_preferences[pref_id]
            preference.update_usage(successful=True, project=project)
        else:
            # Create new preference
            preference = StylePreference(
                preference_id=pref_id,
                preference_type=preference_type,
                value=value,
                context=context or {},
                tags=tags or [],
                usage_count=1,
                success_count=1
            )

            if project:
                preference.project_associations[project] = 1

            self.all_preferences[pref_id] = preference

        # Add to profile
        self.profile.add_preference(preference)

        # Track in session
        self.session_preferences.append(pref_id)

        # Track time patterns
        hour = datetime.now().hour
        if hour not in self.profile.time_of_day_preferences:
            self.profile.time_of_day_preferences[hour] = []
        self.profile.time_of_day_preferences[hour].append(pref_id)

        # Save periodically
        if len(self.session_preferences) % 10 == 0:
            self._save_all()

        logger.info(f"Tracked style preference: {pref_id}")
        return preference

    # TODO: Review unreachable code - def track_workflow_result(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - preference_ids: list[str],
    # TODO: Review unreachable code - successful: bool,
    # TODO: Review unreachable code - quality_score: float | None = None,
    # TODO: Review unreachable code - user_rating: int | None = None
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - """Track the result of using certain preferences.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - preference_ids: Preferences used
    # TODO: Review unreachable code - successful: Whether the result was successful
    # TODO: Review unreachable code - quality_score: Objective quality score (0-1)
    # TODO: Review unreachable code - user_rating: User rating (1-5)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Update individual preferences
    # TODO: Review unreachable code - for pref_id in preference_ids:
    # TODO: Review unreachable code - if pref_id in self.all_preferences:
    # TODO: Review unreachable code - pref = self.all_preferences[pref_id]
    # TODO: Review unreachable code - pref.update_usage(successful=successful)

    # TODO: Review unreachable code - # Adjust score based on quality and rating
    # TODO: Review unreachable code - if quality_score is not None:
    # TODO: Review unreachable code - adjustment = (quality_score - 0.5) * 0.1
    # TODO: Review unreachable code - pref.preference_score = max(0, min(1, pref.preference_score + adjustment))

    # TODO: Review unreachable code - if user_rating is not None:
    # TODO: Review unreachable code - adjustment = (user_rating - 3) * 0.05
    # TODO: Review unreachable code - pref.preference_score = max(0, min(1, pref.preference_score + adjustment))

    # TODO: Review unreachable code - # Track combinations
    # TODO: Review unreachable code - if len(preference_ids) > 1:
    # TODO: Review unreachable code - self.profile.track_combination(preference_ids, successful)

    # TODO: Review unreachable code - # Update patterns
    # TODO: Review unreachable code - self._update_patterns(preference_ids, successful)

    # TODO: Review unreachable code - logger.info(f"Tracked workflow result: {len(preference_ids)} preferences, success={successful}")

    # TODO: Review unreachable code - def get_preferences_for_context(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - context: dict[str, Any],
    # TODO: Review unreachable code - preference_types: list[PreferenceType] | None = None,
    # TODO: Review unreachable code - limit: int = 5
    # TODO: Review unreachable code - ) -> dict[PreferenceType, list[StylePreference]]:
    # TODO: Review unreachable code - """Get relevant preferences for a given context.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - context: Current context (project, time, mood, etc.)
    # TODO: Review unreachable code - preference_types: Types to consider
    # TODO: Review unreachable code - limit: Max preferences per type

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Preferences organized by type
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - results = {}
    # TODO: Review unreachable code - types_to_check = preference_types or list(PreferenceType)

    # TODO: Review unreachable code - for pref_type in types_to_check:
    # TODO: Review unreachable code - candidates = []

    # TODO: Review unreachable code - # Get all preferences of this type
    # TODO: Review unreachable code - type_prefs = self.profile.preferences.get(pref_type, [])

    # TODO: Review unreachable code - for pref in type_prefs:
    # TODO: Review unreachable code - score = pref.preference_score

    # TODO: Review unreachable code - # Boost score based on context match
    # TODO: Review unreachable code - if context is not None and "project" in context and context["project"] in pref.project_associations:
    # TODO: Review unreachable code - score *= 1.5

    # TODO: Review unreachable code - if context is not None and "time_of_day" in context:
    # TODO: Review unreachable code - hour = context["time_of_day"]
    # TODO: Review unreachable code - if pref.preference_id in self.profile.time_of_day_preferences.get(hour, []):
    # TODO: Review unreachable code - score *= 1.3

    # TODO: Review unreachable code - if context is not None and "tags" in context:
    # TODO: Review unreachable code - tag_overlap = len(set(context["tags"]) & set(pref.tags))
    # TODO: Review unreachable code - score *= (1 + tag_overlap * 0.1)

    # TODO: Review unreachable code - candidates.append((pref, score))

    # TODO: Review unreachable code - # Sort by adjusted score
    # TODO: Review unreachable code - candidates.sort(key=lambda x: x[1], reverse=True)

    # TODO: Review unreachable code - # Take top candidates
    # TODO: Review unreachable code - results[pref_type] = [c[0] for c in candidates[:limit]]

    # TODO: Review unreachable code - return results

    # TODO: Review unreachable code - def suggest_combinations(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - base_preferences: list[str],
    # TODO: Review unreachable code - max_suggestions: int = 5
    # TODO: Review unreachable code - ) -> list[list[str]]:
    # TODO: Review unreachable code - """Suggest preference combinations based on history.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - base_preferences: Starting preferences
    # TODO: Review unreachable code - max_suggestions: Maximum suggestions to return

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of suggested combinations
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - suggestions = []
    # TODO: Review unreachable code - base_set = set(base_preferences)

    # TODO: Review unreachable code - # Check favorite combinations
    # TODO: Review unreachable code - for combo in self.profile.favorite_combinations:
    # TODO: Review unreachable code - combo_set = set(combo)

    # TODO: Review unreachable code - # If there's overlap, suggest the full combination
    # TODO: Review unreachable code - if base_set & combo_set and combo_set != base_set:
    # TODO: Review unreachable code - suggestions.append(list(combo_set))

    # TODO: Review unreachable code - # Check co-occurrence patterns
    # TODO: Review unreachable code - for base_pref in base_preferences:
    # TODO: Review unreachable code - if base_pref in self.patterns.get("co_occurrence", {}):
    # TODO: Review unreachable code - related = self.patterns["co_occurrence"][base_pref]

    # TODO: Review unreachable code - for related_pref, count in related.most_common(3):
    # TODO: Review unreachable code - if related_pref not in base_set:
    # TODO: Review unreachable code - suggestion = base_preferences + [related_pref]
    # TODO: Review unreachable code - if suggestion not in suggestions:
    # TODO: Review unreachable code - suggestions.append(suggestion)

    # TODO: Review unreachable code - # Sort by historical success
    # TODO: Review unreachable code - suggestions.sort(key=lambda s: self._score_combination(s), reverse=True)

    # TODO: Review unreachable code - return suggestions[:max_suggestions]

    # TODO: Review unreachable code - def get_style_evolution(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - time_range: timedelta | None = None,
    # TODO: Review unreachable code - preference_type: PreferenceType | None = None
    # TODO: Review unreachable code - ) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Get style evolution over time.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - time_range: Time range to analyze
    # TODO: Review unreachable code - preference_type: Specific type to track

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Evolution timeline
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - cutoff = datetime.now() - time_range if time_range else None

    # TODO: Review unreachable code - evolution = []

    # TODO: Review unreachable code - # Group preferences by time periods
    # TODO: Review unreachable code - time_buckets = defaultdict(list)

    # TODO: Review unreachable code - for pref in self.all_preferences.values():
    # TODO: Review unreachable code - if preference_type and pref.preference_type != preference_type:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - if cutoff and pref.first_seen < cutoff:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Bucket by week
    # TODO: Review unreachable code - week = pref.first_seen.isocalendar()[:2]
    # TODO: Review unreachable code - time_buckets[week].append(pref)

    # TODO: Review unreachable code - # Analyze each bucket
    # TODO: Review unreachable code - for week, prefs in sorted(time_buckets.items()):
    # TODO: Review unreachable code - week_data = {
    # TODO: Review unreachable code - "week": f"{week[0]}-W{week[1]}",
    # TODO: Review unreachable code - "new_preferences": len(prefs),
    # TODO: Review unreachable code - "top_values": [],
    # TODO: Review unreachable code - "average_score": 0.0
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Get top values
    # TODO: Review unreachable code - prefs.sort(key=lambda p: p.preference_score, reverse=True)
    # TODO: Review unreachable code - week_data["top_values"] = [
    # TODO: Review unreachable code - {"type": p.preference_type.value, "value": str(p.value)}
    # TODO: Review unreachable code - for p in prefs[:3]
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - # Calculate average score
    # TODO: Review unreachable code - if prefs:
    # TODO: Review unreachable code - week_data["average_score"] = sum(p.preference_score for p in prefs) / len(prefs)

    # TODO: Review unreachable code - evolution.append(week_data)

    # TODO: Review unreachable code - return evolution

    # TODO: Review unreachable code - def export_profile(self) -> dict[str, Any]:
    # TODO: Review unreachable code - """Export complete style profile.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Complete profile data
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "profile_id": self.profile.profile_id,
    # TODO: Review unreachable code - "created_at": self.profile.created_at.isoformat(),
    # TODO: Review unreachable code - "updated_at": self.profile.updated_at.isoformat(),
    # TODO: Review unreachable code - "preferences_by_type": {
    # TODO: Review unreachable code - pref_type.value: [
    # TODO: Review unreachable code - p.to_dict() for p in prefs
    # TODO: Review unreachable code - ]
    # TODO: Review unreachable code - for pref_type, prefs in self.profile.preferences.items()
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - "favorite_combinations": self.profile.favorite_combinations,
    # TODO: Review unreachable code - "avoided_combinations": self.profile.avoided_combinations,
    # TODO: Review unreachable code - "project_styles": self.profile.project_styles,
    # TODO: Review unreachable code - "statistics": {
    # TODO: Review unreachable code - "total_preferences": len(self.all_preferences),
    # TODO: Review unreachable code - "total_usage": sum(p.usage_count for p in self.all_preferences.values()),
    # TODO: Review unreachable code - "average_confidence": sum(p.confidence for p in self.all_preferences.values()) / len(self.all_preferences) if self.all_preferences else 0
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def import_profile(self, profile_data: dict[str, Any]):
    # TODO: Review unreachable code - """Import a style profile.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - profile_data: Profile data to import
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Create new profile
    # TODO: Review unreachable code - self.profile = StyleProfile(
    # TODO: Review unreachable code - profile_id=profile_data["profile_id"],
    # TODO: Review unreachable code - created_at=datetime.fromisoformat(profile_data["created_at"]),
    # TODO: Review unreachable code - updated_at=datetime.fromisoformat(profile_data["updated_at"])
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Import preferences
    # TODO: Review unreachable code - self.all_preferences.clear()

    # TODO: Review unreachable code - for pref_type_str, prefs_data in profile_data["preferences_by_type"].items():
    # TODO: Review unreachable code - PreferenceType(pref_type_str)

    # TODO: Review unreachable code - for pref_data in prefs_data:
    # TODO: Review unreachable code - pref = StylePreference.from_dict(pref_data)
    # TODO: Review unreachable code - self.all_preferences[pref.preference_id] = pref
    # TODO: Review unreachable code - self.profile.add_preference(pref)

    # TODO: Review unreachable code - # Import combinations
    # TODO: Review unreachable code - self.profile.favorite_combinations = profile_data.get("favorite_combinations", [])
    # TODO: Review unreachable code - self.profile.avoided_combinations = profile_data.get("avoided_combinations", [])
    # TODO: Review unreachable code - self.profile.project_styles = profile_data.get("project_styles", {})

    # TODO: Review unreachable code - # Save
    # TODO: Review unreachable code - self._save_all()

    # TODO: Review unreachable code - logger.info(f"Imported style profile with {len(self.all_preferences)} preferences")

    # TODO: Review unreachable code - def _update_patterns(self, preference_ids: list[str], successful: bool):
    # TODO: Review unreachable code - """Update co-occurrence and success patterns."""
    # TODO: Review unreachable code - if "co_occurrence" not in self.patterns:
    # TODO: Review unreachable code - self.patterns["co_occurrence"] = {}

    # TODO: Review unreachable code - if "success_patterns" not in self.patterns:
    # TODO: Review unreachable code - self.patterns["success_patterns"] = {}

    # TODO: Review unreachable code - # Update co-occurrence
    # TODO: Review unreachable code - for i, pref_id in enumerate(preference_ids):
    # TODO: Review unreachable code - if pref_id not in self.patterns["co_occurrence"]:
    # TODO: Review unreachable code - self.patterns["co_occurrence"][pref_id] = Counter()

    # TODO: Review unreachable code - for j, other_id in enumerate(preference_ids):
    # TODO: Review unreachable code - if i != j:
    # TODO: Review unreachable code - self.patterns["co_occurrence"][pref_id][other_id] += 1

    # TODO: Review unreachable code - # Update success patterns
    # TODO: Review unreachable code - combo_key = ",".join(sorted(preference_ids))
    # TODO: Review unreachable code - if combo_key not in self.patterns["success_patterns"]:
    # TODO: Review unreachable code - self.patterns["success_patterns"][combo_key] = {"success": 0, "total": 0}

    # TODO: Review unreachable code - self.patterns["success_patterns"][combo_key]["total"] += 1
    # TODO: Review unreachable code - if successful:
    # TODO: Review unreachable code - self.patterns["success_patterns"][combo_key]["success"] += 1

    # TODO: Review unreachable code - def _score_combination(self, preference_ids: list[str]) -> float:
    # TODO: Review unreachable code - """Score a preference combination based on history."""
    # TODO: Review unreachable code - combo_key = ",".join(sorted(preference_ids))

    # TODO: Review unreachable code - if combo_key in self.patterns.get("success_patterns", {}):
    # TODO: Review unreachable code - stats = self.patterns["success_patterns"][combo_key]
    # TODO: Review unreachable code - if stats is not None and stats["total"] > 0:
    # TODO: Review unreachable code - return stats["success"] / stats["total"]

    # TODO: Review unreachable code - # Default score based on individual preferences
    # TODO: Review unreachable code - scores = []
    # TODO: Review unreachable code - for pref_id in preference_ids:
    # TODO: Review unreachable code - if pref_id in self.all_preferences:
    # TODO: Review unreachable code - scores.append(self.all_preferences[pref_id].preference_score)

    # TODO: Review unreachable code - return sum(scores) / len(scores) if scores else 0.0

    # TODO: Review unreachable code - def _load_profile(self) -> StyleProfile:
    # TODO: Review unreachable code - """Load style profile from disk."""
    # TODO: Review unreachable code - if self.profile_file.exists():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(self.profile_file) as f:
    # TODO: Review unreachable code - data = json.load(f)

    # TODO: Review unreachable code - profile = StyleProfile(
    # TODO: Review unreachable code - profile_id=data["profile_id"],
    # TODO: Review unreachable code - created_at=datetime.fromisoformat(data["created_at"]),
    # TODO: Review unreachable code - updated_at=datetime.fromisoformat(data["updated_at"])
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Load other fields
    # TODO: Review unreachable code - profile.favorite_combinations = data.get("favorite_combinations", [])
    # TODO: Review unreachable code - profile.avoided_combinations = data.get("avoided_combinations", [])
    # TODO: Review unreachable code - profile.project_styles = data.get("project_styles", {})
    # TODO: Review unreachable code - profile.time_of_day_preferences = {
    # TODO: Review unreachable code - int(k): v for k, v in data.get("time_of_day_preferences", {}).items()
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - return profile

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to load profile: {e}")

    # TODO: Review unreachable code - # Create new profile with timestamp-based ID
    # TODO: Review unreachable code - from datetime import datetime
    # TODO: Review unreachable code - profile_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    # TODO: Review unreachable code - return StyleProfile(profile_id=profile_id)

    # TODO: Review unreachable code - def _load_preferences(self) -> dict[str, StylePreference]:
    # TODO: Review unreachable code - """Load preferences from disk."""
    # TODO: Review unreachable code - preferences = {}

    # TODO: Review unreachable code - if self.preferences_file.exists():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(self.preferences_file) as f:
    # TODO: Review unreachable code - data = json.load(f)

    # TODO: Review unreachable code - for pref_id, pref_data in data.items():
    # TODO: Review unreachable code - preferences[pref_id] = StylePreference.from_dict(pref_data)

    # TODO: Review unreachable code - # Add to profile
    # TODO: Review unreachable code - for pref in preferences.values():
    # TODO: Review unreachable code - self.profile.add_preference(pref)

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to load preferences: {e}")

    # TODO: Review unreachable code - return preferences

    # TODO: Review unreachable code - def _load_patterns(self) -> dict[str, Any]:
    # TODO: Review unreachable code - """Load patterns from disk."""
    # TODO: Review unreachable code - if self.patterns_file.exists():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(self.patterns_file) as f:
    # TODO: Review unreachable code - data = json.load(f)

    # TODO: Review unreachable code - # Convert Counter objects
    # TODO: Review unreachable code - if data is not None and "co_occurrence" in data:
    # TODO: Review unreachable code - for pref_id, counts in data["co_occurrence"].items():
    # TODO: Review unreachable code - data["co_occurrence"][pref_id] = Counter(counts)

    # TODO: Review unreachable code - return data

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to load patterns: {e}")

    # TODO: Review unreachable code - return {}

    # TODO: Review unreachable code - def _save_all(self):
    # TODO: Review unreachable code - """Save all data to disk."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Save profile
    # TODO: Review unreachable code - profile_data = {
    # TODO: Review unreachable code - "profile_id": self.profile.profile_id,
    # TODO: Review unreachable code - "created_at": self.profile.created_at.isoformat(),
    # TODO: Review unreachable code - "updated_at": self.profile.updated_at.isoformat(),
    # TODO: Review unreachable code - "favorite_combinations": self.profile.favorite_combinations,
    # TODO: Review unreachable code - "avoided_combinations": self.profile.avoided_combinations,
    # TODO: Review unreachable code - "project_styles": self.profile.project_styles,
    # TODO: Review unreachable code - "time_of_day_preferences": self.profile.time_of_day_preferences
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - with open(self.profile_file, 'w') as f:
    # TODO: Review unreachable code - json.dump(profile_data, f, indent=2)

    # TODO: Review unreachable code - # Save preferences
    # TODO: Review unreachable code - prefs_data = {
    # TODO: Review unreachable code - pref_id: pref.to_dict()
    # TODO: Review unreachable code - for pref_id, pref in self.all_preferences.items()
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - with open(self.preferences_file, 'w') as f:
    # TODO: Review unreachable code - json.dump(prefs_data, f, indent=2)

    # TODO: Review unreachable code - # Save patterns (convert Counters to dicts)
    # TODO: Review unreachable code - patterns_data = self.patterns.copy()
    # TODO: Review unreachable code - if patterns_data is not None and "co_occurrence" in patterns_data:
    # TODO: Review unreachable code - patterns_data["co_occurrence"] = {
    # TODO: Review unreachable code - pref_id: dict(counter)
    # TODO: Review unreachable code - for pref_id, counter in patterns_data["co_occurrence"].items()
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - with open(self.patterns_file, 'w') as f:
    # TODO: Review unreachable code - json.dump(patterns_data, f, indent=2)

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to save style memory: {e}")
