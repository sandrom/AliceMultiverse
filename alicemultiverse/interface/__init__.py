"""Alice Interface - The primary interface for AI assistants."""

from .alice_interface import AliceInterface
from .alice_orchestrator import AliceOrchestrator, CreativeResponse
from .alice_api import AliceAPI, ask_alice, ask_alice_sync, AliceMCP
from .creative_models import (
    CreativeContext, CreativeAsset, CreativeWorkflow,
    CreativeRole, CreativeMood, WorkflowPhase
)
from .models import (
    AliceResponse,
    SearchRequest,
    GenerateRequest,
    OrganizeRequest,
    TagRequest,
    GroupRequest
)

__all__ = [
    # Legacy interface
    "AliceInterface",
    "AliceResponse",
    "SearchRequest", 
    "GenerateRequest",
    "OrganizeRequest",
    "TagRequest",
    "GroupRequest",
    
    # New orchestrator
    "AliceOrchestrator",
    "CreativeResponse",
    "AliceAPI",
    "ask_alice",
    "ask_alice_sync",
    "AliceMCP",
    
    # Creative models
    "CreativeContext",
    "CreativeAsset",
    "CreativeWorkflow",
    "CreativeRole",
    "CreativeMood",
    "WorkflowPhase"
]