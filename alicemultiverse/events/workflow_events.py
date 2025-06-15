"""Workflow-specific events."""

from dataclasses import dataclass

from .base import Event


@dataclass
class WorkflowStartedEvent(Event):
    """Published when a workflow starts execution."""
    workflow_name: str
    workflow_id: str
    total_steps: int

    def __post_init__(self):
        """Initialize base event fields."""
        super().__init__()

    @property
    def event_type(self) -> str:
        return "workflow.started"


@dataclass
class WorkflowCompletedEvent(Event):
    """Published when a workflow completes successfully."""
    workflow_name: str
    workflow_id: str
    total_cost: float
    execution_time: float
    completed_steps: int
    total_steps: int

    def __post_init__(self):
        """Initialize base event fields."""
        super().__init__()

    @property
    def event_type(self) -> str:
        return "workflow.completed"


@dataclass
class WorkflowFailedEvent(Event):
    """Published when a workflow fails."""
    workflow_name: str
    workflow_id: str
    error: str

    def __post_init__(self):
        """Initialize base event fields."""
        super().__init__()

    @property
    def event_type(self) -> str:
        return "workflow.failed"


@dataclass
class WorkflowStepStartedEvent(Event):
    """Published when a workflow step starts."""
    workflow_id: str
    step_name: str

    def __post_init__(self):
        """Initialize base event fields."""
        super().__init__()

    @property
    def event_type(self) -> str:
        return "workflow.step.started"


@dataclass
class WorkflowStepCompletedEvent(Event):
    """Published when a workflow step completes."""
    workflow_id: str
    step_name: str
    success: bool
    cost: float

    def __post_init__(self):
        """Initialize base event fields."""
        super().__init__()

    @property
    def event_type(self) -> str:
        return "workflow.step.completed"
