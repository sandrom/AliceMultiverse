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


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class WorkflowCompletedEvent(Event):
# TODO: Review unreachable code - """Published when a workflow completes successfully."""
# TODO: Review unreachable code - workflow_name: str
# TODO: Review unreachable code - workflow_id: str
# TODO: Review unreachable code - total_cost: float
# TODO: Review unreachable code - execution_time: float
# TODO: Review unreachable code - completed_steps: int
# TODO: Review unreachable code - total_steps: int

# TODO: Review unreachable code - def __post_init__(self):
# TODO: Review unreachable code - """Initialize base event fields."""
# TODO: Review unreachable code - super().__init__()

# TODO: Review unreachable code - @property
# TODO: Review unreachable code - def event_type(self) -> str:
# TODO: Review unreachable code - return "workflow.completed"


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class WorkflowFailedEvent(Event):
# TODO: Review unreachable code - """Published when a workflow fails."""
# TODO: Review unreachable code - workflow_name: str
# TODO: Review unreachable code - workflow_id: str
# TODO: Review unreachable code - error: str

# TODO: Review unreachable code - def __post_init__(self):
# TODO: Review unreachable code - """Initialize base event fields."""
# TODO: Review unreachable code - super().__init__()

# TODO: Review unreachable code - @property
# TODO: Review unreachable code - def event_type(self) -> str:
# TODO: Review unreachable code - return "workflow.failed"


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class WorkflowStepStartedEvent(Event):
# TODO: Review unreachable code - """Published when a workflow step starts."""
# TODO: Review unreachable code - workflow_id: str
# TODO: Review unreachable code - step_name: str

# TODO: Review unreachable code - def __post_init__(self):
# TODO: Review unreachable code - """Initialize base event fields."""
# TODO: Review unreachable code - super().__init__()

# TODO: Review unreachable code - @property
# TODO: Review unreachable code - def event_type(self) -> str:
# TODO: Review unreachable code - return "workflow.step.started"


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class WorkflowStepCompletedEvent(Event):
# TODO: Review unreachable code - """Published when a workflow step completes."""
# TODO: Review unreachable code - workflow_id: str
# TODO: Review unreachable code - step_name: str
# TODO: Review unreachable code - success: bool
# TODO: Review unreachable code - cost: float

# TODO: Review unreachable code - def __post_init__(self):
# TODO: Review unreachable code - """Initialize base event fields."""
# TODO: Review unreachable code - super().__init__()

# TODO: Review unreachable code - @property
# TODO: Review unreachable code - def event_type(self) -> str:
# TODO: Review unreachable code - return "workflow.step.completed"
