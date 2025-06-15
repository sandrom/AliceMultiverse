"""Unit tests for the selection tracking system."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from alicemultiverse.selections.models import (
    Selection,
    SelectionItem,
    SelectionPurpose,
    SelectionStatus,
)
from alicemultiverse.selections.service import SelectionService


class TestSelectionModels:
    """Test selection model classes."""

    def test_selection_item_creation(self):
        """Test creating a selection item."""
        item = SelectionItem(
            asset_hash="abc123",
            file_path="/path/to/asset.png",
            selection_reason="Great composition",
            quality_notes="High resolution",
            usage_notes="Hero image",
            tags=["hero", "landscape"],
            role="hero"
        )

        assert item.asset_hash == "abc123"
        assert item.file_path == "/path/to/asset.png"
        assert item.selection_reason == "Great composition"
        assert item.role == "hero"
        assert "hero" in item.tags
        assert isinstance(item.added_at, datetime)

    def test_selection_item_serialization(self):
        """Test serializing selection item to/from dict."""
        item = SelectionItem(
            asset_hash="abc123",
            file_path="/path/to/asset.png",
            selection_reason="Test reason",
            tags=["test"],
            related_assets=["def456"],
            custom_metadata={"key": "value"}
        )

        # Convert to dict
        item_dict = item.to_dict()
        assert item_dict["asset_hash"] == "abc123"
        assert item_dict["tags"] == ["test"]
        assert item_dict["custom_metadata"] == {"key": "value"}
        assert isinstance(item_dict["added_at"], str)

        # Convert back from dict
        item2 = SelectionItem.from_dict(item_dict)
        assert item2.asset_hash == item.asset_hash
        assert item2.tags == item.tags
        assert isinstance(item2.added_at, datetime)

    def test_selection_creation(self):
        """Test creating a selection."""
        selection = Selection(
            project_id="test-project",
            name="Test Selection",
            purpose=SelectionPurpose.PORTFOLIO,
            description="Test description",
            criteria={"quality": "high"},
            tags=["test", "portfolio"]
        )

        assert selection.project_id == "test-project"
        assert selection.name == "Test Selection"
        assert selection.purpose == SelectionPurpose.PORTFOLIO
        assert selection.status == SelectionStatus.DRAFT
        assert len(selection.items) == 0
        assert len(selection.history) == 0

    def test_selection_add_remove_items(self):
        """Test adding and removing items from selection."""
        selection = Selection(
            project_id="test-project",
            name="Test Selection"
        )

        # Add item
        item = SelectionItem(
            asset_hash="abc123",
            file_path="/path/to/asset.png",
            selection_reason="Test"
        )
        selection.add_item(item, notes="Adding first item")

        assert len(selection.items) == 1
        assert len(selection.history) == 1
        assert selection.history[0].action == "added"
        assert selection.history[0].asset_hashes == ["abc123"]

        # Get item
        retrieved = selection.get_item("abc123")
        assert retrieved is not None
        assert retrieved.asset_hash == "abc123"

        # Remove item
        success = selection.remove_item("abc123", reason="No longer needed")
        assert success
        assert len(selection.items) == 0
        assert len(selection.history) == 2
        assert selection.history[1].action == "removed"

    def test_selection_grouping_and_sequencing(self):
        """Test grouping and sequencing items."""
        selection = Selection(
            project_id="test-project",
            name="Test Selection"
        )

        # Add multiple items
        for i in range(3):
            item = SelectionItem(
                asset_hash=f"hash{i}",
                file_path=f"/path/to/asset{i}.png"
            )
            selection.add_item(item)

        # Group items
        selection.group_items("nature", ["hash0", "hash1"])
        assert "nature" in selection.groups
        assert len(selection.groups["nature"]) == 2

        # Set sequence
        selection.set_sequence(["hash2", "hash0", "hash1"])
        assert selection.sequence == ["hash2", "hash0", "hash1"]
        assert selection.get_item("hash2").sequence_order == 0
        assert selection.get_item("hash0").sequence_order == 1

    def test_selection_serialization(self):
        """Test serializing selection to/from dict."""
        selection = Selection(
            project_id="test-project",
            name="Test Selection",
            purpose=SelectionPurpose.PRESENTATION,
            status=SelectionStatus.ACTIVE
        )

        # Add an item
        item = SelectionItem(
            asset_hash="abc123",
            file_path="/path/to/asset.png"
        )
        selection.add_item(item)

        # Convert to dict
        sel_dict = selection.to_dict()
        assert sel_dict["name"] == "Test Selection"
        assert sel_dict["purpose"] == "presentation"
        assert sel_dict["status"] == "active"
        assert len(sel_dict["items"]) == 1
        assert len(sel_dict["history"]) == 1

        # Convert back from dict
        selection2 = Selection.from_dict(sel_dict)
        assert selection2.name == selection.name
        assert selection2.purpose == selection.purpose
        assert selection2.status == selection.status
        assert len(selection2.items) == 1
        assert len(selection2.history) == 1


class TestSelectionService:
    """Test selection service functionality."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test-project"
            project_dir.mkdir()

            # Create project.yaml
            project_data = {
                "id": "test-project-id",
                "name": "test-project",
                "status": "active",
                "created_at": datetime.now(UTC).isoformat()
            }
            with open(project_dir / "project.yaml", "w") as f:
                yaml.dump(project_data, f)

            # Create .alice directory
            (project_dir / ".alice").mkdir()

            yield project_dir

    @pytest.fixture
    def mock_project_service(self, temp_project_dir):
        """Create a mock project service."""
        from alicemultiverse.projects.service import ProjectService

        service = MagicMock(spec=ProjectService)
        service.get_project.return_value = {
            "id": "test-project-id",
            "name": "test-project"
        }
        # Mock the file service inside
        service._file_service = MagicMock()
        service._file_service._get_project_path.return_value = temp_project_dir
        return service

    @pytest.fixture
    def selection_service(self, mock_project_service):
        """Create a selection service with mocked dependencies."""
        # Mock the event publishing to avoid Redis dependency
        with patch("alicemultiverse.selections.service.publish_event_sync") as mock_publish:
            mock_publish.return_value = None
            service = SelectionService(project_service=mock_project_service)
            yield service

    def test_create_selection(self, selection_service, temp_project_dir):
        """Test creating a selection."""
        selection = selection_service.create_selection(
            project_id="test-project",
            name="Test Selection",
            purpose=SelectionPurpose.CURATION,
            description="Test description",
            criteria={"quality": "high"},
            tags=["test"]
        )

        assert selection is not None
        assert selection.name == "Test Selection"
        assert selection.purpose == SelectionPurpose.CURATION
        assert selection.description == "Test description"

        # Check file was created
        selections_dir = temp_project_dir / ".alice/selections"
        assert selections_dir.exists()
        selection_files = list(selections_dir.glob("*.yaml"))
        assert len(selection_files) == 1

    def test_get_selection(self, selection_service):
        """Test getting a selection."""
        # Create a selection first
        created = selection_service.create_selection(
            project_id="test-project",
            name="Test Selection"
        )

        # Get it back
        retrieved = selection_service.get_selection("test-project", created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_list_selections(self, selection_service):
        """Test listing selections."""
        # Create multiple selections
        for i in range(3):
            selection_service.create_selection(
                project_id="test-project",
                name=f"Selection {i}",
                purpose=SelectionPurpose.CURATION if i < 2 else SelectionPurpose.EXPORT
            )

        # List all
        all_selections = selection_service.list_selections("test-project")
        assert len(all_selections) == 3

        # List by purpose
        curation_selections = selection_service.list_selections(
            "test-project",
            purpose=SelectionPurpose.CURATION
        )
        assert len(curation_selections) == 2

    def test_add_remove_items(self, selection_service):
        """Test adding and removing items from selection."""
        # Create selection
        selection = selection_service.create_selection(
            project_id="test-project",
            name="Test Selection"
        )

        # Add items
        items = [
            {
                "asset_hash": "hash1",
                "file_path": "/path/1.png",
                "selection_reason": "Reason 1"
            },
            {
                "asset_hash": "hash2",
                "file_path": "/path/2.png",
                "selection_reason": "Reason 2"
            }
        ]

        updated = selection_service.add_items_to_selection(
            project_id="test-project",
            selection_id=selection.id,
            items=items,
            notes="Adding test items"
        )

        assert updated is not None
        assert len(updated.items) == 2

        # Remove one item
        updated = selection_service.remove_items_from_selection(
            project_id="test-project",
            selection_id=selection.id,
            asset_hashes=["hash1"],
            reason="No longer needed"
        )

        assert updated is not None
        assert len(updated.items) == 1
        assert updated.items[0].asset_hash == "hash2"

    def test_update_selection_status(self, selection_service):
        """Test updating selection status."""
        # Create selection
        selection = selection_service.create_selection(
            project_id="test-project",
            name="Test Selection"
        )

        assert selection.status == SelectionStatus.DRAFT

        # Update status
        updated = selection_service.update_selection_status(
            project_id="test-project",
            selection_id=selection.id,
            status=SelectionStatus.ACTIVE,
            notes="Ready for use"
        )

        assert updated is not None
        assert updated.status == SelectionStatus.ACTIVE
        assert len(updated.history) > 0

    def test_export_selection(self, selection_service, tmp_path):
        """Test exporting a selection."""
        # Create selection with items
        selection = selection_service.create_selection(
            project_id="test-project",
            name="Test Selection"
        )

        items = [
            {
                "asset_hash": "hash1",
                "file_path": "/path/1.png",
                "selection_reason": "Test reason",
                "tags": ["test"],
                "role": "hero"
            }
        ]

        selection_service.add_items_to_selection(
            project_id="test-project",
            selection_id=selection.id,
            items=items
        )

        # Export
        export_path = tmp_path / "export"
        success = selection_service.export_selection(
            project_id="test-project",
            selection_id=selection.id,
            export_path=export_path,
            export_settings={"format": "high_quality"}
        )

        assert success
        assert export_path.exists()
        assert (export_path / "selection_metadata.yaml").exists()
        assert (export_path / "assets.json").exists()

        # Check exported data
        with open(export_path / "assets.json") as f:
            assets = json.load(f)
            assert len(assets) == 1
            assert assets[0]["hash"] == "hash1"
            assert assets[0]["role"] == "hero"

    def test_find_selections_with_asset(self, selection_service):
        """Test finding selections containing a specific asset."""
        # Create multiple selections
        sel1 = selection_service.create_selection(
            project_id="test-project",
            name="Selection 1"
        )
        sel2 = selection_service.create_selection(
            project_id="test-project",
            name="Selection 2"
        )

        # Add same asset to first selection
        items = [{"asset_hash": "shared-hash", "file_path": "/path/shared.png"}]
        selection_service.add_items_to_selection(
            project_id="test-project",
            selection_id=sel1.id,
            items=items
        )

        # Find selections with asset
        matches = selection_service.find_selections_with_asset(
            project_id="test-project",
            asset_hash="shared-hash"
        )

        assert len(matches) == 1
        assert matches[0].id == sel1.id

    def test_selection_statistics(self, selection_service):
        """Test getting selection statistics."""
        # Create selection with various items
        selection = selection_service.create_selection(
            project_id="test-project",
            name="Test Selection"
        )

        items = [
            {
                "asset_hash": f"hash{i}",
                "file_path": f"/path/{i}.png",
                "role": "hero" if i == 0 else "supporting",
                "tags": ["landscape", "nature"] if i < 2 else ["portrait"]
            }
            for i in range(3)
        ]

        selection_service.add_items_to_selection(
            project_id="test-project",
            selection_id=selection.id,
            items=items
        )

        # Get statistics
        stats = selection_service.get_selection_statistics(
            project_id="test-project",
            selection_id=selection.id
        )

        assert stats["item_count"] == 3
        assert stats["role_distribution"]["hero"] == 1
        assert stats["role_distribution"]["supporting"] == 2
        assert "landscape" in stats["tag_frequency"]
        assert stats["tag_frequency"]["landscape"] == 2
