"""Workflow-specific events."""

from dataclasses import dataclass
from typing import Optional

from .base import Event


@dataclass
class WorkflowStartedEvent(Event):
    """Published when a workflow starts execution."""
    workflow_name: str
    workflow_id: str
    total_steps: int
    
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
    
    @property
    def event_type(self) -> str:
        return "workflow.completed"


@dataclass
class WorkflowFailedEvent(Event):
    """Published when a workflow fails."""
    workflow_name: str
    workflow_id: str
    error: str
    
    @property
    def event_type(self) -> str:
        return "workflow.failed"


@dataclass
class WorkflowStepStartedEvent(Event):
    """Published when a workflow step starts."""
    workflow_id: str
    step_name: str
    
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
    
    @property
    def event_type(self) -> str:
        return "workflow.step.completed"