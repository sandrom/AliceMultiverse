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

    def track_choice(
        self,
        workflow_id: str,
        choice_type: str,
        value: Any,
        metadata: dict[str, Any] | None = None
    ):
        """Track a choice made during workflow.
        
        Args:
            workflow_id: Workflow being tracked
            choice_type: Type of choice (e.g., "color_palette", "transition")
            value: The chosen value
            metadata: Additional context
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not active")
            return

        context = self.active_workflows[workflow_id]

        choice = {
            "timestamp": datetime.now(),
            "type": choice_type,
            "value": value,
            "metadata": metadata or {}
        }

        context.choices.append(choice)

        # Map to preference type if possible
        pref_type = self._map_to_preference_type(choice_type)
        if pref_type:
            self.style_memory.track_style_choice(
                preference_type=pref_type,
                value=value,
                context=metadata,
                project=context.project
            )

    def track_outcome(
        self,
        workflow_id: str,
        outcome_type: str,
        successful: bool,
        details: dict[str, Any] | None = None
    ):
        """Track an outcome during workflow.
        
        Args:
            workflow_id: Workflow being tracked
            outcome_type: Type of outcome
            successful: Whether outcome was successful
            details: Additional details
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not active")
            return

        context = self.active_workflows[workflow_id]

        outcome = {
            "timestamp": datetime.now(),
            "type": outcome_type,
            "successful": successful,
            "details": details or {}
        }

        context.outcomes.append(outcome)

    def track_adjustment(
        self,
        workflow_id: str,
        original_value: Any,
        adjusted_value: Any,
        reason: str | None = None
    ):
        """Track manual adjustments to generated content.
        
        Args:
            workflow_id: Workflow being tracked
            original_value: Original/generated value
            adjusted_value: User's adjusted value
            reason: Optional reason for adjustment
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not active")
            return

        # Track as both a choice and outcome
        self.track_choice(
            workflow_id,
            "manual_adjustment",
            adjusted_value,
            {
                "original": original_value,
                "reason": reason
            }
        )

        self.track_outcome(
            workflow_id,
            "adjustment_needed",
            False,  # Original wasn't satisfactory
            {
                "original": original_value,
                "adjusted": adjusted_value
            }
        )

    def track_iteration(
        self,
        workflow_id: str,
        iteration_number: int,
        changes: list[str],
        improved: bool = True
    ):
        """Track iterations and refinements.
        
        Args:
            workflow_id: Workflow being tracked
            iteration_number: Which iteration this is
            changes: List of changes made
            improved: Whether this iteration was an improvement
        """
        self.track_outcome(
            workflow_id,
            "iteration",
            improved,
            {
                "number": iteration_number,
                "changes": changes
            }
        )

    def end_workflow(
        self,
        workflow_id: str,
        successful: bool,
        quality_score: float | None = None,
        user_rating: int | None = None,
        notes: str | None = None
    ) -> WorkflowContext | None:
        """End workflow tracking and analyze results.
        
        Args:
            workflow_id: Workflow to end
            successful: Whether workflow was successful
            quality_score: Objective quality (0-1)
            user_rating: User satisfaction (1-5)
            notes: Optional notes
            
        Returns:
            Completed workflow context
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not active")
            return None

        context = self.active_workflows.pop(workflow_id)

        # Calculate duration
        context.duration = (datetime.now() - context.started_at).total_seconds()
        context.successful = successful
        context.quality_score = quality_score
        context.user_rating = user_rating
        context.notes = notes

        # Store in completed list
        self.completed_workflows.append(context)

        # Update style memory with results
        self._update_style_memory(context)

        logger.info(
            f"Ended workflow {workflow_id}: "
            f"success={successful}, duration={context.duration:.1f}s"
        )

        return context

    def get_workflow_summary(self, workflow_id: str) -> dict[str, Any] | None:
        """Get summary of a workflow (active or completed).
        
        Args:
            workflow_id: Workflow to summarize
            
        Returns:
            Summary dictionary or None
        """
        # Check active workflows
        if workflow_id in self.active_workflows:
            context = self.active_workflows[workflow_id]
        else:
            # Check completed workflows
            context = next(
                (w for w in self.completed_workflows if w.workflow_id == workflow_id),
                None
            )

        if not context:
            return None

        return {
            "workflow_id": context.workflow_id,
            "workflow_type": context.workflow_type.value,
            "project": context.project,
            "started_at": context.started_at.isoformat(),
            "duration": context.duration,
            "successful": context.successful,
            "choices_made": len(context.choices),
            "outcomes_tracked": len(context.outcomes),
            "quality_score": context.quality_score,
            "user_rating": context.user_rating,
            "notes": context.notes
        }

    def get_active_workflows(self) -> list[dict[str, Any]]:
        """Get all active workflows.
        
        Returns:
            List of workflow summaries
        """
        return [
            self.get_workflow_summary(wid)
            for wid in self.active_workflows
        ]

    def analyze_workflow_patterns(
        self,
        workflow_type: WorkflowType | None = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """Analyze patterns across completed workflows.
        
        Args:
            workflow_type: Filter by type
            limit: Max workflows to analyze
            
        Returns:
            Pattern analysis
        """
        # Filter workflows
        workflows = self.completed_workflows
        if workflow_type:
            workflows = [
                w for w in workflows
                if w.workflow_type == workflow_type
            ]

        # Take most recent
        workflows = workflows[-limit:]

        if not workflows:
            return {"message": "No workflows to analyze"}

        # Analyze patterns
        total = len(workflows)
        successful = sum(1 for w in workflows if w.successful)

        # Average metrics
        avg_duration = sum(w.duration or 0 for w in workflows) / total
        avg_choices = sum(len(w.choices) for w in workflows) / total
        avg_outcomes = sum(len(w.outcomes) for w in workflows) / total

        # Quality metrics
        quality_scores = [w.quality_score for w in workflows if w.quality_score]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        ratings = [w.user_rating for w in workflows if w.user_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # Common choices
        choice_types = {}
        for w in workflows:
            for choice in w.choices:
                ctype = choice["type"]
                choice_types[ctype] = choice_types.get(ctype, 0) + 1

        # Common adjustments
        adjustments = 0
        for w in workflows:
            adjustments += sum(
                1 for choice in w.choices
                if choice["type"] == "manual_adjustment"
            )

        return {
            "total_workflows": total,
            "success_rate": successful / total,
            "average_duration": avg_duration,
            "average_choices": avg_choices,
            "average_outcomes": avg_outcomes,
            "average_quality": avg_quality,
            "average_rating": avg_rating,
            "common_choice_types": sorted(
                choice_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "adjustment_rate": adjustments / total if total > 0 else 0
        }

    def get_improvement_areas(self) -> list[dict[str, Any]]:
        """Identify areas for improvement based on patterns.
        
        Returns:
            List of improvement suggestions
        """
        improvements = []

        # Analyze adjustment patterns
        adjustments = {}
        for w in self.completed_workflows[-100:]:
            for choice in w.choices:
                if choice["type"] == "manual_adjustment":
                    original = str(choice["metadata"].get("original", ""))
                    if original:
                        adjustments[original] = adjustments.get(original, 0) + 1

        # Frequent adjustments suggest poor defaults
        for original, count in sorted(adjustments.items(), key=lambda x: x[1], reverse=True)[:5]:
            if count > 3:
                improvements.append({
                    "area": "default_values",
                    "issue": f"Value '{original}' frequently adjusted",
                    "count": count,
                    "suggestion": "Consider changing default or learning from adjustments"
                })

        # Analyze failed workflows
        recent = self.completed_workflows[-50:]
        failed = [w for w in recent if not w.successful]

        if len(failed) / len(recent) > 0.2:  # >20% failure rate
            # Find common failure patterns
            failure_types = {}
            for w in failed:
                for outcome in w.outcomes:
                    if not outcome["successful"]:
                        otype = outcome["type"]
                        failure_types[otype] = failure_types.get(otype, 0) + 1

            for ftype, count in sorted(failure_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                improvements.append({
                    "area": "error_reduction",
                    "issue": f"Frequent '{ftype}' failures",
                    "count": count,
                    "suggestion": "Investigate root cause and add validation"
                })

        # Analyze iteration patterns
        high_iteration_workflows = []
        for w in recent:
            iterations = sum(
                1 for o in w.outcomes
                if o["type"] == "iteration"
            )
            if iterations > 3:
                high_iteration_workflows.append((w, iterations))

        if len(high_iteration_workflows) > len(recent) * 0.3:  # >30% need many iterations
            improvements.append({
                "area": "first_attempt_quality",
                "issue": "Many workflows require multiple iterations",
                "count": len(high_iteration_workflows),
                "suggestion": "Improve initial generation quality or suggestions"
            })

        return improvements

    def _map_to_preference_type(self, choice_type: str) -> PreferenceType | None:
        """Map choice type string to PreferenceType enum.
        
        Args:
            choice_type: String choice type
            
        Returns:
            PreferenceType or None
        """
        mapping = {
            "color_palette": PreferenceType.COLOR_PALETTE,
            "color": PreferenceType.COLOR_PALETTE,
            "composition": PreferenceType.COMPOSITION,
            "layout": PreferenceType.COMPOSITION,
            "lighting": PreferenceType.LIGHTING,
            "light": PreferenceType.LIGHTING,
            "texture": PreferenceType.TEXTURE,
            "mood": PreferenceType.MOOD,
            "emotion": PreferenceType.MOOD,
            "subject": PreferenceType.SUBJECT,
            "technique": PreferenceType.TECHNIQUE,
            "style": PreferenceType.TECHNIQUE,
            "transition": PreferenceType.TRANSITION,
            "pacing": PreferenceType.PACING,
            "rhythm": PreferenceType.PACING,
            "effect": PreferenceType.EFFECT,
            "filter": PreferenceType.EFFECT
        }

        # Direct match
        if choice_type in mapping:
            return mapping[choice_type]

        # Partial match
        choice_lower = choice_type.lower()
        for key, pref_type in mapping.items():
            if key in choice_lower:
                return pref_type

        return None

    def _update_style_memory(self, context: WorkflowContext):
        """Update style memory based on workflow results.
        
        Args:
            context: Completed workflow context
        """
        # Get all preference IDs used
        preference_ids = []

        for choice in context.choices:
            pref_type = self._map_to_preference_type(choice["type"])
            if pref_type:
                pref_id = f"{pref_type.value}:{choice['value']}"
                preference_ids.append(pref_id)

        if preference_ids:
            # Track workflow result
            self.style_memory.track_workflow_result(
                preference_ids=preference_ids,
                successful=context.successful or False,
                quality_score=context.quality_score,
                user_rating=context.user_rating
            )
