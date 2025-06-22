"""Alice Interface - The primary interface for AI assistants."""

from .alice_api import AliceAPI, ask_alice, ask_alice_sync
# AliceMCP is commented out in alice_api.py
from .alice_interface import AliceInterface
# from .alice_orchestrator import AliceOrchestrator, CreativeIntent, CreativeResponse  # Temporarily disabled
from .alice_structured import AliceStructuredInterface
from .creative_models import (
    CreativeAsset,
    CreativeContext,
    CreativeMood,
    CreativeRole,
    CreativeWorkflow,
    WorkflowPhase,
)
from .models import (
    AliceResponse,
    GenerateRequest,
    GroupRequest,
    OrganizeRequest,
    SearchRequest,
    TagRequest,
)
from .structured_models import (
    AssetRole,
    DimensionFilter,
    GroupingRequest,
    MediaType,
    ProjectRequest,
    RangeFilter,
    SearchFilters,
    SearchResponse,
    SortField,
    SortOrder,
    TagUpdateRequest,
    WorkflowRequest,
)
from .structured_models import (
    GenerationRequest as StructuredGenerationRequest,
)
from .structured_models import (
    OrganizeRequest as StructuredOrganizeRequest,
)
from .structured_models import (
    SearchRequest as StructuredSearchRequest,
)

__all__ = [
    # Legacy interface (deprecated)
    "AliceInterface",
    "AliceResponse",
    "SearchRequest",
    "GenerateRequest",
    "OrganizeRequest",
    "TagRequest",
    "GroupRequest",
    # Structured interface (recommended)
    "AliceStructuredInterface",
    "AssetRole",
    "DimensionFilter",
    "GroupingRequest",
    "MediaType",
    "ProjectRequest",
    "RangeFilter",
    "SearchFilters",
    "SearchResponse",
    "SortField",
    "SortOrder",
    "StructuredGenerationRequest",
    "StructuredOrganizeRequest",
    "StructuredSearchRequest",
    "TagUpdateRequest",
    "WorkflowRequest",
    # New orchestrator (temporarily disabled)
    # "AliceOrchestrator",
    # "CreativeIntent", 
    # "CreativeResponse",
    "AliceAPI",
    "ask_alice",
    "ask_alice_sync",
    # Creative models
    "CreativeContext",
    "CreativeAsset",
    "CreativeWorkflow",
    "CreativeRole",
    "CreativeMood",
    "WorkflowPhase",
]
