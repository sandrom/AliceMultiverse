"""Real-time preference tracking during workflows."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..core.structured_logging import get_logger
from .style_memory import PreferenceType, StyleMemory

logger = get_logger(__name__)


class WorkflowType(Enum):
    """Types of workflows that can be tracked."""
    IMAGE_GENERATION = "image_generation"
    VIDEO_CREATION = "video_creation"
    TIMELINE_EDITING = "timeline_editing"
    EXPORT = "export"
    ORGANIZATION = "organization"
    SEARCH = "search"


@dataclass
class WorkflowContext:
    """Context for a workflow being tracked."""
    workflow_id: str
    workflow_type: WorkflowType
    project: str | None = None
    started_at: datetime = field(default_factory=datetime.now)

    # Tracking data
    choices: list[dict[str, Any]] = field(default_factory=list)
    outcomes: list[dict[str, Any]] = field(default_factory=list)
    duration: float | None = None
    successful: bool | None = None

    # User feedback
    quality_score: float | None = None
    user_rating: int | None = None
    notes: str | None = None


class PreferenceTracker:
    """Tracks preferences during workflows in real-time."""

    def __init__(self, style_memory: StyleMemory):
        """Initialize tracker with style memory.

        Args:
            style_memory: StyleMemory instance for persistence
        """
        self.style_memory = style_memory
        self.active_workflows: dict[str, WorkflowContext] = {}
        self.completed_workflows: list[WorkflowContext] = []

    def start_workflow(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        project: str | None = None
    ) -> WorkflowContext:
        """Start tracking a new workflow.

        Args:
            workflow_id: Unique workflow identifier
            workflow_type: Type of workflow
            project: Associated project name

        Returns:
            WorkflowContext for tracking
        """
        context = WorkflowContext(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            project=project
        )

        self.active_workflows[workflow_id] = context
        logger.info(f"Started tracking workflow {workflow_id} ({workflow_type.value})")

        return context

    # TODO: Review unreachable code - def track_choice(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - workflow_id: str,
    # TODO: Review unreachable code - choice_type: str,
    # TODO: Review unreachable code - value: Any,
    # TODO: Review unreachable code - metadata: dict[str, Any] | None = None
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - """Track a choice made during workflow.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - workflow_id: Workflow being tracked
    # TODO: Review unreachable code - choice_type: Type of choice (e.g., "color_palette", "transition")
    # TODO: Review unreachable code - value: The chosen value
    # TODO: Review unreachable code - metadata: Additional context
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if workflow_id not in self.active_workflows:
    # TODO: Review unreachable code - logger.warning(f"Workflow {workflow_id} not active")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - context = self.active_workflows[workflow_id]

    # TODO: Review unreachable code - choice = {
    # TODO: Review unreachable code - "timestamp": datetime.now(),
    # TODO: Review unreachable code - "type": choice_type,
    # TODO: Review unreachable code - "value": value,
    # TODO: Review unreachable code - "metadata": metadata or {}
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - context.choices.append(choice)

    # TODO: Review unreachable code - # Map to preference type if possible
    # TODO: Review unreachable code - pref_type = self._map_to_preference_type(choice_type)
    # TODO: Review unreachable code - if pref_type:
    # TODO: Review unreachable code - self.style_memory.track_style_choice(
    # TODO: Review unreachable code - preference_type=pref_type,
    # TODO: Review unreachable code - value=value,
    # TODO: Review unreachable code - context=metadata,
    # TODO: Review unreachable code - project=context.project
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def track_outcome(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - workflow_id: str,
    # TODO: Review unreachable code - outcome_type: str,
    # TODO: Review unreachable code - successful: bool,
    # TODO: Review unreachable code - details: dict[str, Any] | None = None
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - """Track an outcome during workflow.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - workflow_id: Workflow being tracked
    # TODO: Review unreachable code - outcome_type: Type of outcome
    # TODO: Review unreachable code - successful: Whether outcome was successful
    # TODO: Review unreachable code - details: Additional details
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if workflow_id not in self.active_workflows:
    # TODO: Review unreachable code - logger.warning(f"Workflow {workflow_id} not active")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - context = self.active_workflows[workflow_id]

    # TODO: Review unreachable code - outcome = {
    # TODO: Review unreachable code - "timestamp": datetime.now(),
    # TODO: Review unreachable code - "type": outcome_type,
    # TODO: Review unreachable code - "successful": successful,
    # TODO: Review unreachable code - "details": details or {}
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - context.outcomes.append(outcome)

    # TODO: Review unreachable code - def track_adjustment(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - workflow_id: str,
    # TODO: Review unreachable code - original_value: Any,
    # TODO: Review unreachable code - adjusted_value: Any,
    # TODO: Review unreachable code - reason: str | None = None
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - """Track manual adjustments to generated content.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - workflow_id: Workflow being tracked
    # TODO: Review unreachable code - original_value: Original/generated value
    # TODO: Review unreachable code - adjusted_value: User's adjusted value
    # TODO: Review unreachable code - reason: Optional reason for adjustment
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if workflow_id not in self.active_workflows:
    # TODO: Review unreachable code - logger.warning(f"Workflow {workflow_id} not active")
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - # Track as both a choice and outcome
    # TODO: Review unreachable code - self.track_choice(
    # TODO: Review unreachable code - workflow_id,
    # TODO: Review unreachable code - "manual_adjustment",
    # TODO: Review unreachable code - adjusted_value,
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "original": original_value,
    # TODO: Review unreachable code - "reason": reason
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - self.track_outcome(
    # TODO: Review unreachable code - workflow_id,
    # TODO: Review unreachable code - "adjustment_needed",
    # TODO: Review unreachable code - False,  # Original wasn't satisfactory
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "original": original_value,
    # TODO: Review unreachable code - "adjusted": adjusted_value
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def track_iteration(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - workflow_id: str,
    # TODO: Review unreachable code - iteration_number: int,
    # TODO: Review unreachable code - changes: list[str],
    # TODO: Review unreachable code - improved: bool = True
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - """Track iterations and refinements.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - workflow_id: Workflow being tracked
    # TODO: Review unreachable code - iteration_number: Which iteration this is
    # TODO: Review unreachable code - changes: List of changes made
    # TODO: Review unreachable code - improved: Whether this iteration was an improvement
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - self.track_outcome(
    # TODO: Review unreachable code - workflow_id,
    # TODO: Review unreachable code - "iteration",
    # TODO: Review unreachable code - improved,
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "number": iteration_number,
    # TODO: Review unreachable code - "changes": changes
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def end_workflow(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - workflow_id: str,
    # TODO: Review unreachable code - successful: bool,
    # TODO: Review unreachable code - quality_score: float | None = None,
    # TODO: Review unreachable code - user_rating: int | None = None,
    # TODO: Review unreachable code - notes: str | None = None
    # TODO: Review unreachable code - ) -> WorkflowContext | None:
    # TODO: Review unreachable code - """End workflow tracking and analyze results.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - workflow_id: Workflow to end
    # TODO: Review unreachable code - successful: Whether workflow was successful
    # TODO: Review unreachable code - quality_score: Objective quality (0-1)
    # TODO: Review unreachable code - user_rating: User satisfaction (1-5)
    # TODO: Review unreachable code - notes: Optional notes

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Completed workflow context
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if workflow_id not in self.active_workflows:
    # TODO: Review unreachable code - logger.warning(f"Workflow {workflow_id} not active")
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - context = self.active_workflows.pop(workflow_id)

    # TODO: Review unreachable code - # Calculate duration
    # TODO: Review unreachable code - context.duration = (datetime.now() - context.started_at).total_seconds()
    # TODO: Review unreachable code - context.successful = successful
    # TODO: Review unreachable code - context.quality_score = quality_score
    # TODO: Review unreachable code - context.user_rating = user_rating
    # TODO: Review unreachable code - context.notes = notes

    # TODO: Review unreachable code - # Store in completed list
    # TODO: Review unreachable code - self.completed_workflows.append(context)

    # TODO: Review unreachable code - # Update style memory with results
    # TODO: Review unreachable code - self._update_style_memory(context)

    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Ended workflow {workflow_id}: "
    # TODO: Review unreachable code - f"success={successful}, duration={context.duration:.1f}s"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return context

    # TODO: Review unreachable code - def get_workflow_summary(self, workflow_id: str) -> dict[str, Any] | None:
    # TODO: Review unreachable code - """Get summary of a workflow (active or completed).

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - workflow_id: Workflow to summarize

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Summary dictionary or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Check active workflows
    # TODO: Review unreachable code - if workflow_id in self.active_workflows:
    # TODO: Review unreachable code - context = self.active_workflows[workflow_id]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Check completed workflows
    # TODO: Review unreachable code - context = next(
    # TODO: Review unreachable code - (w for w in self.completed_workflows if w.workflow_id == workflow_id),
    # TODO: Review unreachable code - None
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if not context:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "workflow_id": context.workflow_id,
    # TODO: Review unreachable code - "workflow_type": context.workflow_type.value,
    # TODO: Review unreachable code - "project": context.project,
    # TODO: Review unreachable code - "started_at": context.started_at.isoformat(),
    # TODO: Review unreachable code - "duration": context.duration,
    # TODO: Review unreachable code - "successful": context.successful,
    # TODO: Review unreachable code - "choices_made": len(context.choices),
    # TODO: Review unreachable code - "outcomes_tracked": len(context.outcomes),
    # TODO: Review unreachable code - "quality_score": context.quality_score,
    # TODO: Review unreachable code - "user_rating": context.user_rating,
    # TODO: Review unreachable code - "notes": context.notes
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def get_active_workflows(self) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Get all active workflows.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of workflow summaries
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - return [
    # TODO: Review unreachable code - self.get_workflow_summary(wid)
    # TODO: Review unreachable code - for wid in self.active_workflows
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - def analyze_workflow_patterns(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - workflow_type: WorkflowType | None = None,
    # TODO: Review unreachable code - limit: int = 100
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Analyze patterns across completed workflows.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - workflow_type: Filter by type
    # TODO: Review unreachable code - limit: Max workflows to analyze

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Pattern analysis
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Filter workflows
    # TODO: Review unreachable code - workflows = self.completed_workflows
    # TODO: Review unreachable code - if workflow_type:
    # TODO: Review unreachable code - workflows = [
    # TODO: Review unreachable code - w for w in workflows
    # TODO: Review unreachable code - if w.workflow_type == workflow_type
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - # Take most recent
    # TODO: Review unreachable code - workflows = workflows[-limit:]

    # TODO: Review unreachable code - if not workflows:
    # TODO: Review unreachable code - return {"message": "No workflows to analyze"}

    # TODO: Review unreachable code - # Analyze patterns
    # TODO: Review unreachable code - total = len(workflows)
    # TODO: Review unreachable code - successful = sum(1 for w in workflows if w.successful)

    # TODO: Review unreachable code - # Average metrics
    # TODO: Review unreachable code - avg_duration = sum(w.duration or 0 for w in workflows) / total
    # TODO: Review unreachable code - avg_choices = sum(len(w.choices) for w in workflows) / total
    # TODO: Review unreachable code - avg_outcomes = sum(len(w.outcomes) for w in workflows) / total

    # TODO: Review unreachable code - # Quality metrics
    # TODO: Review unreachable code - quality_scores = [w.quality_score for w in workflows if w.quality_score]
    # TODO: Review unreachable code - avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

    # TODO: Review unreachable code - ratings = [w.user_rating for w in workflows if w.user_rating]
    # TODO: Review unreachable code - avg_rating = sum(ratings) / len(ratings) if ratings else None

    # TODO: Review unreachable code - # Common choices
    # TODO: Review unreachable code - choice_types = {}
    # TODO: Review unreachable code - for w in workflows:
    # TODO: Review unreachable code - for choice in w.choices:
    # TODO: Review unreachable code - ctype = choice["type"]
    # TODO: Review unreachable code - choice_types[ctype] = choice_types.get(ctype, 0) + 1

    # TODO: Review unreachable code - # Common adjustments
    # TODO: Review unreachable code - adjustments = 0
    # TODO: Review unreachable code - for w in workflows:
    # TODO: Review unreachable code - adjustments += sum(
    # TODO: Review unreachable code - 1 for choice in w.choices
    # TODO: Review unreachable code - if choice is not None and choice["type"] == "manual_adjustment"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "total_workflows": total,
    # TODO: Review unreachable code - "success_rate": successful / total,
    # TODO: Review unreachable code - "average_duration": avg_duration,
    # TODO: Review unreachable code - "average_choices": avg_choices,
    # TODO: Review unreachable code - "average_outcomes": avg_outcomes,
    # TODO: Review unreachable code - "average_quality": avg_quality,
    # TODO: Review unreachable code - "average_rating": avg_rating,
    # TODO: Review unreachable code - "common_choice_types": sorted(
    # TODO: Review unreachable code - choice_types.items(),
    # TODO: Review unreachable code - key=lambda x: x[1],
    # TODO: Review unreachable code - reverse=True
    # TODO: Review unreachable code - )[:5],
    # TODO: Review unreachable code - "adjustment_rate": adjustments / total if total > 0 else 0
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def get_improvement_areas(self) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Identify areas for improvement based on patterns.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of improvement suggestions
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - improvements = []

    # TODO: Review unreachable code - # Analyze adjustment patterns
    # TODO: Review unreachable code - adjustments = {}
    # TODO: Review unreachable code - for w in self.completed_workflows[-100:]:
    # TODO: Review unreachable code - for choice in w.choices:
    # TODO: Review unreachable code - if choice is not None and choice["type"] == "manual_adjustment":
    # TODO: Review unreachable code - original = str(choice["metadata"].get("original", ""))
    # TODO: Review unreachable code - if original:
    # TODO: Review unreachable code - adjustments[original] = adjustments.get(original, 0) + 1

    # TODO: Review unreachable code - # Frequent adjustments suggest poor defaults
    # TODO: Review unreachable code - for original, count in sorted(adjustments.items(), key=lambda x: x[1], reverse=True)[:5]:
    # TODO: Review unreachable code - if count > 3:
    # TODO: Review unreachable code - improvements.append({
    # TODO: Review unreachable code - "area": "default_values",
    # TODO: Review unreachable code - "issue": f"Value '{original}' frequently adjusted",
    # TODO: Review unreachable code - "count": count,
    # TODO: Review unreachable code - "suggestion": "Consider changing default or learning from adjustments"
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - # Analyze failed workflows
    # TODO: Review unreachable code - recent = self.completed_workflows[-50:]
    # TODO: Review unreachable code - failed = [w for w in recent if not w.successful]

    # TODO: Review unreachable code - if len(failed) / len(recent) > 0.2:  # >20% failure rate
    # TODO: Review unreachable code - # Find common failure patterns
    # TODO: Review unreachable code - failure_types = {}
    # TODO: Review unreachable code - for w in failed:
    # TODO: Review unreachable code - for outcome in w.outcomes:
    # TODO: Review unreachable code - if not outcome["successful"]:
    # TODO: Review unreachable code - otype = outcome["type"]
    # TODO: Review unreachable code - failure_types[otype] = failure_types.get(otype, 0) + 1

    # TODO: Review unreachable code - for ftype, count in sorted(failure_types.items(), key=lambda x: x[1], reverse=True)[:3]:
    # TODO: Review unreachable code - improvements.append({
    # TODO: Review unreachable code - "area": "error_reduction",
    # TODO: Review unreachable code - "issue": f"Frequent '{ftype}' failures",
    # TODO: Review unreachable code - "count": count,
    # TODO: Review unreachable code - "suggestion": "Investigate root cause and add validation"
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - # Analyze iteration patterns
    # TODO: Review unreachable code - high_iteration_workflows = []
    # TODO: Review unreachable code - for w in recent:
    # TODO: Review unreachable code - iterations = sum(
    # TODO: Review unreachable code - 1 for o in w.outcomes
    # TODO: Review unreachable code - if o is not None and o["type"] == "iteration"
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - if iterations > 3:
    # TODO: Review unreachable code - high_iteration_workflows.append((w, iterations))

    # TODO: Review unreachable code - if len(high_iteration_workflows) > len(recent) * 0.3:  # >30% need many iterations
    # TODO: Review unreachable code - improvements.append({
    # TODO: Review unreachable code - "area": "first_attempt_quality",
    # TODO: Review unreachable code - "issue": "Many workflows require multiple iterations",
    # TODO: Review unreachable code - "count": len(high_iteration_workflows),
    # TODO: Review unreachable code - "suggestion": "Improve initial generation quality or suggestions"
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - return improvements

    # TODO: Review unreachable code - def _map_to_preference_type(self, choice_type: str) -> PreferenceType | None:
    # TODO: Review unreachable code - """Map choice type string to PreferenceType enum.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - choice_type: String choice type

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - PreferenceType or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - mapping = {
    # TODO: Review unreachable code - "color_palette": PreferenceType.COLOR_PALETTE,
    # TODO: Review unreachable code - "color": PreferenceType.COLOR_PALETTE,
    # TODO: Review unreachable code - "composition": PreferenceType.COMPOSITION,
    # TODO: Review unreachable code - "layout": PreferenceType.COMPOSITION,
    # TODO: Review unreachable code - "lighting": PreferenceType.LIGHTING,
    # TODO: Review unreachable code - "light": PreferenceType.LIGHTING,
    # TODO: Review unreachable code - "texture": PreferenceType.TEXTURE,
    # TODO: Review unreachable code - "mood": PreferenceType.MOOD,
    # TODO: Review unreachable code - "emotion": PreferenceType.MOOD,
    # TODO: Review unreachable code - "subject": PreferenceType.SUBJECT,
    # TODO: Review unreachable code - "technique": PreferenceType.TECHNIQUE,
    # TODO: Review unreachable code - "style": PreferenceType.TECHNIQUE,
    # TODO: Review unreachable code - "transition": PreferenceType.TRANSITION,
    # TODO: Review unreachable code - "pacing": PreferenceType.PACING,
    # TODO: Review unreachable code - "rhythm": PreferenceType.PACING,
    # TODO: Review unreachable code - "effect": PreferenceType.EFFECT,
    # TODO: Review unreachable code - "filter": PreferenceType.EFFECT
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Direct match
    # TODO: Review unreachable code - if choice_type in mapping:
    # TODO: Review unreachable code - return mapping[choice_type]

    # TODO: Review unreachable code - # Partial match
    # TODO: Review unreachable code - choice_lower = choice_type.lower()
    # TODO: Review unreachable code - for key, pref_type in mapping.items():
    # TODO: Review unreachable code - if key in choice_lower:
    # TODO: Review unreachable code - return pref_type

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def _update_style_memory(self, context: WorkflowContext):
    # TODO: Review unreachable code - """Update style memory based on workflow results.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - context: Completed workflow context
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Get all preference IDs used
    # TODO: Review unreachable code - preference_ids = []

    # TODO: Review unreachable code - for choice in context.choices:
    # TODO: Review unreachable code - pref_type = self._map_to_preference_type(choice["type"])
    # TODO: Review unreachable code - if pref_type:
    # TODO: Review unreachable code - pref_id = f"{pref_type.value}:{choice['value']}"
    # TODO: Review unreachable code - preference_ids.append(pref_id)

    # TODO: Review unreachable code - if preference_ids:
    # TODO: Review unreachable code - # Track workflow result
    # TODO: Review unreachable code - self.style_memory.track_workflow_result(
    # TODO: Review unreachable code - preference_ids=preference_ids,
    # TODO: Review unreachable code - successful=context.successful or False,
    # TODO: Review unreachable code - quality_score=context.quality_score,
    # TODO: Review unreachable code - user_rating=context.user_rating
    # TODO: Review unreachable code - )
