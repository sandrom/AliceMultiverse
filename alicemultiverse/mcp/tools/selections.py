"""Selection and quick mark MCP tools."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server

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

        # TODO: Review unreachable code - # Validate paths
        # TODO: Review unreachable code - valid_paths = []
        # TODO: Review unreachable code - for path_str in paths:
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - path = validate_path(path_str, must_exist=True)
        # TODO: Review unreachable code - valid_paths.append(str(path))
        # TODO: Review unreachable code - except ValidationError as e:
        # TODO: Review unreachable code - logger.warning(f"Skipping invalid path: {e}")

        # TODO: Review unreachable code - if not valid_paths:
        # TODO: Review unreachable code - raise ValidationError("No valid paths provided")

        # TODO: Review unreachable code - # Validate rating if provided
        # TODO: Review unreachable code - if rating is not None:
        # TODO: Review unreachable code - if not 1 <= rating <= 5:
        # TODO: Review unreachable code - raise ValidationError("Rating must be between 1 and 5")

        # TODO: Review unreachable code - # Generate name if not provided
        # TODO: Review unreachable code - if not name:
        # TODO: Review unreachable code - name = f"Quick Mark {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # TODO: Review unreachable code - # Get selection service
        # TODO: Review unreachable code - selection_service = services.get("selections")

        # TODO: Review unreachable code - # Create selection
        # TODO: Review unreachable code - selection_data = SelectionCreate(
        # TODO: Review unreachable code - name=name,
        # TODO: Review unreachable code - paths=valid_paths,
        # TODO: Review unreachable code - tags=tags or [],
        # TODO: Review unreachable code - notes=notes,
        # TODO: Review unreachable code - metadata={"rating": rating} if rating else {}
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - selection = selection_service.create_selection(selection_data)

        # TODO: Review unreachable code - return create_tool_response(
        # TODO: Review unreachable code - success=True,
        # TODO: Review unreachable code - data={
        # TODO: Review unreachable code - "id": selection.id,
        # TODO: Review unreachable code - "name": selection.name,
        # TODO: Review unreachable code - "file_count": len(selection.paths),
        # TODO: Review unreachable code - "tags": selection.tags,
        # TODO: Review unreachable code - "created_at": selection.created_at.isoformat()
        # TODO: Review unreachable code - },
        # TODO: Review unreachable code - message=f"Marked {len(valid_paths)} files as '{name}'"
        # TODO: Review unreachable code - )

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

        # TODO: Review unreachable code - # Get selection service
        # TODO: Review unreachable code - selection_service = services.get("selections")

        # TODO: Review unreachable code - # Get selections
        # TODO: Review unreachable code - selections = selection_service.list_selections(
        # TODO: Review unreachable code - tags=tags,
        # TODO: Review unreachable code - limit=limit
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Format selections
        # TODO: Review unreachable code - selection_list = []
        # TODO: Review unreachable code - for selection in selections:
        # TODO: Review unreachable code - data = {
        # TODO: Review unreachable code - "id": selection.id,
        # TODO: Review unreachable code - "name": selection.name,
        # TODO: Review unreachable code - "file_count": len(selection.paths),
        # TODO: Review unreachable code - "tags": selection.tags,
        # TODO: Review unreachable code - "notes": selection.notes,
        # TODO: Review unreachable code - "created_at": selection.created_at.isoformat(),
        # TODO: Review unreachable code - "metadata": selection.metadata
        # TODO: Review unreachable code - }

        # TODO: Review unreachable code - if include_paths:
        # TODO: Review unreachable code - data["paths"] = selection.paths

        # TODO: Review unreachable code - selection_list.append(data)

        # TODO: Review unreachable code - return create_tool_response(
        # TODO: Review unreachable code - success=True,
        # TODO: Review unreachable code - data={
        # TODO: Review unreachable code - "selections": selection_list,
        # TODO: Review unreachable code - "count": len(selection_list),
        # TODO: Review unreachable code - "total_files": sum(s["file_count"] for s in selection_list)
        # TODO: Review unreachable code - }
        # TODO: Review unreachable code - )

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

        # TODO: Review unreachable code - # Get selection service
        # TODO: Review unreachable code - selection_service = services.get("selections")

        # TODO: Review unreachable code - # Get selections to export
        # TODO: Review unreachable code - if selection_id:
        # TODO: Review unreachable code - selection = selection_service.get_selection(selection_id)
        # TODO: Review unreachable code - if not selection:
        # TODO: Review unreachable code - raise ValidationError(f"Selection '{selection_id}' not found")
        # TODO: Review unreachable code - selections = [selection]
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - selections = selection_service.list_selections()

        # TODO: Review unreachable code - if not selections:
        # TODO: Review unreachable code - raise ValidationError("No selections to export")

        # TODO: Review unreachable code - # Determine output path
        # TODO: Review unreachable code - if output_path:
        # TODO: Review unreachable code - output_file = validate_path(output_path, must_exist=False)
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # TODO: Review unreachable code - output_file = Path(f"selections_export_{timestamp}.{format}")

        # TODO: Review unreachable code - # Export based on format
        # TODO: Review unreachable code - if format == "json":
        # TODO: Review unreachable code - export_data = []
        # TODO: Review unreachable code - for sel in selections:
        # TODO: Review unreachable code - export_data.append({
        # TODO: Review unreachable code - "id": sel.id,
        # TODO: Review unreachable code - "name": sel.name,
        # TODO: Review unreachable code - "paths": sel.paths,
        # TODO: Review unreachable code - "tags": sel.tags,
        # TODO: Review unreachable code - "notes": sel.notes,
        # TODO: Review unreachable code - "metadata": sel.metadata,
        # TODO: Review unreachable code - "created_at": sel.created_at.isoformat()
        # TODO: Review unreachable code - })

        # TODO: Review unreachable code - with open(output_file, 'w') as f:
        # TODO: Review unreachable code - json.dump(export_data, f, indent=2)

        # TODO: Review unreachable code - elif format == "txt":
        # TODO: Review unreachable code - lines = []
        # TODO: Review unreachable code - for sel in selections:
        # TODO: Review unreachable code - lines.append(f"# {sel.name}")
        # TODO: Review unreachable code - lines.append(f"Created: {sel.created_at}")
        # TODO: Review unreachable code - if sel.tags:
        # TODO: Review unreachable code - lines.append(f"Tags: {', '.join(sel.tags)}")
        # TODO: Review unreachable code - if sel.notes:
        # TODO: Review unreachable code - lines.append(f"Notes: {sel.notes}")
        # TODO: Review unreachable code - lines.append("Files:")
        # TODO: Review unreachable code - for path in sel.paths:
        # TODO: Review unreachable code - lines.append(f"  - {path}")
        # TODO: Review unreachable code - lines.append("")  # Empty line between selections

        # TODO: Review unreachable code - with open(output_file, 'w') as f:
        # TODO: Review unreachable code - f.write("\n".join(lines))

        # TODO: Review unreachable code - elif format == "csv":
        # TODO: Review unreachable code - import csv

        # TODO: Review unreachable code - with open(output_file, 'w', newline='') as f:
        # TODO: Review unreachable code - writer = csv.writer(f)
        # TODO: Review unreachable code - writer.writerow(["Selection", "File", "Tags", "Notes", "Created"])

        # TODO: Review unreachable code - for sel in selections:
        # TODO: Review unreachable code - tags_str = ", ".join(sel.tags) if sel.tags else ""
        # TODO: Review unreachable code - for path in sel.paths:
        # TODO: Review unreachable code - writer.writerow([
        # TODO: Review unreachable code - sel.name,
        # TODO: Review unreachable code - path,
        # TODO: Review unreachable code - tags_str,
        # TODO: Review unreachable code - sel.notes or "",
        # TODO: Review unreachable code - sel.created_at.isoformat()
        # TODO: Review unreachable code - ])

        # TODO: Review unreachable code - # Get file size
        # TODO: Review unreachable code - file_size = output_file.stat().st_size

        # TODO: Review unreachable code - return create_tool_response(
        # TODO: Review unreachable code - success=True,
        # TODO: Review unreachable code - data={
        # TODO: Review unreachable code - "output_file": str(output_file),
        # TODO: Review unreachable code - "format": format,
        # TODO: Review unreachable code - "selections_exported": len(selections),
        # TODO: Review unreachable code - "total_files": sum(len(s.paths) for s in selections),
        # TODO: Review unreachable code - "file_size": file_size
        # TODO: Review unreachable code - },
        # TODO: Review unreachable code - message=f"Exported {len(selections)} selections to {output_file.name}"
        # TODO: Review unreachable code - )
