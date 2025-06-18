"""Main AliceStructuredInterface class combining all operation mixins."""

from pathlib import Path

from .asset_operations import AssetOperationsMixin
from .base import StructuredInterfaceBase
from .organization_operations import OrganizationOperationsMixin
from .project_operations import ProjectOperationsMixin
from .selection_operations import SelectionOperationsMixin
from .workflow_operations import WorkflowOperationsMixin


class AliceStructuredInterface(
    StructuredInterfaceBase,
    AssetOperationsMixin,
    OrganizationOperationsMixin,
    ProjectOperationsMixin,
    SelectionOperationsMixin,
    WorkflowOperationsMixin
):
    """Structured interface for AI assistants to interact with AliceMultiverse.

    This interface accepts ONLY structured queries - no natural language processing.
    All NLP should happen at the AI assistant layer before calling these methods.

    The interface is composed of several operation mixins:
    - AssetOperationsMixin: search_assets, get_asset_by_id, set_asset_role, soft_delete_assets
    - OrganizationOperationsMixin: organize_media, update_tags, group_assets
    - ProjectOperationsMixin: manage_project
    - SelectionOperationsMixin: create_selection, update_selection, search_selections,
                                export_selection, get_selection, find_similar_to_selection
    - WorkflowOperationsMixin: execute_workflow, generate_content
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize Alice structured interface.

        Args:
            config_path: Optional path to configuration file
        """
        # Base class initializes all shared components
        super().__init__(config_path)
