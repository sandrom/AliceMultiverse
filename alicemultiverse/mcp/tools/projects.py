"""Project management MCP tools."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import Server

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
        description: Optional[str] = None,
        path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
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
        
        # Validate path if provided
        project_path = None
        if path:
            project_path = validate_path(path, must_exist=False)
            # Create directory if it doesn't exist
            project_path.mkdir(parents=True, exist_ok=True)
        
        # Get project service
        project_service = services.get("projects")
        
        # Create project
        project = project_service.create_project(
            name=name.strip(),
            description=description,
            path=str(project_path) if project_path else None,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        return create_tool_response(
            success=True,
            data={
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "path": project.path,
                "tags": project.tags,
                "created_at": project.created_at.isoformat(),
                "metadata": project.metadata
            },
            message=f"Created project '{name}'"
        )
    
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
        project_id: Optional[str] = None,
        project_name: Optional[str] = None
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
        
        # Get project service
        project_service = services.get("projects")
        
        # Find project
        if project_id:
            project = project_service.get_project(project_id)
        else:
            # Find by name
            projects = project_service.list_projects()
            matching = [p for p in projects if p.name == project_name]
            if not matching:
                raise ValidationError(f"Project '{project_name}' not found")
            project = matching[0]
        
        if not project:
            raise ValidationError("Project not found")
        
        # Get project context
        context = project_service.get_project_context(project.id)
        
        # Get recent assets
        recent_assets = project_service.get_recent_assets(project.id, limit=10)
        
        return create_tool_response(
            success=True,
            data={
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "path": project.path,
                    "tags": project.tags,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat()
                },
                "context": context,
                "recent_assets": [
                    {
                        "path": asset.get("file_path"),
                        "type": asset.get("media_type"),
                        "tags": asset.get("tags", []),
                        "added_at": asset.get("created_at")
                    }
                    for asset in recent_assets
                ],
                "stats": project_service.get_project_stats(project.id)
            }
        )
    
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
        
        # Update context
        updated_context = project_service.update_project_context(
            project_id=project_id,
            key=context_key,
            value=context_value,
            merge=merge
        )
        
        return create_tool_response(
            success=True,
            data={
                "project_id": project_id,
                "updated_key": context_key,
                "new_value": context_value,
                "full_context": updated_context
            },
            message=f"Updated project context for '{project.name}'"
        )