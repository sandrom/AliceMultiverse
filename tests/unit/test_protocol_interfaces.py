"""Tests for Protocol interfaces functionality."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from alicemultiverse.core.protocols import (
    HasConfig,
    HasOrganizer,
    HasStats,
    HasSearchDB,
)

if TYPE_CHECKING:
    from alicemultiverse.core.config import Config
    from alicemultiverse.core.statistics import Statistics
    from alicemultiverse.storage.duckdb_search import DuckDBSearch
    from alicemultiverse.organizer.components.organizer import MediaOrganizer


class TestProtocolInterfaces:
    """Test that Protocol interfaces work correctly."""
    
    def test_has_config_protocol(self):
        """Test HasConfig protocol."""
        
        class ConfigurableComponent:
            """Component that implements HasConfig."""
            def __init__(self):
                self.config = MagicMock()
        
        component = ConfigurableComponent()
        
        # Should satisfy HasConfig protocol
        assert hasattr(component, 'config')
        
        # Test using the protocol
        def process_with_config(obj: HasConfig) -> str:
            """Function that requires HasConfig."""
            return f"Config exists: {obj.config is not None}"
        
        result = process_with_config(component)
        assert result == "Config exists: True"
    
    def test_has_stats_protocol(self):
        """Test HasStats protocol."""
        
        class StatTracker:
            """Component that implements HasStats."""
            def __init__(self):
                self.stats = {
                    "processed": 0,
                    "errors": 0,
                    "skipped": 0
                }
        
        tracker = StatTracker()
        
        # Should satisfy HasStats protocol
        assert hasattr(tracker, 'stats')
        
        # Test using the protocol
        def update_stats(obj: HasStats) -> None:
            """Function that requires HasStats."""
            obj.stats["processed"] += 1
        
        update_stats(tracker)
        assert tracker.stats["processed"] == 1
    
    def test_has_search_db_protocol(self):
        """Test HasSearchDB protocol."""
        
        class StorageComponent:
            """Component that implements HasSearchDB."""
            def __init__(self):
                self.search_db = MagicMock()
                self.search_db.search_by_text = MagicMock(return_value=[])
        
        component = StorageComponent()
        
        # Should satisfy HasSearchDB protocol
        assert hasattr(component, 'search_db')
        
        # Test using the protocol
        def search_in_storage(obj: HasSearchDB, query: str) -> list:
            """Function that requires HasSearchDB."""
            return obj.search_db.search_by_text(query)
        
        results = search_in_storage(component, "test query")
        assert results == []
        component.search_db.search_by_text.assert_called_once_with("test query")
    
    def test_has_organizer_protocol(self):
        """Test HasOrganizer protocol."""
        
        class OrganizerComponent:
            """Component that implements HasOrganizer."""
            def __init__(self):
                self.organizer = MagicMock()
                self.organizer.organize = MagicMock(return_value={"status": "success"})
        
        component = OrganizerComponent()
        
        # Should satisfy HasOrganizer protocol
        assert hasattr(component, 'organizer')
        
        # Test using the protocol
        def organize_with_protocol(obj: HasOrganizer) -> dict:
            """Function that requires HasOrganizer."""
            return obj.organizer.organize()
        
        result = organize_with_protocol(component)
        
        assert result["status"] == "success"
        component.organizer.organize.assert_called_once()
    
    def test_multiple_protocols(self):
        """Test a class implementing multiple protocols."""
        
        class MultiProtocolComponent:
            """Component implementing multiple protocols."""
            def __init__(self):
                # HasConfig
                self.config = MagicMock()
                # HasStats
                self.stats = {"total": 0}
                # HasStorage
                self.search_db = MagicMock()
        
        component = MultiProtocolComponent()
        
        # Test function requiring multiple protocols
        def complex_operation(obj: HasConfig & HasStats & HasSearchDB) -> dict:
            """Function requiring multiple protocols."""
            return {
                "has_config": obj.config is not None,
                "stats_total": obj.stats.get("total", 0),
                "has_storage": obj.search_db is not None
            }
        
        result = complex_operation(component)
        
        assert result["has_config"] is True
        assert result["stats_total"] == 0
        assert result["has_storage"] is True
    
    def test_protocol_with_mixins(self):
        """Test protocols work with mixin classes."""
        
        class ConfigMixin:
            """Mixin providing config."""
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.config = MagicMock()
        
        class StatsMixin:
            """Mixin providing stats."""
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.stats = {"count": 0}
        
        class CombinedComponent(ConfigMixin, StatsMixin):
            """Component using mixins."""
            pass
        
        component = CombinedComponent()
        
        # Should satisfy both protocols
        def use_protocols(obj: HasConfig & HasStats) -> bool:
            """Use both protocols."""
            return obj.config is not None and "count" in obj.stats
        
        assert use_protocols(component) is True
    
    def test_protocol_type_checking(self):
        """Test protocol type checking with actual type annotations."""
        
        class TypedComponent:
            """Component with proper type annotations."""
            def __init__(self):
                from alicemultiverse.core.config import Config
                from alicemultiverse.core.statistics import Statistics
                
                self.config: Config = MagicMock(spec=Config)
                self.stats: Statistics = MagicMock(spec=Statistics)
        
        component = TypedComponent()
        
        # Type checking should work properly
        def strictly_typed_function(obj: HasConfig) -> None:
            """Function with strict typing."""
            # In runtime, we just check the attribute exists
            assert hasattr(obj, 'config')
            # Type checker would verify config is correct type
        
        strictly_typed_function(component)
    
    def test_protocol_inheritance(self):
        """Test protocol inheritance patterns."""
        
        class BaseComponent:
            """Base component with some protocol attributes."""
            def __init__(self):
                self.config = MagicMock()
        
        class ExtendedComponent(BaseComponent):
            """Extended component adding more protocol attributes."""
            def __init__(self):
                super().__init__()
                self.stats = {"extended": True}
        
        base = BaseComponent()
        extended = ExtendedComponent()
        
        # Base satisfies HasConfig
        def needs_config(obj: HasConfig) -> bool:
            return obj.config is not None
        
        assert needs_config(base) is True
        assert needs_config(extended) is True
        
        # Extended satisfies both HasConfig and HasStats
        def needs_both(obj: HasConfig & HasStats) -> bool:
            return obj.config is not None and obj.stats is not None
        
        # This would fail for base (no stats attribute)
        # But works for extended
        assert needs_both(extended) is True
    
    def test_optional_protocol_attributes(self):
        """Test handling of optional protocol attributes."""
        
        class ComponentWithOptionalDB:
            """Component with optional search DB."""
            def __init__(self):
                self.search_db = None  # Optional
        
        component = ComponentWithOptionalDB()
        
        # Test handling optional attributes
        def handle_optional_db(obj: HasSearchDB) -> str:
            """Handle optional search DB."""
            if obj.search_db is not None:
                return "Database available"
            else:
                return "Database not available"
        
        result = handle_optional_db(component)
        assert result == "Database not available"
        
        # Add database
        component.search_db = MagicMock()
        
        result = handle_optional_db(component)
        assert result == "Database available"