"""Selection and quick mark MCP tools."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp import Server

from ...selections.models import SelectionCreate
from ...selections.service import SelectionService
from ..base import (
    ValidationError,
    create_tool_response,
    handle_errors,
    services,
    validate_path,
)
from ..utils.decorators import require_service

logger = logging.getLogger(__name__)


def register_selection_tools(server: Server) -> None:
    """Register all selection/quick mark tools with the MCP server.
    
    Args:
        server: MCP server instance
    """

    # Register selection service loader
    services.register("selections", lambda: SelectionService())

    @server.tool()
    @handle_errors
    @require_service("selections")
    async def quick_mark(
        paths: list[str],
        name: str | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
        rating: int | None = None
    ) -> Any:
        """Quickly mark files for later reference.
        
        Args:
            paths: List of file paths to mark
            name: Optional name for the selection
            tags: Optional tags
            notes: Optional notes
            rating: Optional rating (1-5)
            
        Returns:
            Created selection information
        """
        # Validate inputs
        if not paths:
            raise ValidationError("At least one path is required")

        # Validate paths
        valid_paths = []
        for path_str in paths:
            try:
                path = validate_path(path_str, must_exist=True)
                valid_paths.append(str(path))
            except ValidationError as e:
                logger.warning(f"Skipping invalid path: {e}")

        if not valid_paths:
            raise ValidationError("No valid paths provided")

        # Validate rating if provided
        if rating is not None:
            if not 1 <= rating <= 5:
                raise ValidationError("Rating must be between 1 and 5")

        # Generate name if not provided
        if not name:
            name = f"Quick Mark {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Get selection service
        selection_service = services.get("selections")

        # Create selection
        selection_data = SelectionCreate(
            name=name,
            paths=valid_paths,
            tags=tags or [],
            notes=notes,
            metadata={"rating": rating} if rating else {}
        )

        selection = selection_service.create_selection(selection_data)

        return create_tool_response(
            success=True,
            data={
                "id": selection.id,
                "name": selection.name,
                "file_count": len(selection.paths),
                "tags": selection.tags,
                "created_at": selection.created_at.isoformat()
            },
            message=f"Marked {len(valid_paths)} files as '{name}'"
        )

    @server.tool()
    @handle_errors
    @require_service("selections")
    async def list_quick_marks(
        tags: list[str] | None = None,
        limit: int = 20,
        include_paths: bool = False
    ) -> Any:
        """List recent quick marks/selections.
        
        Args:
            tags: Filter by tags
            limit: Maximum number to return
            include_paths: Whether to include file paths in response
            
        Returns:
            List of selections
        """
        # Validate limit
        if limit <= 0:
            raise ValidationError("Limit must be positive")

        # Get selection service
        selection_service = services.get("selections")

        # Get selections
        selections = selection_service.list_selections(
            tags=tags,
            limit=limit
        )

        # Format selections
        selection_list = []
        for selection in selections:
            data = {
                "id": selection.id,
                "name": selection.name,
                "file_count": len(selection.paths),
                "tags": selection.tags,
                "notes": selection.notes,
                "created_at": selection.created_at.isoformat(),
                "metadata": selection.metadata
            }

            if include_paths:
                data["paths"] = selection.paths

            selection_list.append(data)

        return create_tool_response(
            success=True,
            data={
                "selections": selection_list,
                "count": len(selection_list),
                "total_files": sum(s["file_count"] for s in selection_list)
            }
        )

    @server.tool()
    @handle_errors
    @require_service("selections")
    async def export_quick_marks(
        selection_id: str | None = None,
        output_path: str | None = None,
        format: str = "json"
    ) -> Any:
        """Export quick marks/selections to a file.
        
        Args:
            selection_id: Specific selection to export (exports all if not provided)
            output_path: Output file path
            format: Export format (json, txt, csv)
            
        Returns:
            Export information
        """
        # Validate format
        if format not in ["json", "txt", "csv"]:
            raise ValidationError("Format must be one of: json, txt, csv")

        # Get selection service
        selection_service = services.get("selections")

        # Get selections to export
        if selection_id:
            selection = selection_service.get_selection(selection_id)
            if not selection:
                raise ValidationError(f"Selection '{selection_id}' not found")
            selections = [selection]
        else:
            selections = selection_service.list_selections()

        if not selections:
            raise ValidationError("No selections to export")

        # Determine output path
        if output_path:
            output_file = validate_path(output_path, must_exist=False)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f"selections_export_{timestamp}.{format}")

        # Export based on format
        if format == "json":
            export_data = []
            for sel in selections:
                export_data.append({
                    "id": sel.id,
                    "name": sel.name,
                    "paths": sel.paths,
                    "tags": sel.tags,
                    "notes": sel.notes,
                    "metadata": sel.metadata,
                    "created_at": sel.created_at.isoformat()
                })

            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)

        elif format == "txt":
            lines = []
            for sel in selections:
                lines.append(f"# {sel.name}")
                lines.append(f"Created: {sel.created_at}")
                if sel.tags:
                    lines.append(f"Tags: {', '.join(sel.tags)}")
                if sel.notes:
                    lines.append(f"Notes: {sel.notes}")
                lines.append("Files:")
                for path in sel.paths:
                    lines.append(f"  - {path}")
                lines.append("")  # Empty line between selections

            with open(output_file, 'w') as f:
                f.write("\n".join(lines))

        elif format == "csv":
            import csv

            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Selection", "File", "Tags", "Notes", "Created"])

                for sel in selections:
                    tags_str = ", ".join(sel.tags) if sel.tags else ""
                    for path in sel.paths:
                        writer.writerow([
                            sel.name,
                            path,
                            tags_str,
                            sel.notes or "",
                            sel.created_at.isoformat()
                        ])

        # Get file size
        file_size = output_file.stat().st_size

        return create_tool_response(
            success=True,
            data={
                "output_file": str(output_file),
                "format": format,
                "selections_exported": len(selections),
                "total_files": sum(len(s.paths) for s in selections),
                "file_size": file_size
            },
            message=f"Exported {len(selections)} selections to {output_file.name}"
        )
