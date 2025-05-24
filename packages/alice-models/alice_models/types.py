"""Type definitions and value objects."""

from typing import NewType, Union
from datetime import datetime
from pathlib import Path

# Type aliases for better type safety
ContentHash = NewType('ContentHash', str)
FilePath = Union[str, Path]
ProjectId = NewType('ProjectId', str)
WorkflowId = NewType('WorkflowId', str)
AssetId = NewType('AssetId', str)
Timestamp = Union[datetime, str]

# Validation functions
def validate_content_hash(value: str) -> ContentHash:
    """Validate and create a ContentHash."""
    if not value or len(value) < 32:
        raise ValueError("Invalid content hash")
    return ContentHash(value)

def validate_project_id(value: str) -> ProjectId:
    """Validate and create a ProjectId."""
    if not value or not value.startswith("proj-"):
        raise ValueError("Project ID must start with 'proj-'")
    return ProjectId(value)

def validate_workflow_id(value: str) -> WorkflowId:
    """Validate and create a WorkflowId."""
    if not value or not value.startswith("wf-"):
        raise ValueError("Workflow ID must start with 'wf-'")
    return WorkflowId(value)