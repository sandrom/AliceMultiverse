"""Project management MCP tools."""

import logging
from typing import Any

from mcp.server import Server

from ...projects.service import ProjectService
from ..base import (
    ValidationError,
    create_tool_response,
    handle_errors,
    services,
    validate_path,
)
from ..utils.decorators import require_service

logger = logging.getLogger(__name__)


def register_project_tools(server: Server) -> None:
    """Register all project management tools with the MCP server.

    Args:
        server: MCP server instance
    """

    # Register project service loader
    services.register("projects", lambda: ProjectService())

    @server.tool()
    @handle_errors
    @require_service("projects")
    async def create_project(
        name: str,
        description: str | None = None,
        path: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> Any:
        """Create a new project.

        Args:
            name: Project name
            description: Project description
            path: Optional path to project directory
            tags: Optional project tags
            metadata: Optional additional metadata

        Returns:
            Created project information
        """
        # Validate inputs
        if not name or not name.strip():
            raise ValidationError("Project name is required")

        # TODO: Review unreachable code - # Validate path if provided
        # TODO: Review unreachable code - project_path = None
        # TODO: Review unreachable code - if path:
        # TODO: Review unreachable code - project_path = validate_path(path, must_exist=False)
        # TODO: Review unreachable code - # Create directory if it doesn't exist
        # TODO: Review unreachable code - project_path.mkdir(parents=True, exist_ok=True)

        # TODO: Review unreachable code - # Get project service
        # TODO: Review unreachable code - project_service = services.get("projects")

        # TODO: Review unreachable code - # Create project
        # TODO: Review unreachable code - project = project_service.create_project(
        # TODO: Review unreachable code - name=name.strip(),
        # TODO: Review unreachable code - description=description,
        # TODO: Review unreachable code - path=str(project_path) if project_path else None,
        # TODO: Review unreachable code - tags=tags or [],
        # TODO: Review unreachable code - metadata=metadata or {}
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - return create_tool_response(
        # TODO: Review unreachable code - success=True,
        # TODO: Review unreachable code - data={
        # TODO: Review unreachable code - "id": project.id,
        # TODO: Review unreachable code - "name": project.name,
        # TODO: Review unreachable code - "description": project.description,
        # TODO: Review unreachable code - "path": project.path,
        # TODO: Review unreachable code - "tags": project.tags,
        # TODO: Review unreachable code - "created_at": project.created_at.isoformat(),
        # TODO: Review unreachable code - "metadata": project.metadata
        # TODO: Review unreachable code - },
        # TODO: Review unreachable code - message=f"Created project '{name}'"
        # TODO: Review unreachable code - )

    @server.tool()
    @handle_errors
    @require_service("projects")
    async def list_projects(
        active_only: bool = True,
        with_stats: bool = False
    ) -> Any:
        """List all projects.

        Args:
            active_only: Only show active projects
            with_stats: Include project statistics

        Returns:
            List of projects
        """
        # Get project service
        project_service = services.get("projects")

        # Get projects
        projects = project_service.list_projects(active_only=active_only)

        # Format project data
        project_list = []
        for project in projects:
            project_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "path": project.path,
                "tags": project.tags,
                "active": project.active,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }

            # Add stats if requested
            if with_stats:
                stats = project_service.get_project_stats(project.id)
                if project_data is not None:
                    project_data["stats"] = {
                    "asset_count": stats.get("total_assets", 0),
                    "total_size": stats.get("total_size", 0),
                    "last_activity": stats.get("last_activity"),
                    "tags_used": stats.get("unique_tags", 0)
                }

            project_list.append(project_data)

        return create_tool_response(
            success=True,
            data={
                "projects": project_list,
                "count": len(project_list)
            }
        )

    @server.tool()
    @handle_errors
    @require_service("projects")
    async def get_project_context(
        project_id: str | None = None,
        project_name: str | None = None
    ) -> Any:
        """Get context for a specific project.

        Args:
            project_id: Project ID
            project_name: Project name (alternative to ID)

        Returns:
            Project context including assets and metadata
        """
        # Validate inputs
        if not project_id and not project_name:
            raise ValidationError("Either project_id or project_name is required")

        # TODO: Review unreachable code - # Get project service
        # TODO: Review unreachable code - project_service = services.get("projects")

        # TODO: Review unreachable code - # Find project
        # TODO: Review unreachable code - if project_id:
        # TODO: Review unreachable code - project = project_service.get_project(project_id)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - # Find by name
        # TODO: Review unreachable code - projects = project_service.list_projects()
        # TODO: Review unreachable code - matching = [p for p in projects if p.name == project_name]
        # TODO: Review unreachable code - if not matching:
        # TODO: Review unreachable code - raise ValidationError(f"Project '{project_name}' not found")
        # TODO: Review unreachable code - project = matching[0]

        # TODO: Review unreachable code - if not project:
        # TODO: Review unreachable code - raise ValidationError("Project not found")

        # TODO: Review unreachable code - # Get project context
        # TODO: Review unreachable code - context = project_service.get_project_context(project.id)

        # TODO: Review unreachable code - # Get recent assets
        # TODO: Review unreachable code - recent_assets = project_service.get_recent_assets(project.id, limit=10)

        # TODO: Review unreachable code - return create_tool_response(
        # TODO: Review unreachable code - success=True,
        # TODO: Review unreachable code - data={
        # TODO: Review unreachable code - "project": {
        # TODO: Review unreachable code - "id": project.id,
        # TODO: Review unreachable code - "name": project.name,
        # TODO: Review unreachable code - "description": project.description,
        # TODO: Review unreachable code - "path": project.path,
        # TODO: Review unreachable code - "tags": project.tags,
        # TODO: Review unreachable code - "created_at": project.created_at.isoformat(),
        # TODO: Review unreachable code - "updated_at": project.updated_at.isoformat()
        # TODO: Review unreachable code - },
        # TODO: Review unreachable code - "context": context,
        # TODO: Review unreachable code - "recent_assets": [
        # TODO: Review unreachable code - {
        # TODO: Review unreachable code - "path": asset.get("file_path"),
        # TODO: Review unreachable code - "type": asset.get("media_type"),
        # TODO: Review unreachable code - "tags": asset.get("tags", []),
        # TODO: Review unreachable code - "added_at": asset.get("created_at")
        # TODO: Review unreachable code - }
        # TODO: Review unreachable code - for asset in recent_assets
        # TODO: Review unreachable code - ],
        # TODO: Review unreachable code - "stats": project_service.get_project_stats(project.id)
        # TODO: Review unreachable code - }
        # TODO: Review unreachable code - )

    @server.tool()
    @handle_errors
    @require_service("projects")
    async def update_project_context(
        project_id: str,
        context_key: str,
        context_value: Any,
        merge: bool = True
    ) -> Any:
        """Update project context.

        Args:
            project_id: Project ID
            context_key: Context key to update
            context_value: New context value
            merge: Whether to merge with existing value (for dicts/lists)

        Returns:
            Updated context
        """
        # Get project service
        project_service = services.get("projects")

        # Verify project exists
        project = project_service.get_project(project_id)
        if not project:
            raise ValidationError(f"Project '{project_id}' not found")

        # TODO: Review unreachable code - # Update context
        # TODO: Review unreachable code - updated_context = project_service.update_project_context(
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - key=context_key,
        # TODO: Review unreachable code - value=context_value,
        # TODO: Review unreachable code - merge=merge
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - return create_tool_response(
        # TODO: Review unreachable code - success=True,
        # TODO: Review unreachable code - data={
        # TODO: Review unreachable code - "project_id": project_id,
        # TODO: Review unreachable code - "updated_key": context_key,
        # TODO: Review unreachable code - "new_value": context_value,
        # TODO: Review unreachable code - "full_context": updated_context
        # TODO: Review unreachable code - },
        # TODO: Review unreachable code - message=f"Updated project context for '{project.name}'"
        # TODO: Review unreachable code - )
