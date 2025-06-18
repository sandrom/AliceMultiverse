"""MCP tools for style memory and learning system."""

from datetime import datetime, timedelta
from typing import Any

from ..core.structured_logging import get_logger
from .learning_engine import StyleLearningEngine
from .preference_tracker import PreferenceTracker, WorkflowType
from .recommendation_engine import StyleRecommendationEngine
from .style_memory import PreferenceType, StyleMemory

logger = get_logger(__name__)

# Global instances
_style_memory: StyleMemory | None = None
_preference_tracker: PreferenceTracker | None = None
_learning_engine: StyleLearningEngine | None = None
_recommendation_engine: StyleRecommendationEngine | None = None


def _get_style_memory() -> StyleMemory:
    """Get or create style memory instance."""
    global _style_memory
    if _style_memory is None:
        _style_memory = StyleMemory()
    return _style_memory


def _get_preference_tracker() -> PreferenceTracker:
    """Get or create preference tracker instance."""
    global _preference_tracker
    if _preference_tracker is None:
        _preference_tracker = PreferenceTracker(_get_style_memory())
    return _preference_tracker


def _get_learning_engine() -> StyleLearningEngine:
    """Get or create learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = StyleLearningEngine(
            _get_style_memory(),
            _get_preference_tracker()
        )
    return _learning_engine


def _get_recommendation_engine() -> StyleRecommendationEngine:
    """Get or create recommendation engine instance."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = StyleRecommendationEngine(
            _get_style_memory(),
            _get_learning_engine()
        )
    return _recommendation_engine


async def track_style_preference(
    preference_type: str,
    value: str,
    project: str | None = None,
    tags: list[str] | None = None,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Track a style preference choice.

    Args:
        preference_type: Type of preference (color_palette, composition, etc.)
        value: The chosen value
        project: Optional project context
        tags: Optional descriptive tags
        context: Optional additional context

    Returns:
        Tracked preference details
    """
    try:
        # Map string to enum
        pref_type = PreferenceType(preference_type.lower())

        # Track the preference
        style_memory = _get_style_memory()
        preference = style_memory.track_style_choice(
            preference_type=pref_type,
            value=value,
            context=context,
            project=project,
            tags=tags
        )

        return {
            "preference_id": preference.preference_id,
            "type": preference.preference_type.value,
            "value": preference.value,
            "usage_count": preference.usage_count,
            "preference_score": preference.preference_score,
            "confidence": preference.confidence,
            "tags": preference.tags
        }

    except Exception as e:
        logger.error(f"Failed to track preference: {e}")
        raise


async def get_style_recommendations(
    context: dict[str, Any] | None = None,
    types: list[str] | None = None,
    limit: int = 5
) -> list[dict[str, Any]]:
    """Get personalized style recommendations.

    Args:
        context: Optional context (project, time, etc.)
        types: Recommendation types (preset, variation, exploration, trending)
        limit: Maximum recommendations

    Returns:
        List of recommendations
    """
    try:
        engine = _get_recommendation_engine()
        recommendations = engine.get_recommendations(
            context=context,
            recommendation_types=types,
            limit=limit
        )

        return [
            {
                "id": rec.recommendation_id,
                "type": rec.recommendation_type,
                "title": rec.title,
                "description": rec.description,
                "preferences": {
                    k.value: v for k, v in rec.preferences.items()
                },
                "confidence": rec.confidence,
                "relevance_score": rec.relevance_score,
                "novelty_score": rec.novelty_score,
                "reasoning": rec.reasoning,
                "tags": rec.tags
            }
            for rec in recommendations
        ]

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise


async def analyze_style_patterns(
    time_range_days: int | None = 30
) -> dict[str, Any]:
    """Analyze style patterns and generate insights.

    Args:
        time_range_days: Days to analyze

    Returns:
        Pattern analysis and insights
    """
    try:
        engine = _get_learning_engine()

        # Update time window
        if time_range_days:
            engine.learning_window = timedelta(days=time_range_days)

        # Analyze patterns
        patterns = engine.analyze_patterns()

        # Generate insights
        insights = engine.generate_insights()

        return {
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type,
                    "preferences": p.preferences,
                    "frequency": p.frequency,
                    "success_rate": p.success_rate,
                    "confidence": p.confidence,
                    "projects": p.projects
                }
                for p in patterns
            ],
            "insights": [
                {
                    "type": i.insight_type,
                    "title": i.title,
                    "description": i.description,
                    "priority": i.priority,
                    "recommendations": i.recommendations,
                    "confidence": i.confidence
                }
                for i in insights
            ],
            "summary": {
                "total_patterns": len(patterns),
                "high_priority_insights": sum(
                    1 for i in insights if i.priority == "high"
                ),
                "time_range_days": time_range_days or 30
            }
        }

    except Exception as e:
        logger.error(f"Failed to analyze patterns: {e}")
        raise


async def start_style_workflow(
    workflow_type: str,
    project: str | None = None
) -> dict[str, Any]:
    """Start tracking a style workflow.

    Args:
        workflow_type: Type of workflow
        project: Optional project context

    Returns:
        Workflow tracking details
    """
    try:
        # Map string to enum
        wf_type = WorkflowType(workflow_type.lower())

        # Generate workflow ID
        workflow_id = f"{workflow_type}_{datetime.now().timestamp()}"

        # Start tracking
        tracker = _get_preference_tracker()
        context = tracker.start_workflow(workflow_id, wf_type, project)

        return {
            "workflow_id": context.workflow_id,
            "type": context.workflow_type.value,
            "project": context.project,
            "started_at": context.started_at.isoformat(),
            "status": "active"
        }

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise


async def end_style_workflow(
    workflow_id: str,
    successful: bool,
    quality_score: float | None = None,
    user_rating: int | None = None,
    notes: str | None = None
) -> dict[str, Any]:
    """End a style workflow and get summary.

    Args:
        workflow_id: Workflow to end
        successful: Whether workflow was successful
        quality_score: Optional quality score (0-1)
        user_rating: Optional user rating (1-5)
        notes: Optional notes

    Returns:
        Workflow summary
    """
    try:
        tracker = _get_preference_tracker()
        context = tracker.end_workflow(
            workflow_id,
            successful,
            quality_score,
            user_rating,
            notes
        )

        if not context:
            return {"error": "Workflow not found"}

        return tracker.get_workflow_summary(workflow_id)

    except Exception as e:
        logger.error(f"Failed to end workflow: {e}")
        raise


async def get_style_evolution(
    days: int = 30,
    preference_type: str | None = None
) -> list[dict[str, Any]]:
    """Get style evolution over time.

    Args:
        days: Number of days to analyze
        preference_type: Optional specific type

    Returns:
        Evolution timeline
    """
    try:
        style_memory = _get_style_memory()

        # Map string to enum if provided
        pref_type = None
        if preference_type:
            pref_type = PreferenceType(preference_type.lower())

        evolution = style_memory.get_style_evolution(
            time_range=timedelta(days=days),
            preference_type=pref_type
        )

        return evolution

    except Exception as e:
        logger.error(f"Failed to get evolution: {e}")
        raise


async def suggest_next_action(
    current_preferences: dict[str, str]
) -> dict[str, Any]:
    """Get next best action suggestion.

    Args:
        current_preferences: Current preference selections

    Returns:
        Action recommendation
    """
    try:
        # Convert to enum-based dict
        current_state = {
            "preferences": {
                PreferenceType(k.lower()): v
                for k, v in current_preferences.items()
            }
        }

        engine = _get_recommendation_engine()
        suggestion = engine.get_next_best_action(current_state)

        return suggestion

    except Exception as e:
        logger.error(f"Failed to get next action: {e}")
        raise


async def export_style_profile() -> dict[str, Any]:
    """Export complete style profile.

    Returns:
        Complete profile data
    """
    try:
        style_memory = _get_style_memory()
        return style_memory.export_profile()

    except Exception as e:
        logger.error(f"Failed to export profile: {e}")
        raise


async def import_style_profile(
    profile_data: dict[str, Any]
) -> dict[str, Any]:
    """Import a style profile.

    Args:
        profile_data: Profile data to import

    Returns:
        Import status
    """
    try:
        style_memory = _get_style_memory()
        style_memory.import_profile(profile_data)

        return {
            "status": "success",
            "preferences_imported": len(style_memory.all_preferences),
            "profile_id": style_memory.profile.profile_id
        }

    except Exception as e:
        logger.error(f"Failed to import profile: {e}")
        raise


# Tool definitions for MCP registration
STYLE_MEMORY_TOOLS = [
    {
        "name": "track_style_preference",
        "description": "Track a style preference choice",
        "input_schema": {
            "type": "object",
            "properties": {
                "preference_type": {
                    "type": "string",
                    "description": "Type: color_palette, composition, lighting, texture, mood, subject, technique, transition, pacing, effect",
                    "enum": ["color_palette", "composition", "lighting", "texture", "mood", "subject", "technique", "transition", "pacing", "effect"]
                },
                "value": {
                    "type": "string",
                    "description": "The chosen value"
                },
                "project": {
                    "type": "string",
                    "description": "Optional project context"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional descriptive tags"
                },
                "context": {
                    "type": "object",
                    "description": "Optional additional context"
                }
            },
            "required": ["preference_type", "value"]
        }
    },
    {
        "name": "get_style_recommendations",
        "description": "Get personalized style recommendations",
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {
                    "type": "object",
                    "description": "Optional context (project, time, etc.)"
                },
                "types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recommendation types: preset, variation, exploration, trending"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum recommendations",
                    "default": 5
                }
            }
        }
    },
    {
        "name": "analyze_style_patterns",
        "description": "Analyze style patterns and generate insights",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_range_days": {
                    "type": "integer",
                    "description": "Days to analyze",
                    "default": 30
                }
            }
        }
    },
    {
        "name": "start_style_workflow",
        "description": "Start tracking a style workflow",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_type": {
                    "type": "string",
                    "description": "Type: image_generation, video_creation, timeline_editing, export, organization, search",
                    "enum": ["image_generation", "video_creation", "timeline_editing", "export", "organization", "search"]
                },
                "project": {
                    "type": "string",
                    "description": "Optional project context"
                }
            },
            "required": ["workflow_type"]
        }
    },
    {
        "name": "end_style_workflow",
        "description": "End a style workflow and get summary",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow to end"
                },
                "successful": {
                    "type": "boolean",
                    "description": "Whether workflow was successful"
                },
                "quality_score": {
                    "type": "number",
                    "description": "Optional quality score (0-1)"
                },
                "user_rating": {
                    "type": "integer",
                    "description": "Optional user rating (1-5)"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes"
                }
            },
            "required": ["workflow_id", "successful"]
        }
    },
    {
        "name": "get_style_evolution",
        "description": "Get style evolution over time",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze",
                    "default": 30
                },
                "preference_type": {
                    "type": "string",
                    "description": "Optional specific type to track"
                }
            }
        }
    },
    {
        "name": "suggest_next_action",
        "description": "Get next best action suggestion based on current preferences",
        "input_schema": {
            "type": "object",
            "properties": {
                "current_preferences": {
                    "type": "object",
                    "description": "Current preference selections (type->value mapping)"
                }
            },
            "required": ["current_preferences"]
        }
    },
    {
        "name": "export_style_profile",
        "description": "Export complete style profile",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "import_style_profile",
        "description": "Import a style profile",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_data": {
                    "type": "object",
                    "description": "Profile data to import"
                }
            },
            "required": ["profile_data"]
        }
    }
]
