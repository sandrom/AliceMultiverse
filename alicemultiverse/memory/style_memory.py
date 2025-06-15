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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'StylePreference':
        """Create from dictionary."""
        data = data.copy()
        data['preference_type'] = PreferenceType(data['preference_type'])
        data['first_seen'] = datetime.fromisoformat(data['first_seen'])
        data['last_used'] = datetime.fromisoformat(data['last_used'])
        return cls(**data)


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

        self.preferences[pref_type].append(preference)
        self.updated_at = datetime.now()

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

    def track_combination(self, preference_ids: list[str], successful: bool = True):
        """Track preference combinations."""
        combo = sorted(preference_ids)

        if successful:
            # Add to favorites if used multiple times
            combo_str = ",".join(combo)
            found = False

            for fav in self.favorite_combinations:
                if ",".join(sorted(fav)) == combo_str:
                    found = True
                    break

            if not found and len(combo) > 1:
                self.favorite_combinations.append(combo)
        else:
            # Add to avoided if failed
            if combo not in self.avoided_combinations:
                self.avoided_combinations.append(combo)

        self.updated_at = datetime.now()


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

    def track_workflow_result(
        self,
        preference_ids: list[str],
        successful: bool,
        quality_score: float | None = None,
        user_rating: int | None = None
    ):
        """Track the result of using certain preferences.
        
        Args:
            preference_ids: Preferences used
            successful: Whether the result was successful
            quality_score: Objective quality score (0-1)
            user_rating: User rating (1-5)
        """
        # Update individual preferences
        for pref_id in preference_ids:
            if pref_id in self.all_preferences:
                pref = self.all_preferences[pref_id]
                pref.update_usage(successful=successful)

                # Adjust score based on quality and rating
                if quality_score is not None:
                    adjustment = (quality_score - 0.5) * 0.1
                    pref.preference_score = max(0, min(1, pref.preference_score + adjustment))

                if user_rating is not None:
                    adjustment = (user_rating - 3) * 0.05
                    pref.preference_score = max(0, min(1, pref.preference_score + adjustment))

        # Track combinations
        if len(preference_ids) > 1:
            self.profile.track_combination(preference_ids, successful)

        # Update patterns
        self._update_patterns(preference_ids, successful)

        logger.info(f"Tracked workflow result: {len(preference_ids)} preferences, success={successful}")

    def get_preferences_for_context(
        self,
        context: dict[str, Any],
        preference_types: list[PreferenceType] | None = None,
        limit: int = 5
    ) -> dict[PreferenceType, list[StylePreference]]:
        """Get relevant preferences for a given context.
        
        Args:
            context: Current context (project, time, mood, etc.)
            preference_types: Types to consider
            limit: Max preferences per type
            
        Returns:
            Preferences organized by type
        """
        results = {}
        types_to_check = preference_types or list(PreferenceType)

        for pref_type in types_to_check:
            candidates = []

            # Get all preferences of this type
            type_prefs = self.profile.preferences.get(pref_type, [])

            for pref in type_prefs:
                score = pref.preference_score

                # Boost score based on context match
                if "project" in context and context["project"] in pref.project_associations:
                    score *= 1.5

                if "time_of_day" in context:
                    hour = context["time_of_day"]
                    if pref.preference_id in self.profile.time_of_day_preferences.get(hour, []):
                        score *= 1.3

                if "tags" in context:
                    tag_overlap = len(set(context["tags"]) & set(pref.tags))
                    score *= (1 + tag_overlap * 0.1)

                candidates.append((pref, score))

            # Sort by adjusted score
            candidates.sort(key=lambda x: x[1], reverse=True)

            # Take top candidates
            results[pref_type] = [c[0] for c in candidates[:limit]]

        return results

    def suggest_combinations(
        self,
        base_preferences: list[str],
        max_suggestions: int = 5
    ) -> list[list[str]]:
        """Suggest preference combinations based on history.
        
        Args:
            base_preferences: Starting preferences
            max_suggestions: Maximum suggestions to return
            
        Returns:
            List of suggested combinations
        """
        suggestions = []
        base_set = set(base_preferences)

        # Check favorite combinations
        for combo in self.profile.favorite_combinations:
            combo_set = set(combo)

            # If there's overlap, suggest the full combination
            if base_set & combo_set and combo_set != base_set:
                suggestions.append(list(combo_set))

        # Check co-occurrence patterns
        for base_pref in base_preferences:
            if base_pref in self.patterns.get("co_occurrence", {}):
                related = self.patterns["co_occurrence"][base_pref]

                for related_pref, count in related.most_common(3):
                    if related_pref not in base_set:
                        suggestion = base_preferences + [related_pref]
                        if suggestion not in suggestions:
                            suggestions.append(suggestion)

        # Sort by historical success
        suggestions.sort(key=lambda s: self._score_combination(s), reverse=True)

        return suggestions[:max_suggestions]

    def get_style_evolution(
        self,
        time_range: timedelta | None = None,
        preference_type: PreferenceType | None = None
    ) -> list[dict[str, Any]]:
        """Get style evolution over time.
        
        Args:
            time_range: Time range to analyze
            preference_type: Specific type to track
            
        Returns:
            Evolution timeline
        """
        cutoff = datetime.now() - time_range if time_range else None

        evolution = []

        # Group preferences by time periods
        time_buckets = defaultdict(list)

        for pref in self.all_preferences.values():
            if preference_type and pref.preference_type != preference_type:
                continue

            if cutoff and pref.first_seen < cutoff:
                continue

            # Bucket by week
            week = pref.first_seen.isocalendar()[:2]
            time_buckets[week].append(pref)

        # Analyze each bucket
        for week, prefs in sorted(time_buckets.items()):
            week_data = {
                "week": f"{week[0]}-W{week[1]}",
                "new_preferences": len(prefs),
                "top_values": [],
                "average_score": 0.0
            }

            # Get top values
            prefs.sort(key=lambda p: p.preference_score, reverse=True)
            week_data["top_values"] = [
                {"type": p.preference_type.value, "value": str(p.value)}
                for p in prefs[:3]
            ]

            # Calculate average score
            if prefs:
                week_data["average_score"] = sum(p.preference_score for p in prefs) / len(prefs)

            evolution.append(week_data)

        return evolution

    def export_profile(self) -> dict[str, Any]:
        """Export complete style profile.
        
        Returns:
            Complete profile data
        """
        return {
            "profile_id": self.profile.profile_id,
            "created_at": self.profile.created_at.isoformat(),
            "updated_at": self.profile.updated_at.isoformat(),
            "preferences_by_type": {
                pref_type.value: [
                    p.to_dict() for p in prefs
                ]
                for pref_type, prefs in self.profile.preferences.items()
            },
            "favorite_combinations": self.profile.favorite_combinations,
            "avoided_combinations": self.profile.avoided_combinations,
            "project_styles": self.profile.project_styles,
            "statistics": {
                "total_preferences": len(self.all_preferences),
                "total_usage": sum(p.usage_count for p in self.all_preferences.values()),
                "average_confidence": sum(p.confidence for p in self.all_preferences.values()) / len(self.all_preferences) if self.all_preferences else 0
            }
        }

    def import_profile(self, profile_data: dict[str, Any]):
        """Import a style profile.
        
        Args:
            profile_data: Profile data to import
        """
        # Create new profile
        self.profile = StyleProfile(
            profile_id=profile_data["profile_id"],
            created_at=datetime.fromisoformat(profile_data["created_at"]),
            updated_at=datetime.fromisoformat(profile_data["updated_at"])
        )

        # Import preferences
        self.all_preferences.clear()

        for pref_type_str, prefs_data in profile_data["preferences_by_type"].items():
            PreferenceType(pref_type_str)

            for pref_data in prefs_data:
                pref = StylePreference.from_dict(pref_data)
                self.all_preferences[pref.preference_id] = pref
                self.profile.add_preference(pref)

        # Import combinations
        self.profile.favorite_combinations = profile_data.get("favorite_combinations", [])
        self.profile.avoided_combinations = profile_data.get("avoided_combinations", [])
        self.profile.project_styles = profile_data.get("project_styles", {})

        # Save
        self._save_all()

        logger.info(f"Imported style profile with {len(self.all_preferences)} preferences")

    def _update_patterns(self, preference_ids: list[str], successful: bool):
        """Update co-occurrence and success patterns."""
        if "co_occurrence" not in self.patterns:
            self.patterns["co_occurrence"] = {}

        if "success_patterns" not in self.patterns:
            self.patterns["success_patterns"] = {}

        # Update co-occurrence
        for i, pref_id in enumerate(preference_ids):
            if pref_id not in self.patterns["co_occurrence"]:
                self.patterns["co_occurrence"][pref_id] = Counter()

            for j, other_id in enumerate(preference_ids):
                if i != j:
                    self.patterns["co_occurrence"][pref_id][other_id] += 1

        # Update success patterns
        combo_key = ",".join(sorted(preference_ids))
        if combo_key not in self.patterns["success_patterns"]:
            self.patterns["success_patterns"][combo_key] = {"success": 0, "total": 0}

        self.patterns["success_patterns"][combo_key]["total"] += 1
        if successful:
            self.patterns["success_patterns"][combo_key]["success"] += 1

    def _score_combination(self, preference_ids: list[str]) -> float:
        """Score a preference combination based on history."""
        combo_key = ",".join(sorted(preference_ids))

        if combo_key in self.patterns.get("success_patterns", {}):
            stats = self.patterns["success_patterns"][combo_key]
            if stats["total"] > 0:
                return stats["success"] / stats["total"]

        # Default score based on individual preferences
        scores = []
        for pref_id in preference_ids:
            if pref_id in self.all_preferences:
                scores.append(self.all_preferences[pref_id].preference_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _load_profile(self) -> StyleProfile:
        """Load style profile from disk."""
        if self.profile_file.exists():
            try:
                with open(self.profile_file) as f:
                    data = json.load(f)

                profile = StyleProfile(
                    profile_id=data["profile_id"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"])
                )

                # Load other fields
                profile.favorite_combinations = data.get("favorite_combinations", [])
                profile.avoided_combinations = data.get("avoided_combinations", [])
                profile.project_styles = data.get("project_styles", {})
                profile.time_of_day_preferences = {
                    int(k): v for k, v in data.get("time_of_day_preferences", {}).items()
                }

                return profile

            except Exception as e:
                logger.error(f"Failed to load profile: {e}")

        # Create new profile with timestamp-based ID
        from datetime import datetime
        profile_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return StyleProfile(profile_id=profile_id)

    def _load_preferences(self) -> dict[str, StylePreference]:
        """Load preferences from disk."""
        preferences = {}

        if self.preferences_file.exists():
            try:
                with open(self.preferences_file) as f:
                    data = json.load(f)

                for pref_id, pref_data in data.items():
                    preferences[pref_id] = StylePreference.from_dict(pref_data)

                # Add to profile
                for pref in preferences.values():
                    self.profile.add_preference(pref)

            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")

        return preferences

    def _load_patterns(self) -> dict[str, Any]:
        """Load patterns from disk."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file) as f:
                    data = json.load(f)

                # Convert Counter objects
                if "co_occurrence" in data:
                    for pref_id, counts in data["co_occurrence"].items():
                        data["co_occurrence"][pref_id] = Counter(counts)

                return data

            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")

        return {}

    def _save_all(self):
        """Save all data to disk."""
        try:
            # Save profile
            profile_data = {
                "profile_id": self.profile.profile_id,
                "created_at": self.profile.created_at.isoformat(),
                "updated_at": self.profile.updated_at.isoformat(),
                "favorite_combinations": self.profile.favorite_combinations,
                "avoided_combinations": self.profile.avoided_combinations,
                "project_styles": self.profile.project_styles,
                "time_of_day_preferences": self.profile.time_of_day_preferences
            }

            with open(self.profile_file, 'w') as f:
                json.dump(profile_data, f, indent=2)

            # Save preferences
            prefs_data = {
                pref_id: pref.to_dict()
                for pref_id, pref in self.all_preferences.items()
            }

            with open(self.preferences_file, 'w') as f:
                json.dump(prefs_data, f, indent=2)

            # Save patterns (convert Counters to dicts)
            patterns_data = self.patterns.copy()
            if "co_occurrence" in patterns_data:
                patterns_data["co_occurrence"] = {
                    pref_id: dict(counter)
                    for pref_id, counter in patterns_data["co_occurrence"].items()
                }

            with open(self.patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save style memory: {e}")
