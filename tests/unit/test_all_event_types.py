"""Comprehensive tests for all event types to ensure dataclass inheritance works correctly."""

from datetime import datetime

from alicemultiverse.events.asset_events import (
    AssetDiscoveredEvent,
    AssetOrganizedEvent,
    AssetProcessedEvent,
    MetadataUpdatedEvent,
    QualityAssessedEvent,
)
from alicemultiverse.events.creative_events import (
    CharacterDefinedEvent,
    ConceptApprovedEvent,
    ContextUpdatedEvent,
    ProjectCreatedEvent,
    StyleChosenEvent,
)
from alicemultiverse.events.workflow_events import (
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
)


class TestAllEventTypes:
    """Test all event types to ensure they work correctly with dataclass inheritance fix."""

    def test_asset_events(self):
        """Test all asset event types."""
        # AssetDiscoveredEvent
        event = AssetDiscoveredEvent(
            file_path="/path/to/asset.jpg",
            content_hash="abc123",
            file_size=1024,
            media_type="image",
            project_name="test-project",
        )
        assert event.file_path == "/path/to/asset.jpg"
        assert event.file_size == 1024
        assert event.content_hash == "abc123"
        assert event.media_type == "image"
        assert event.project_name == "test-project"
        assert isinstance(event.event_id, str)
        assert isinstance(event.timestamp, datetime)

        # AssetProcessedEvent
        event = AssetProcessedEvent(
            content_hash="abc123",
            file_path="/path/to/asset.jpg",
            metadata={"quality": "high"},
            processor_version="1.0",
        )
        assert event.content_hash == "abc123"
        assert event.file_path == "/path/to/asset.jpg"
        assert event.metadata["quality"] == "high"
        assert event.processor_version == "1.0"

        # AssetOrganizedEvent
        event = AssetOrganizedEvent(
            content_hash="abc123",
            source_path="/inbox/asset.jpg",
            destination_path="/organized/asset.jpg",
            project_name="test-project",
            source_type="stable-diffusion",
            date_folder="2024-01-01",
        )
        assert event.content_hash == "abc123"
        assert event.source_path == "/inbox/asset.jpg"
        assert event.destination_path == "/organized/asset.jpg"
        assert event.project_name == "test-project"
        assert event.source_type == "stable-diffusion"
        assert event.date_folder == "2024-01-01"

        # MetadataUpdatedEvent
        event = MetadataUpdatedEvent(
            content_hash="abc123",
            metadata={"title": "My Photo", "tags": ["portrait"]},
            updated_fields=["title", "tags"],
            update_reason="User edit",
        )
        assert event.content_hash == "abc123"
        assert event.metadata["title"] == "My Photo"
        assert event.metadata["tags"] == ["portrait"]
        assert event.update_reason == "User edit"

        # QualityAssessedEvent
        event = QualityAssessedEvent(
            content_hash="abc123",
            file_path="/path/to/asset.jpg",
            star_rating=5,
            combined_score=0.85,
            brisque_score=15.5,
            pipeline_mode="basic",
        )
        assert event.content_hash == "abc123"
        assert event.file_path == "/path/to/asset.jpg"
        assert event.star_rating == 5
        assert event.combined_score == 0.85
        assert event.brisque_score == 15.5
        assert event.pipeline_mode == "basic"

    def test_creative_events(self):
        """Test all creative event types."""
        # ProjectCreatedEvent
        event = ProjectCreatedEvent(
            project_id="proj-123",
            project_name="My Project",
            description="Test project",
            style_preferences={"style": "photorealistic"},
        )
        assert event.project_id == "proj-123"
        assert event.project_name == "My Project"
        assert event.description == "Test project"
        assert event.style_preferences["style"] == "photorealistic"

        # StyleChosenEvent
        event = StyleChosenEvent(
            project_id="proj-123", style_name="Photorealistic", style_category="realism"
        )
        assert event.project_id == "proj-123"
        assert event.style_name == "Photorealistic"
        assert event.style_category == "realism"

        # ContextUpdatedEvent
        event = ContextUpdatedEvent(
            project_id="proj-123",
            context_type="scene",
            update_type="modify",
            context_key="location",
        )
        assert event.project_id == "proj-123"
        assert event.context_type == "scene"
        assert event.update_type == "modify"
        assert event.context_key == "location"

        # CharacterDefinedEvent
        event = CharacterDefinedEvent(
            project_id="proj-123",
            character_id="char-789",
            character_name="Alice",
            character_type="protagonist",
        )
        assert event.project_id == "proj-123"
        assert event.character_id == "char-789"
        assert event.character_name == "Alice"
        assert event.character_type == "protagonist"

        # ConceptApprovedEvent
        event = ConceptApprovedEvent(
            project_id="proj-123",
            concept_id="concept-789",
            concept_type="character",
            concept_name="Alice Design",
            description="Main character design",
            approved_by="user",
        )
        assert event.project_id == "proj-123"
        assert event.concept_id == "concept-789"
        assert event.concept_type == "character"
        assert event.concept_name == "Alice Design"
        assert event.description == "Main character design"
        assert event.approved_by == "user"

    def test_workflow_events(self):
        """Test all workflow event types."""
        # WorkflowStartedEvent
        event = WorkflowStartedEvent(
            workflow_id="wf-123",
            workflow_type="asset-processing",
            workflow_name="Process Assets",
            input_parameters={"quality": "high"},
            initiated_by="user",
        )
        assert event.workflow_id == "wf-123"
        assert event.workflow_type == "asset-processing"
        assert event.workflow_name == "Process Assets"
        assert event.input_parameters["quality"] == "high"
        assert event.initiated_by == "user"

        # WorkflowStepCompletedEvent
        event = WorkflowStepCompletedEvent(
            workflow_id="wf-123",
            step_id="step-456",
            step_name="quality-check",
            step_number=2,
            total_steps=5,
            status="completed",
        )
        assert event.workflow_id == "wf-123"
        assert event.step_id == "step-456"
        assert event.step_name == "quality-check"
        assert event.step_number == 2
        assert event.total_steps == 5
        assert event.status == "completed"

        # WorkflowCompletedEvent
        event = WorkflowCompletedEvent(
            workflow_id="wf-123",
            workflow_type="asset-processing",
            total_duration_ms=120500,
            steps_completed=5,
        )
        assert event.workflow_id == "wf-123"
        assert event.workflow_type == "asset-processing"
        assert event.total_duration_ms == 120500
        assert event.steps_completed == 5

        # WorkflowFailedEvent
        event = WorkflowFailedEvent(
            workflow_id="wf-123",
            workflow_type="asset-processing",
            error_type="ProcessingError",
            error_message="Processing failed at quality check",
        )
        assert event.workflow_id == "wf-123"
        assert event.workflow_type == "asset-processing"
        assert event.error_type == "ProcessingError"
        assert event.error_message == "Processing failed at quality check"

    def test_event_metadata(self):
        """Test that all events have proper metadata fields."""
        event = AssetDiscoveredEvent(
            file_path="/path/to/asset.jpg",
            content_hash="abc123",
            file_size=1024,
            media_type="image",
            project_name="test-project",
        )

        # Check metadata fields
        assert hasattr(event, "event_id")
        assert hasattr(event, "event_type")
        assert hasattr(event, "timestamp")
        assert hasattr(event, "version")
        assert hasattr(event, "source")

        # Check default values
        assert event.version == "1.0.0"
        assert event.event_type == "asset.discovered"
        assert event.source == ""

    def test_event_serialization(self):
        """Test that all events can be properly serialized."""
        events = [
            AssetDiscoveredEvent(
                file_path="/test.jpg",
                content_hash="abc",
                file_size=1024,
                media_type="image",
                project_name="test",
            ),
            ProjectCreatedEvent(project_id="p1", project_name="Test", description="Desc"),
            WorkflowStartedEvent(
                workflow_id="w1", workflow_type="test", workflow_name="Test WF", initiated_by="user"
            ),
            MetadataUpdatedEvent(content_hash="abc123", metadata={"test": "data"}),
            CharacterDefinedEvent(
                project_id="p1", character_id="c1", character_name="Alice", character_type="main"
            ),
            WorkflowCompletedEvent(
                workflow_id="w1", workflow_type="test", total_duration_ms=10000, steps_completed=3
            ),
        ]

        for event in events:
            # Test to_dict
            data = event.to_dict()
            assert isinstance(data, dict)
            assert "event_id" in data
            assert "event_type" in data
            assert "timestamp" in data
            # In v2, fields are flattened, not nested under 'data'
            assert "file_path" in data or "project_id" in data or "workflow_id" in data

            # Test from_dict if available
            if hasattr(event.__class__, "from_dict"):
                reconstructed = event.__class__.from_dict(data)
                # Event ID might be regenerated, so just check it exists
                assert reconstructed.event_id
                assert reconstructed.event_type == event.event_type

    def test_event_type_names(self):
        """Test that event types have correct naming."""
        event_type_map = {
            AssetDiscoveredEvent: "asset.discovered",
            AssetProcessedEvent: "asset.processed",
            AssetOrganizedEvent: "asset.organized",
            QualityAssessedEvent: "quality.assessed",
            MetadataUpdatedEvent: "metadata.updated",
            ProjectCreatedEvent: "project.created",
            StyleChosenEvent: "style.chosen",
            ContextUpdatedEvent: "context.updated",
            CharacterDefinedEvent: "character.defined",
            ConceptApprovedEvent: "concept.approved",
            WorkflowStartedEvent: "workflow.started",
            WorkflowStepCompletedEvent: "workflow.step_completed",
            WorkflowCompletedEvent: "workflow.completed",
            WorkflowFailedEvent: "workflow.failed",
        }

        for event_class, expected_type in event_type_map.items():
            # Create minimal instance with required fields
            if event_class == AssetDiscoveredEvent:
                event = event_class(
                    file_path="/test",
                    file_size=1,
                    content_hash="abc",
                    media_type="image",
                    project_name="test",
                )
            elif event_class == AssetProcessedEvent:
                event = event_class(content_hash="abc", file_path="/f")
            elif event_class == AssetOrganizedEvent:
                event = event_class(
                    content_hash="abc",
                    source_path="/s",
                    destination_path="/d",
                    project_name="p",
                    source_type="st",
                    date_folder="2024-01-01",
                )
            elif event_class == QualityAssessedEvent:
                event = event_class(
                    content_hash="abc", file_path="/f", star_rating=4, combined_score=0.75
                )
            elif event_class == MetadataUpdatedEvent:
                event = event_class(content_hash="abc")
            elif event_class == ProjectCreatedEvent:
                event = event_class(project_id="p1", project_name="n")
            elif event_class == StyleChosenEvent:
                event = event_class(project_id="p1", style_name="n", style_category="c")
            elif event_class == ContextUpdatedEvent:
                event = event_class(
                    project_id="p1", context_type="t", update_type="u", context_key="k"
                )
            elif event_class == CharacterDefinedEvent:
                event = event_class(
                    project_id="p1", character_id="c1", character_name="n", character_type="t"
                )
            elif event_class == ConceptApprovedEvent:
                event = event_class(
                    project_id="p1",
                    concept_id="c1",
                    concept_type="t",
                    concept_name="n",
                    description="d",
                    approved_by="u",
                )
            elif event_class == WorkflowStartedEvent:
                event = event_class(workflow_id="w1", workflow_type="t", workflow_name="n")
            elif event_class == WorkflowStepCompletedEvent:
                event = event_class(
                    workflow_id="w1",
                    step_id="s1",
                    step_name="s",
                    step_number=1,
                    total_steps=3,
                    status="ok",
                )
            elif event_class == WorkflowCompletedEvent:
                event = event_class(
                    workflow_id="w1", workflow_type="t", total_duration_ms=1000, steps_completed=3
                )
            elif event_class == WorkflowFailedEvent:
                event = event_class(
                    workflow_id="w1", workflow_type="t", error_type="e", error_message="msg"
                )

            assert event.event_type == expected_type
