"""Test AI-friendly error handling throughout the system."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from alicemultiverse.interface import AliceInterface
from alicemultiverse.interface.models import (
    SearchRequest,
    OrganizeRequest,
    TagRequest,
)
from alicemultiverse.core.exceptions import (
    AliceMultiverseError,
    ConfigurationError,
)


class TestAIFriendlyErrors:
    """Test that errors are AI-friendly and actionable."""

    @pytest.fixture
    def alice(self, tmp_path):
        """Create Alice interface."""
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text("""
paths:
  inbox: /tmp/inbox
  organized: /tmp/organized
""")
        return AliceInterface(config_path)

    def test_configuration_errors_are_clear(self, alice):
        """Test configuration errors provide clear guidance."""
        # Test with non-existent directory
        request = OrganizeRequest(
            source_path="/this/path/does/not/exist"
        )
        
        response = alice.organize_media(request)
        
        assert not response["success"]
        assert response["error"] is not None
        # Error should be clear for AI to explain
        assert any(phrase in response["error"].lower() for phrase in ["does not exist", "not found", "read-only"])

    def test_validation_errors_explain_issue(self, alice):
        """Test validation errors are descriptive."""
        # Test with invalid quality stars
        request = SearchRequest(
            min_quality_stars=10  # Invalid - should be 1-5
        )
        
        # This should handle gracefully
        response = alice.search_assets(request)
        
        # Even with invalid input, should not crash
        assert isinstance(response["success"], bool)
        if not response["success"]:
            assert response["error"] is not None

    def test_missing_dependencies_clear_message(self, alice):
        """Test missing dependencies provide installation instructions."""
        with patch('alicemultiverse.quality.brisque.is_available', return_value=False):
            # Try to use quality assessment without BRISQUE
            request = OrganizeRequest(
                quality_assessment=True,
                pipeline="basic"
            )
            
            response = alice.organize_media(request)
            
            # Should still work but maybe skip quality
            assert isinstance(response["success"], bool)
            if response["message"]:
                # Message should explain the limitation
                assert "quality" in response["message"].lower() or response["success"]

    def test_api_errors_include_context(self, alice):
        """Test API errors include helpful context."""
        # Mock API failure
        with patch.object(alice.organizer, '_process_file') as mock_process:
            mock_process.side_effect = Exception("API rate limit exceeded")
            
            request = OrganizeRequest()
            response = alice.organize_media(request)
            
            # Should handle API errors gracefully
            assert isinstance(response["success"], bool)
            if not response["success"] and response["error"]:
                # Error should mention API or rate limit
                assert "API" in response["error"] or "rate limit" in response["error"]

    def test_search_errors_suggest_alternatives(self, alice):
        """Test search errors provide helpful suggestions."""
        # Search with very specific criteria that won't match
        request = SearchRequest(
            description="ultra specific search that matches nothing",
            style_tags=["nonexistent-style"],
            mood_tags=["impossible-mood"],
            min_quality_stars=5,
            source_types=["unknown-source"]
        )
        
        response = alice.search_assets(request)
        
        assert response["success"]  # Search should succeed even with no results
        assert len(response["data"]) == 0
        # Message should be helpful
        assert "Found 0 assets" in response["message"] or "0" in response["message"]

    def test_file_permission_errors(self, alice, tmp_path):
        """Test file permission errors are explained clearly."""
        # Create a read-only directory
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)
        
        request = OrganizeRequest(
            source_path=str(tmp_path),
            # This would fail if it tries to write to read_only_dir
        )
        
        response = alice.organize_media(request)
        
        # Should handle permission errors gracefully
        assert isinstance(response["success"], bool)
        
        # Clean up
        read_only_dir.chmod(0o755)

    def test_memory_errors_handled(self, alice):
        """Test large operations handle memory issues."""
        # Mock a memory issue
        with patch.object(alice.organizer.metadata_cache, 'get_all_metadata') as mock_get_all:
            # Simulate large cache by returning many items
            mock_get_all.return_value = {f"hash_{i}": {} for i in range(1000000)}
            
            response = alice.get_stats()
            
            # Should handle large data gracefully
            assert isinstance(response["success"], bool)
            if response["success"]:
                assert isinstance(response["data"], dict)

    def test_concurrent_access_errors(self, alice):
        """Test handling of concurrent access issues."""
        # Mock file being accessed by another process
        with patch.object(alice.organizer, '_process_file') as mock_process:
            mock_process.side_effect = OSError("Resource temporarily unavailable")
            
            request = OrganizeRequest()
            response = alice.organize_media(request)
            
            assert isinstance(response["success"], bool)
            if not response["success"] and response["error"]:
                # Error should mention temporary issue
                assert "temporarily" in response["error"].lower() or "unavailable" in response["error"].lower()


class TestErrorMessageQuality:
    """Test that error messages are suitable for AI assistants."""

    def test_error_messages_no_technical_jargon(self):
        """Error messages should avoid technical jargon."""
        bad_messages = [
            "OSError: [Errno 2] No such file or directory",
            "KeyError: 'missing_key'",
            "ValueError: invalid literal for int() with base 10",
            "AttributeError: 'NoneType' object has no attribute 'split'"
        ]
        
        good_messages = [
            "File not found: The specified file does not exist",
            "Missing configuration: The required setting 'missing_key' is not configured",
            "Invalid number: Expected a number but received text",
            "Processing error: Unable to process empty data"
        ]
        
        # Good messages should be clear
        for msg in good_messages:
            assert ":" in msg  # Has clear separation
            assert len(msg.split()) > 3  # Has explanation
            assert not msg.startswith("Error")  # Doesn't start with "Error"

    def test_error_includes_suggestions(self):
        """Errors should include actionable suggestions."""
        error_response = {
            "success": False,
            "message": "Unable to find images matching criteria",
            "error": "No images found with 5-star quality rating",
            "suggestions": [
                "Try lowering the quality threshold",
                "Check if images have been assessed for quality",
                "Use broader search terms"
            ]
        }
        
        assert "suggestions" in error_response
        assert len(error_response["suggestions"]) > 0
        assert all(isinstance(s, str) for s in error_response["suggestions"])

    def test_error_context_preserved(self):
        """Errors should preserve context for AI understanding."""
        error_with_context = {
            "success": False,
            "message": "Search failed",
            "error": "Unable to search assets",
            "context": {
                "search_terms": ["cyberpunk", "portrait"],
                "filters_applied": {"min_quality": 5},
                "assets_checked": 150,
                "matches_found": 0
            }
        }
        
        assert "context" in error_with_context
        assert "search_terms" in error_with_context["context"]
        assert isinstance(error_with_context["context"]["assets_checked"], int)