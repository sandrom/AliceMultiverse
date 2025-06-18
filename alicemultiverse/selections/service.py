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

        # Get project path from file service
        if hasattr(self.project_service, '_file_service'):
            project_path = self.project_service._file_service._get_project_path(project["name"])
            if project_path:
                selections_dir = project_path / self.selection_dir_name
                selections_dir.mkdir(parents=True, exist_ok=True)
                return selections_dir

        return None

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
        return None

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

        # Create selection
        selection = Selection(
            project_id=project_id,
            name=name,
            purpose=purpose,
            description=description,
            criteria=criteria or {},
            constraints=constraints or {},
            tags=tags or [],
            metadata=metadata or {},
        )

        # Save to file
        selection_file = selections_dir / f"{selection.id}.yaml"
        with open(selection_file, 'w') as f:
            yaml.dump(selection.to_dict(), f, default_flow_style=False)

        # Publish event
        self._publish_event(
            "selection.created",
            source="selection_service",
            project_id=project_id,
            selection_id=selection.id,
            selection_name=name,
            purpose=purpose.value,
            criteria=criteria or {},
        )

        logger.info(f"Created selection '{name}' ({selection.id}) for project {project_id}")
        return selection

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
        return None

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

        selections = []
        for selection_file in selections_dir.glob("*.yaml"):
            with open(selection_file) as f:
                data = yaml.safe_load(f)
                selection = Selection.from_dict(data)

                # Apply filters
                if status and selection.status != status:
                    continue
                if purpose and selection.purpose != purpose:
                    continue

                selections.append(selection)

        # Sort by updated_at descending
        selections.sort(key=lambda s: s.updated_at, reverse=True)
        return selections

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

        # Update timestamp
        selection.updated_at = datetime.now(UTC)

        # Save to file
        with open(selection_file, 'w') as f:
            yaml.dump(selection.to_dict(), f, default_flow_style=False)

        # Publish event
        self._publish_event(
            "selection.updated",
            source="selection_service",
            project_id=project_id,
            selection_id=selection.id,
            selection_name=selection.name,
        )

        return True

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

        # Add items
        for item_data in items:
            if "asset_hash" not in item_data or "file_path" not in item_data:
                logger.warning("Skipping item without required fields")
                continue

            # Create selection item
            item = SelectionItem(
                asset_hash=item_data["asset_hash"],
                file_path=item_data["file_path"],
                selection_reason=item_data.get("selection_reason"),
                quality_notes=item_data.get("quality_notes"),
                usage_notes=item_data.get("usage_notes"),
                tags=item_data.get("tags", []),
                role=item_data.get("role"),
                related_assets=item_data.get("related_assets", []),
                alternatives=item_data.get("alternatives", []),
                custom_metadata=item_data.get("custom_metadata", {}),
            )

            selection.add_item(item, notes)

        # Save updated selection
        if self.update_selection(project_id, selection):
            # Publish event
            self._publish_event(
                "selection.items_added",
                source="selection_service",
                project_id=project_id,
                selection_id=selection_id,
                item_count=len(items),
                asset_hashes=[item["asset_hash"] for item in items if "asset_hash" in item],
                notes=notes,
            )
            return selection

        return None

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

        # Remove items
        removed = []
        for asset_hash in asset_hashes:
            if selection.remove_item(asset_hash, reason):
                removed.append(asset_hash)

        # Save updated selection
        if removed and self.update_selection(project_id, selection):
            # Publish event
            self._publish_event(
                "selection.items_removed",
                source="selection_service",
                project_id=project_id,
                selection_id=selection_id,
                asset_hashes=removed,
                reason=reason,
            )
            return selection

        return None

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

        old_status = selection.status
        selection.status = status

        # Add history entry
        from .models import SelectionHistory
        selection.history.append(SelectionHistory(
            action="status_changed",
            changes={"old_status": old_status.value, "new_status": status.value},
            notes=notes,
        ))

        # Save updated selection
        if self.update_selection(project_id, selection):
            # Publish event
            self._publish_event(
                "selection.status_changed",
                source="selection_service",
                project_id=project_id,
                selection_id=selection_id,
                old_status=old_status.value,
                new_status=status.value,
                notes=notes,
            )
            return selection

        return None

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

        # Create export directory
        export_path.mkdir(parents=True, exist_ok=True)

        # Export metadata
        metadata_file = export_path / "selection_metadata.yaml"
        with open(metadata_file, 'w') as f:
            yaml.dump({
                "selection": selection.to_dict(),
                "export_date": datetime.now(UTC).isoformat(),
                "export_settings": export_settings or {},
            }, f, default_flow_style=False)

        # Create asset list
        asset_list_file = export_path / "assets.json"
        asset_list = []
        for item in selection.items:
            asset_list.append({
                "hash": item.asset_hash,
                "path": item.file_path,
                "role": item.role,
                "tags": item.tags,
                "notes": {
                    "selection": item.selection_reason,
                    "quality": item.quality_notes,
                    "usage": item.usage_notes,
                },
            })

        with open(asset_list_file, 'w') as f:
            json.dump(asset_list, f, indent=2)

        # Update selection
        selection.export_history.append({
            "export_date": datetime.now(UTC).isoformat(),
            "export_path": str(export_path),
            "export_settings": export_settings or {},
            "asset_count": len(selection.items),
        })

        # Save updated selection
        self.update_selection(project_id, selection)

        # Publish event
        self._publish_event(
            "selection.exported",
            source="selection_service",
            project_id=project_id,
            selection_id=selection_id,
            export_path=str(export_path),
            asset_count=len(selection.items),
        )

        logger.info(f"Exported selection {selection_id} to {export_path}")
        return True

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

    def get_selection_statistics(
        self,
        project_id: str,
        selection_id: str,
    ) -> dict[str, Any]:
        """Get statistics about a selection.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID

        Returns:
            Statistics dictionary
        """
        selection = self.get_selection(project_id, selection_id)
        if not selection:
            return {}

        # Collect statistics
        stats = {
            "id": selection.id,
            "name": selection.name,
            "purpose": selection.purpose.value,
            "status": selection.status.value,
            "item_count": len(selection.items),
            "group_count": len(selection.groups),
            "has_sequence": len(selection.sequence) > 0,
            "created_at": selection.created_at.isoformat(),
            "updated_at": selection.updated_at.isoformat(),
            "history_count": len(selection.history),
            "export_count": len(selection.export_history),
        }

        # Role distribution
        role_counts = {}
        for item in selection.items:
            if item.role:
                role_counts[item.role] = role_counts.get(item.role, 0) + 1
        stats["role_distribution"] = role_counts

        # Tag frequency
        tag_counts = {}
        for item in selection.items:
            for tag in item.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        stats["tag_frequency"] = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        return stats

    def find_similar_to_selection(
        self,
        project_id: str,
        selection_id: str,
        threshold: int = 10,
        limit: int = 50,
        exclude_existing: bool = True,
    ) -> list[dict[str, Any]]:
        """Find images similar to those in a selection.

        This method uses perceptual hashing to find images visually similar
        to the items already in the selection. It's useful for discovering
        more images that match the aesthetic or style of the selection.

        Args:
            project_id: Project ID or name
            selection_id: Selection ID
            threshold: Maximum Hamming distance for similarity (0-64, lower is more similar)
            limit: Maximum number of results to return
            exclude_existing: Whether to exclude items already in the selection

        Returns:
            List of similar images with similarity scores
        """
        from ..core.config import load_config
        from ..storage.unified_duckdb import DuckDBSearch

        # Get the selection
        selection = self.get_selection(project_id, selection_id)
        if not selection:
            logger.error(f"Selection not found: {selection_id}")
            return []

        # Get content hashes from selection
        content_hashes = selection.get_asset_hashes()
        if not content_hashes:
            logger.warning(f"Selection {selection_id} has no items")
            return []

        # Initialize search
        config = load_config()
        db_path = getattr(config, 'search_db_path', 'data/search.duckdb')
        search_db = DuckDBSearch(db_path)

        try:
            # Find similar images
            exclude_hashes = set(content_hashes) if exclude_existing else None
            similar_images = search_db.find_similar_to_multiple(
                content_hashes=list(content_hashes),
                threshold=threshold,
                limit=limit,
                exclude_hashes=exclude_hashes
            )

            # Enhance results with selection context
            for image in similar_images:
                # Add which selection items this is similar to
                similar_items = []
                for source_hash in image.get("similar_to", []):
                    item = selection.get_item(source_hash)
                    if item:
                        similar_items.append({
                            "hash": source_hash,
                            "path": item.file_path,
                            "role": item.role,
                            "reason": item.selection_reason,
                        })
                image["similar_to_items"] = similar_items

                # Add recommendation score based on distance and number of similar items
                # Lower distance is better, more similar items is better
                image["recommendation_score"] = (
                    (64 - image["min_distance"]) / 64 * 0.7 +  # Distance component (70%)
                    len(image["similar_to"]) / len(content_hashes) * 0.3  # Coverage component (30%)
                )

            # Sort by recommendation score
            similar_images.sort(key=lambda x: x["recommendation_score"], reverse=True)

            logger.info(f"Found {len(similar_images)} images similar to selection {selection_id}")
            return similar_images

        finally:
            search_db.close()
