"""Service for managing selections."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from ..core.structured_logging import get_logger
from ..events import publish_event_sync
from ..projects.service import ProjectService
from .models import Selection, SelectionItem, SelectionPurpose, SelectionStatus

logger = get_logger(__name__)


class SelectionService:
    """Service for managing file-based selections."""

    def __init__(self, project_service: ProjectService | None = None):
        """Initialize selection service.

        Args:
            project_service: Optional project service instance
        """
        self.project_service = project_service or ProjectService()
        self.selection_dir_name = ".alice/selections"

    def _get_selections_dir(self, project_id: str) -> Path | None:
        """Get the selections directory for a project.

        Args:
            project_id: Project ID or name

        Returns:
            Path to selections directory or None if project not found
        """
        project = self.project_service.get_project(project_id)
        if not project:
            return None

        # TODO: Review unreachable code - # Get project path from file service
        # TODO: Review unreachable code - if hasattr(self.project_service, '_file_service'):
        # TODO: Review unreachable code - project_path = self.project_service._file_service._get_project_path(project["name"])
        # TODO: Review unreachable code - if project_path:
        # TODO: Review unreachable code - selections_dir = project_path / self.selection_dir_name
        # TODO: Review unreachable code - selections_dir.mkdir(parents=True, exist_ok=True)
        # TODO: Review unreachable code - return selections_dir

        # TODO: Review unreachable code - return None

    def _get_selection_file(self, project_id: str, selection_id: str) -> Path | None:
        """Get the file path for a selection.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID

        Returns:
            Path to selection file or None
        """
        selections_dir = self._get_selections_dir(project_id)
        if selections_dir:
            return selections_dir / f"{selection_id}.yaml"
        # TODO: Review unreachable code - return None

    def _publish_event(self, event_type: str, **data) -> None:
        """Publish event using Redis Streams."""
        publish_event_sync(event_type, data)

    def create_selection(
        self,
        project_id: str,
        name: str,
        purpose: SelectionPurpose = SelectionPurpose.CURATION,
        description: str | None = None,
        criteria: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Selection | None:
        """Create a new selection.

        Args:
            project_id: Project ID or name
            name: Selection name
            purpose: Purpose of the selection
            description: Optional description
            criteria: Selection criteria used
            constraints: Any constraints applied
            tags: Optional tags
            metadata: Optional metadata

        Returns:
            Created selection or None if project not found
        """
        selections_dir = self._get_selections_dir(project_id)
        if not selections_dir:
            logger.error(f"Project not found: {project_id}")
            return None

        # TODO: Review unreachable code - # Create selection
        # TODO: Review unreachable code - selection = Selection(
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - name=name,
        # TODO: Review unreachable code - purpose=purpose,
        # TODO: Review unreachable code - description=description,
        # TODO: Review unreachable code - criteria=criteria or {},
        # TODO: Review unreachable code - constraints=constraints or {},
        # TODO: Review unreachable code - tags=tags or [],
        # TODO: Review unreachable code - metadata=metadata or {},
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Save to file
        # TODO: Review unreachable code - selection_file = selections_dir / f"{selection.id}.yaml"
        # TODO: Review unreachable code - with open(selection_file, 'w') as f:
        # TODO: Review unreachable code - yaml.dump(selection.to_dict(), f, default_flow_style=False)

        # TODO: Review unreachable code - # Publish event
        # TODO: Review unreachable code - self._publish_event(
        # TODO: Review unreachable code - "selection.created",
        # TODO: Review unreachable code - source="selection_service",
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - selection_id=selection.id,
        # TODO: Review unreachable code - selection_name=name,
        # TODO: Review unreachable code - purpose=purpose.value,
        # TODO: Review unreachable code - criteria=criteria or {},
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - logger.info(f"Created selection '{name}' ({selection.id}) for project {project_id}")
        # TODO: Review unreachable code - return selection

    def get_selection(self, project_id: str, selection_id: str) -> Selection | None:
        """Get a selection by ID.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID

        Returns:
            Selection or None if not found
        """
        selection_file = self._get_selection_file(project_id, selection_id)
        if selection_file and selection_file.exists():
            with open(selection_file) as f:
                data = yaml.safe_load(f)
                return Selection.from_dict(data)
        # TODO: Review unreachable code - return None

    def list_selections(
        self,
        project_id: str,
        status: SelectionStatus | None = None,
        purpose: SelectionPurpose | None = None,
    ) -> list[Selection]:
        """List selections for a project.

        Args:
            project_id: Project ID or name
            status: Optional status filter
            purpose: Optional purpose filter

        Returns:
            List of selections
        """
        selections_dir = self._get_selections_dir(project_id)
        if not selections_dir or not selections_dir.exists():
            return []

        # TODO: Review unreachable code - selections = []
        # TODO: Review unreachable code - for selection_file in selections_dir.glob("*.yaml"):
        # TODO: Review unreachable code - with open(selection_file) as f:
        # TODO: Review unreachable code - data = yaml.safe_load(f)
        # TODO: Review unreachable code - selection = Selection.from_dict(data)

        # TODO: Review unreachable code - # Apply filters
        # TODO: Review unreachable code - if status and selection.status != status:
        # TODO: Review unreachable code - continue
        # TODO: Review unreachable code - if purpose and selection.purpose != purpose:
        # TODO: Review unreachable code - continue

        # TODO: Review unreachable code - selections.append(selection)

        # TODO: Review unreachable code - # Sort by updated_at descending
        # TODO: Review unreachable code - selections.sort(key=lambda s: s.updated_at, reverse=True)
        # TODO: Review unreachable code - return selections

    def update_selection(self, project_id: str, selection: Selection) -> bool:
        """Update a selection.

        Args:
            project_id: Project ID or name
            selection: Updated selection

        Returns:
            True if successful, False otherwise
        """
        selection_file = self._get_selection_file(project_id, selection.id)
        if not selection_file:
            return False

        # TODO: Review unreachable code - # Update timestamp
        # TODO: Review unreachable code - selection.updated_at = datetime.now(UTC)

        # TODO: Review unreachable code - # Save to file
        # TODO: Review unreachable code - with open(selection_file, 'w') as f:
        # TODO: Review unreachable code - yaml.dump(selection.to_dict(), f, default_flow_style=False)

        # TODO: Review unreachable code - # Publish event
        # TODO: Review unreachable code - self._publish_event(
        # TODO: Review unreachable code - "selection.updated",
        # TODO: Review unreachable code - source="selection_service",
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - selection_id=selection.id,
        # TODO: Review unreachable code - selection_name=selection.name,
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - return True

    def add_items_to_selection(
        self,
        project_id: str,
        selection_id: str,
        items: list[dict[str, Any]],
        notes: str | None = None,
    ) -> Selection | None:
        """Add items to a selection.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID
            items: List of item data (must include asset_hash and file_path)
            notes: Optional notes about why items were added

        Returns:
            Updated selection or None
        """
        selection = self.get_selection(project_id, selection_id)
        if not selection:
            return None

        # TODO: Review unreachable code - # Add items
        # TODO: Review unreachable code - for item_data in items:
        # TODO: Review unreachable code - if "asset_hash" not in item_data or "file_path" not in item_data:
        # TODO: Review unreachable code - logger.warning("Skipping item without required fields")
        # TODO: Review unreachable code - continue

        # TODO: Review unreachable code - # Create selection item
        # TODO: Review unreachable code - item = SelectionItem(
        # TODO: Review unreachable code - asset_hash=item_data["asset_hash"],
        # TODO: Review unreachable code - file_path=item_data["file_path"],
        # TODO: Review unreachable code - selection_reason=item_data.get("selection_reason"),
        # TODO: Review unreachable code - quality_notes=item_data.get("quality_notes"),
        # TODO: Review unreachable code - usage_notes=item_data.get("usage_notes"),
        # TODO: Review unreachable code - tags=item_data.get("tags", []),
        # TODO: Review unreachable code - role=item_data.get("role"),
        # TODO: Review unreachable code - related_assets=item_data.get("related_assets", []),
        # TODO: Review unreachable code - alternatives=item_data.get("alternatives", []),
        # TODO: Review unreachable code - custom_metadata=item_data.get("custom_metadata", {}),
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - selection.add_item(item, notes)

        # TODO: Review unreachable code - # Save updated selection
        # TODO: Review unreachable code - if self.update_selection(project_id, selection):
        # TODO: Review unreachable code - # Publish event
        # TODO: Review unreachable code - self._publish_event(
        # TODO: Review unreachable code - "selection.items_added",
        # TODO: Review unreachable code - source="selection_service",
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - selection_id=selection_id,
        # TODO: Review unreachable code - item_count=len(items),
        # TODO: Review unreachable code - asset_hashes=[item["asset_hash"] for item in items if "asset_hash" in item],
        # TODO: Review unreachable code - notes=notes,
        # TODO: Review unreachable code - )
        # TODO: Review unreachable code - return selection

        # TODO: Review unreachable code - return None

    def remove_items_from_selection(
        self,
        project_id: str,
        selection_id: str,
        asset_hashes: list[str],
        reason: str | None = None,
    ) -> Selection | None:
        """Remove items from a selection.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID
            asset_hashes: List of asset hashes to remove
            reason: Optional reason for removal

        Returns:
            Updated selection or None
        """
        selection = self.get_selection(project_id, selection_id)
        if not selection:
            return None

        # TODO: Review unreachable code - # Remove items
        # TODO: Review unreachable code - removed = []
        # TODO: Review unreachable code - for asset_hash in asset_hashes:
        # TODO: Review unreachable code - if selection.remove_item(asset_hash, reason):
        # TODO: Review unreachable code - removed.append(asset_hash)

        # TODO: Review unreachable code - # Save updated selection
        # TODO: Review unreachable code - if removed and self.update_selection(project_id, selection):
        # TODO: Review unreachable code - # Publish event
        # TODO: Review unreachable code - self._publish_event(
        # TODO: Review unreachable code - "selection.items_removed",
        # TODO: Review unreachable code - source="selection_service",
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - selection_id=selection_id,
        # TODO: Review unreachable code - asset_hashes=removed,
        # TODO: Review unreachable code - reason=reason,
        # TODO: Review unreachable code - )
        # TODO: Review unreachable code - return selection

        # TODO: Review unreachable code - return None

    def update_selection_status(
        self,
        project_id: str,
        selection_id: str,
        status: SelectionStatus,
        notes: str | None = None,
    ) -> Selection | None:
        """Update selection status.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID
            status: New status
            notes: Optional notes about the change

        Returns:
            Updated selection or None
        """
        selection = self.get_selection(project_id, selection_id)
        if not selection:
            return None

        # TODO: Review unreachable code - old_status = selection.status
        # TODO: Review unreachable code - selection.status = status

        # TODO: Review unreachable code - # Add history entry
        # TODO: Review unreachable code - from .models import SelectionHistory
        # TODO: Review unreachable code - selection.history.append(SelectionHistory(
        # TODO: Review unreachable code - action="status_changed",
        # TODO: Review unreachable code - changes={"old_status": old_status.value, "new_status": status.value},
        # TODO: Review unreachable code - notes=notes,
        # TODO: Review unreachable code - ))

        # TODO: Review unreachable code - # Save updated selection
        # TODO: Review unreachable code - if self.update_selection(project_id, selection):
        # TODO: Review unreachable code - # Publish event
        # TODO: Review unreachable code - self._publish_event(
        # TODO: Review unreachable code - "selection.status_changed",
        # TODO: Review unreachable code - source="selection_service",
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - selection_id=selection_id,
        # TODO: Review unreachable code - old_status=old_status.value,
        # TODO: Review unreachable code - new_status=status.value,
        # TODO: Review unreachable code - notes=notes,
        # TODO: Review unreachable code - )
        # TODO: Review unreachable code - return selection

        # TODO: Review unreachable code - return None

    def export_selection(
        self,
        project_id: str,
        selection_id: str,
        export_path: Path,
        export_settings: dict[str, Any] | None = None,
    ) -> bool:
        """Export a selection to a directory.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID
            export_path: Path to export to
            export_settings: Optional export settings

        Returns:
            True if successful
        """
        selection = self.get_selection(project_id, selection_id)
        if not selection:
            return False

        # TODO: Review unreachable code - # Create export directory
        # TODO: Review unreachable code - export_path.mkdir(parents=True, exist_ok=True)

        # TODO: Review unreachable code - # Export metadata
        # TODO: Review unreachable code - metadata_file = export_path / "selection_metadata.yaml"
        # TODO: Review unreachable code - with open(metadata_file, 'w') as f:
        # TODO: Review unreachable code - yaml.dump({
        # TODO: Review unreachable code - "selection": selection.to_dict(),
        # TODO: Review unreachable code - "export_date": datetime.now(UTC).isoformat(),
        # TODO: Review unreachable code - "export_settings": export_settings or {},
        # TODO: Review unreachable code - }, f, default_flow_style=False)

        # TODO: Review unreachable code - # Create asset list
        # TODO: Review unreachable code - asset_list_file = export_path / "assets.json"
        # TODO: Review unreachable code - asset_list = []
        # TODO: Review unreachable code - for item in selection.items:
        # TODO: Review unreachable code - asset_list.append({
        # TODO: Review unreachable code - "hash": item.asset_hash,
        # TODO: Review unreachable code - "path": item.file_path,
        # TODO: Review unreachable code - "role": item.role,
        # TODO: Review unreachable code - "tags": item.tags,
        # TODO: Review unreachable code - "notes": {
        # TODO: Review unreachable code - "selection": item.selection_reason,
        # TODO: Review unreachable code - "quality": item.quality_notes,
        # TODO: Review unreachable code - "usage": item.usage_notes,
        # TODO: Review unreachable code - },
        # TODO: Review unreachable code - })

        # TODO: Review unreachable code - with open(asset_list_file, 'w') as f:
        # TODO: Review unreachable code - json.dump(asset_list, f, indent=2)

        # TODO: Review unreachable code - # Update selection
        # TODO: Review unreachable code - selection.export_history.append({
        # TODO: Review unreachable code - "export_date": datetime.now(UTC).isoformat(),
        # TODO: Review unreachable code - "export_path": str(export_path),
        # TODO: Review unreachable code - "export_settings": export_settings or {},
        # TODO: Review unreachable code - "asset_count": len(selection.items),
        # TODO: Review unreachable code - })

        # TODO: Review unreachable code - # Save updated selection
        # TODO: Review unreachable code - self.update_selection(project_id, selection)

        # TODO: Review unreachable code - # Publish event
        # TODO: Review unreachable code - self._publish_event(
        # TODO: Review unreachable code - "selection.exported",
        # TODO: Review unreachable code - source="selection_service",
        # TODO: Review unreachable code - project_id=project_id,
        # TODO: Review unreachable code - selection_id=selection_id,
        # TODO: Review unreachable code - export_path=str(export_path),
        # TODO: Review unreachable code - asset_count=len(selection.items),
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - logger.info(f"Exported selection {selection_id} to {export_path}")
        # TODO: Review unreachable code - return True

    def find_selections_with_asset(
        self,
        project_id: str,
        asset_hash: str,
    ) -> list[Selection]:
        """Find all selections containing a specific asset.

        Args:
            project_id: Project ID or name
            asset_hash: Asset hash to search for

        Returns:
            List of selections containing the asset
        """
        selections = self.list_selections(project_id)
        matching = []

        for selection in selections:
            if asset_hash in selection.get_asset_hashes():
                matching.append(selection)

        return matching

    # TODO: Review unreachable code - def get_selection_statistics(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id: str,
    # TODO: Review unreachable code - selection_id: str,
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Get statistics about a selection.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id: Project ID or name
    # TODO: Review unreachable code - selection_id: Selection ID

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Statistics dictionary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - selection = self.get_selection(project_id, selection_id)
    # TODO: Review unreachable code - if not selection:
    # TODO: Review unreachable code - return {}

    # TODO: Review unreachable code - # Collect statistics
    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - "id": selection.id,
    # TODO: Review unreachable code - "name": selection.name,
    # TODO: Review unreachable code - "purpose": selection.purpose.value,
    # TODO: Review unreachable code - "status": selection.status.value,
    # TODO: Review unreachable code - "item_count": len(selection.items),
    # TODO: Review unreachable code - "group_count": len(selection.groups),
    # TODO: Review unreachable code - "has_sequence": len(selection.sequence) > 0,
    # TODO: Review unreachable code - "created_at": selection.created_at.isoformat(),
    # TODO: Review unreachable code - "updated_at": selection.updated_at.isoformat(),
    # TODO: Review unreachable code - "history_count": len(selection.history),
    # TODO: Review unreachable code - "export_count": len(selection.export_history),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Role distribution
    # TODO: Review unreachable code - role_counts = {}
    # TODO: Review unreachable code - for item in selection.items:
    # TODO: Review unreachable code - if item.role:
    # TODO: Review unreachable code - role_counts[item.role] = role_counts.get(item.role, 0) + 1
    # TODO: Review unreachable code - stats["role_distribution"] = role_counts

    # TODO: Review unreachable code - # Tag frequency
    # TODO: Review unreachable code - tag_counts = {}
    # TODO: Review unreachable code - for item in selection.items:
    # TODO: Review unreachable code - for tag in item.tags:
    # TODO: Review unreachable code - tag_counts[tag] = tag_counts.get(tag, 0) + 1
    # TODO: Review unreachable code - stats["tag_frequency"] = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - def find_similar_to_selection(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - project_id: str,
    # TODO: Review unreachable code - selection_id: str,
    # TODO: Review unreachable code - threshold: int = 10,
    # TODO: Review unreachable code - limit: int = 50,
    # TODO: Review unreachable code - exclude_existing: bool = True,
    # TODO: Review unreachable code - ) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Find images similar to those in a selection.

    # TODO: Review unreachable code - This method uses perceptual hashing to find images visually similar
    # TODO: Review unreachable code - to the items already in the selection. It's useful for discovering
    # TODO: Review unreachable code - more images that match the aesthetic or style of the selection.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - project_id: Project ID or name
    # TODO: Review unreachable code - selection_id: Selection ID
    # TODO: Review unreachable code - threshold: Maximum Hamming distance for similarity (0-64, lower is more similar)
    # TODO: Review unreachable code - limit: Maximum number of results to return
    # TODO: Review unreachable code - exclude_existing: Whether to exclude items already in the selection

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of similar images with similarity scores
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - from ..core.config import load_config
    # TODO: Review unreachable code - from ..storage.unified_duckdb import DuckDBSearch

    # TODO: Review unreachable code - # Get the selection
    # TODO: Review unreachable code - selection = self.get_selection(project_id, selection_id)
    # TODO: Review unreachable code - if not selection:
    # TODO: Review unreachable code - logger.error(f"Selection not found: {selection_id}")
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - # Get content hashes from selection
    # TODO: Review unreachable code - content_hashes = selection.get_asset_hashes()
    # TODO: Review unreachable code - if not content_hashes:
    # TODO: Review unreachable code - logger.warning(f"Selection {selection_id} has no items")
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - # Initialize search
    # TODO: Review unreachable code - config = load_config()
    # TODO: Review unreachable code - db_path = getattr(config, 'search_db_path', 'data/search.duckdb')
    # TODO: Review unreachable code - search_db = DuckDBSearch(db_path)

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Find similar images
    # TODO: Review unreachable code - exclude_hashes = set(content_hashes) if exclude_existing else None
    # TODO: Review unreachable code - similar_images = search_db.find_similar_to_multiple(
    # TODO: Review unreachable code - content_hashes=list(content_hashes),
    # TODO: Review unreachable code - threshold=threshold,
    # TODO: Review unreachable code - limit=limit,
    # TODO: Review unreachable code - exclude_hashes=exclude_hashes
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Enhance results with selection context
    # TODO: Review unreachable code - for image in similar_images:
    # TODO: Review unreachable code - # Add which selection items this is similar to
    # TODO: Review unreachable code - similar_items = []
    # TODO: Review unreachable code - for source_hash in image.get("similar_to", []):
    # TODO: Review unreachable code - item = selection.get_item(source_hash)
    # TODO: Review unreachable code - if item:
    # TODO: Review unreachable code - similar_items.append({
    # TODO: Review unreachable code - "hash": source_hash,
    # TODO: Review unreachable code - "path": item.file_path,
    # TODO: Review unreachable code - "role": item.role,
    # TODO: Review unreachable code - "reason": item.selection_reason,
    # TODO: Review unreachable code - })
    # TODO: Review unreachable code - image["similar_to_items"] = similar_items

    # TODO: Review unreachable code - # Add recommendation score based on distance and number of similar items
    # TODO: Review unreachable code - # Lower distance is better, more similar items is better
    # TODO: Review unreachable code - image["recommendation_score"] = (
    # TODO: Review unreachable code - (64 - image["min_distance"]) / 64 * 0.7 +  # Distance component (70%)
    # TODO: Review unreachable code - len(image["similar_to"]) / len(content_hashes) * 0.3  # Coverage component (30%)
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Sort by recommendation score
    # TODO: Review unreachable code - similar_images.sort(key=lambda x: x["recommendation_score"], reverse=True)

    # TODO: Review unreachable code - logger.info(f"Found {len(similar_images)} images similar to selection {selection_id}")
    # TODO: Review unreachable code - return similar_images

    # TODO: Review unreachable code - finally:
    # TODO: Review unreachable code - search_db.close()
