"""Main AliceInterface class combining all operation mixins."""

from pathlib import Path

from .base import NaturalInterfaceBase
from .content_operations import ContentOperationsMixin
from .organization_operations import OrganizationOperationsMixin
from .project_operations import ProjectOperationsMixin
from .search_operations import SearchOperationsMixin
from .similarity_operations import SimilarityOperationsMixin


class AliceInterface(
    NaturalInterfaceBase,
    SearchOperationsMixin,
    ContentOperationsMixin,
    OrganizationOperationsMixin,
    ProjectOperationsMixin,
    SimilarityOperationsMixin
):
    """Primary interface for AI assistants to interact with AliceMultiverse.

    This class provides high-level functions that AI can call using natural
    language concepts, while Alice handles all technical complexity.
    
    The interface is composed of several operation mixins:
    - SearchOperationsMixin: search_assets, find_similar_assets
    - ContentOperationsMixin: generate_content
    - OrganizationOperationsMixin: organize_media, tag_assets, group_assets
    - ProjectOperationsMixin: get_project_context, create_project, update_project_context,
                              get_project_budget_status, list_projects, set_asset_role, 
                              get_asset_info
    - SimilarityOperationsMixin: (reserved for future similarity operations)
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize Alice interface.

        Args:
            config_path: Optional path to configuration file
        """
        # Base class initializes all shared components
        super().__init__(config_path)
