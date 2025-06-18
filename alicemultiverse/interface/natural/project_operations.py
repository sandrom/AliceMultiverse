"""Project operations for natural language interface."""

import logging
from typing import Any

from ...assets.metadata.models import AssetRole
from ...core.ai_errors import AIFriendlyError
from ..models import ProjectContextRequest
from .base import AliceResponse

logger = logging.getLogger(__name__)


class ProjectOperationsMixin:
    """Mixin for project-related operations."""

    def get_project_context(self, request: ProjectContextRequest) -> AliceResponse:
        """Get project context and statistics.

        Args:
            request: Context request

        Returns:
            Response with project context
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            context = self.organizer.get_project_context()

            # Add recent assets if requested
            if request.get("include_recent_assets"):
                recent = self.organizer.search_assets(sort_by="created", limit=10)
                context["recent_assets"] = [self._simplify_asset_info(asset) for asset in recent]

            return AliceResponse(
                success=True, message="Project context retrieved", data=context, error=None
            )

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return AliceResponse(
                success=False, message="Context retrieval failed", data=None, error=str(e)
            )

    def create_project(
        self,
        name: str,
        description: str | None = None,
        budget: float | None = None,
        creative_context: dict[str, Any] | None = None
    ) -> AliceResponse:
        """Create a new project for organizing creative work.

        Args:
            name: Project name
            description: Optional project description
            budget: Optional budget limit in USD
            creative_context: Optional creative context (style preferences, characters, etc.)

        Returns:
            Response with created project details
        """
        try:
            project = self.project_service.create_project(
                name=name,
                description=description,
                budget_total=budget,
                creative_context=creative_context
            )

            return AliceResponse(
                success=True,
                message=f"Created project '{name}'",
                data={
                    "project_id": project.id,
                    "name": project.name,
                    "budget": project.budget_total,
                    "status": project.status
                },
                error=None
            )

        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            friendly = AIFriendlyError.make_friendly(e, {"operation": "create_project", "name": name})
            return AliceResponse(
                success=False,
                message=friendly["error"],
                data={"suggestions": friendly["suggestions"]},
                error=friendly["technical_details"]
            )

    def update_project_context(
        self,
        project_id: str,
        creative_context: dict[str, Any]
    ) -> AliceResponse:
        """Update project's creative context.

        Args:
            project_id: Project identifier
            creative_context: New creative context to merge

        Returns:
            Response with updated project
        """
        try:
            updated = self.project_service.update_creative_context(
                project_id, creative_context
            )

            if updated:
                return AliceResponse(
                    success=True,
                    message="Project context updated",
                    data={
                        "project_id": project_id,
                        "creative_context": updated.creative_context
                    },
                    error=None
                )
            else:
                return AliceResponse(
                    success=False,
                    message="Project not found",
                    data=None,
                    error=f"No project found with ID: {project_id}"
                )

        except Exception as e:
            logger.error(f"Project update failed: {e}")
            return AliceResponse(
                success=False,
                message="Project update failed",
                data=None,
                error=str(e)
            )

    def get_project_budget_status(self, project_id: str) -> AliceResponse:
        """Get budget status for a project.

        Args:
            project_id: Project identifier

        Returns:
            Response with budget information
        """
        try:
            project = self.project_service.get_project(project_id)

            if not project:
                return AliceResponse(
                    success=False,
                    message="Project not found",
                    data=None,
                    error=f"No project found with ID: {project_id}"
                )

            # Calculate budget usage
            budget_data = {
                "total_budget": project.budget_total,
                "used_budget": project.budget_used,
                "remaining_budget": project.budget_total - project.budget_used if project.budget_total else None,
                "percentage_used": (project.budget_used / project.budget_total * 100) if project.budget_total and project.budget_total > 0 else 0
            }

            return AliceResponse(
                success=True,
                message=f"Budget status for '{project.name}'",
                data=budget_data,
                error=None
            )

        except Exception as e:
            logger.error(f"Budget status failed: {e}")
            return AliceResponse(
                success=False,
                message="Failed to get budget status",
                data=None,
                error=str(e)
            )

    def list_projects(self, status: str | None = None) -> AliceResponse:
        """List all projects with optional status filter.

        Args:
            status: Optional status filter ('active', 'completed', 'archived')

        Returns:
            Response with project list
        """
        try:
            projects = self.project_service.list_projects()

            # Filter by status if requested
            if status:
                projects = [p for p in projects if p.get("status") == status]

            return AliceResponse(
                success=True,
                message=f"Found {len(projects)} projects",
                data={
                    "projects": projects,
                    "total_count": len(projects)
                },
                error=None
            )

        except Exception as e:
            logger.error(f"Project listing failed: {e}")
            return AliceResponse(
                success=False,
                message="Failed to list projects",
                data=None,
                error=str(e)
            )

    def set_asset_role(self, asset_id: str, role: str) -> AliceResponse:
        """Set the creative role of an asset.

        Args:
            asset_id: Asset ID
            role: Role name (hero, b_roll, reference, etc.)

        Returns:
            Response indicating success
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            role_enum = AssetRole(role)
            success = self.organizer.set_asset_role(asset_id, role_enum)

            return AliceResponse(
                success=success,
                message=f"Set role to '{role}'" if success else "Failed to set role",
                data={"asset_id": asset_id, "role": role},
                error=None,
            )

        except Exception as e:
            logger.error(f"Role setting failed: {e}")
            return AliceResponse(
                success=False, message="Role setting failed", data=None, error=str(e)
            )

    def get_asset_info(self, asset_id: str) -> AliceResponse:
        """Get detailed information about a specific asset.

        Args:
            asset_id: The unique asset identifier

        Returns:
            Response with asset information
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            # Search for the asset
            all_metadata = self.organizer.metadata_cache.get_all_metadata()

            for file_path, metadata in all_metadata.items():
                if metadata.get("asset_id") == asset_id or metadata.get("file_hash") == asset_id:
                    metadata["file_path"] = str(file_path)
                    return AliceResponse(
                        success=True,
                        message="Asset found",
                        data=self._simplify_asset_info(metadata),
                        error=None
                    )

            return AliceResponse(
                success=False,
                message=f"Asset {asset_id} not found",
                data=None,
                error="Asset not found in metadata"
            )

        except Exception as e:
            logger.error(f"Asset info retrieval failed: {e}")
            return AliceResponse(
                success=False,
                message="Failed to get asset info",
                data=None,
                error=str(e)
            )
