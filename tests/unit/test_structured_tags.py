"""Test structured key:value tag functionality."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

from alicemultiverse.database.models import Asset, Tag
from alicemultiverse.database.repository import AssetRepository
from alicemultiverse.interface.alice_interface import AliceInterface


class TestStructuredTags:
    """Test the key:value tag implementation."""
    
    def test_search_with_structured_tags_any_mode(self, mock_db_session):
        """Test searching with structured tags in 'any' mode (OR logic)."""
        # Create test assets with different tags
        asset1 = Asset(
            content_hash="hash1",
            file_path="/test/asset1.png",
            media_type="image",
            source_type="midjourney"
        )
        asset2 = Asset(
            content_hash="hash2", 
            file_path="/test/asset2.png",
            media_type="image",
            source_type="flux"
        )
        asset3 = Asset(
            content_hash="hash3",
            file_path="/test/asset3.png", 
            media_type="image",
            source_type="stablediffusion"
        )
        
        # Add tags
        tag1_style = Tag(asset_id="hash1", tag_type="style", tag_value="cyberpunk", source="user")
        tag1_mood = Tag(asset_id="hash1", tag_type="mood", tag_value="dark", source="user")
        tag2_style = Tag(asset_id="hash2", tag_type="style", tag_value="anime", source="user")
        tag2_mood = Tag(asset_id="hash2", tag_type="mood", tag_value="bright", source="user")
        tag3_style = Tag(asset_id="hash3", tag_type="style", tag_value="cyberpunk", source="user")
        tag3_mood = Tag(asset_id="hash3", tag_type="mood", tag_value="bright", source="user")
        
        mock_db_session.add_all([asset1, asset2, asset3])
        mock_db_session.add_all([tag1_style, tag1_mood, tag2_style, tag2_mood, tag3_style, tag3_mood])
        mock_db_session.commit()
        
        @contextmanager
        def mock_get_session():
            yield mock_db_session
            
        with patch('alicemultiverse.database.repository.get_session', mock_get_session):
            repo = AssetRepository()
            
            # Search for cyberpunk OR dark (should find asset1 and asset3)
            results = repo.search(
                tags={"style": ["cyberpunk"], "mood": ["dark"]},
                tag_mode="any"
            )
            assert len(results) == 2
            assert set(a.content_hash for a in results) == {"hash1", "hash3"}
            
            # Search for anime style (should find only asset2)
            results = repo.search(
                tags={"style": ["anime"]},
                tag_mode="any"
            )
            assert len(results) == 1
            assert results[0].content_hash == "hash2"
    
    def test_search_with_structured_tags_all_mode(self, mock_db_session):
        """Test searching with structured tags in 'all' mode (AND logic)."""
        # Create test assets
        asset1 = Asset(
            content_hash="hash1",
            file_path="/test/asset1.png",
            media_type="image",
            source_type="midjourney"
        )
        asset2 = Asset(
            content_hash="hash2",
            file_path="/test/asset2.png",
            media_type="image", 
            source_type="flux"
        )
        
        # Asset1 has both cyberpunk style AND dark mood
        tag1_style = Tag(asset_id="hash1", tag_type="style", tag_value="cyberpunk", source="user")
        tag1_mood = Tag(asset_id="hash1", tag_type="mood", tag_value="dark", source="user")
        
        # Asset2 has cyberpunk style but bright mood
        tag2_style = Tag(asset_id="hash2", tag_type="style", tag_value="cyberpunk", source="user")
        tag2_mood = Tag(asset_id="hash2", tag_type="mood", tag_value="bright", source="user")
        
        mock_db_session.add_all([asset1, asset2])
        mock_db_session.add_all([tag1_style, tag1_mood, tag2_style, tag2_mood])
        mock_db_session.commit()
        
        @contextmanager
        def mock_get_session():
            yield mock_db_session
            
        with patch('alicemultiverse.database.repository.get_session', mock_get_session):
            repo = AssetRepository()
            
            # Search for cyberpunk AND dark (should find only asset1)
            results = repo.search(
                tags={"style": ["cyberpunk"], "mood": ["dark"]},
                tag_mode="all"
            )
            assert len(results) == 1
            assert results[0].content_hash == "hash1"
            
            # Search for cyberpunk AND bright (should find only asset2)
            results = repo.search(
                tags={"style": ["cyberpunk"], "mood": ["bright"]},
                tag_mode="all"
            )
            assert len(results) == 1
            assert results[0].content_hash == "hash2"
    
    def test_alice_interface_structured_tag_search(self, tmp_path):
        """Test Alice interface search with structured tags."""
        # Mock the asset repository
        mock_repo = MagicMock()
        mock_assets = [
            Asset(
                content_hash="hash1",
                file_path="/test/asset1.png",
                media_type="image",
                source_type="midjourney",
                embedded_metadata={"prompt": "cyberpunk city at night"}
            )
        ]
        mock_repo.search.return_value = mock_assets
        
        # Create Alice interface with mocked repository
        alice = AliceInterface()
        alice.asset_repo = mock_repo
        alice.initialization_error = None  # Ensure no init error
        
        # Search with structured tags
        response = alice.search_assets({
            "style_tags": ["cyberpunk", "neon"],
            "mood_tags": ["dark", "mysterious"],
            "tag_mode": "all",
            "limit": 10
        })
        
        # Verify the repository was called with structured format
        mock_repo.search.assert_called_once_with(
            tags={
                "style": ["cyberpunk", "neon"],
                "mood": ["dark", "mysterious"]
            },
            tag_mode="all",
            source_type=None,
            min_rating=None,
            role=None,
            limit=10
        )
        
        assert response["success"] is True
        assert len(response["data"]) == 1
        assert response["data"][0]["id"] == "hash1"
    
    def test_alice_interface_tag_assets_structured(self, tmp_path):
        """Test Alice interface tagging with structured tags."""
        # Mock the asset repository
        mock_repo = MagicMock()
        mock_repo.add_tag.return_value = True
        
        # Create Alice interface with mocked repository  
        alice = AliceInterface()
        alice.asset_repo = mock_repo
        alice.initialization_error = None
        
        # Tag assets with structured format
        response = alice.tag_assets({
            "asset_ids": ["hash1", "hash2"],
            "tags": {
                "style": ["cyberpunk", "neon"],
                "mood": ["dark"],
                "subject": ["city", "night"]
            }
        })
        
        # Verify all tags were added correctly
        assert mock_repo.add_tag.call_count == 10  # 2 assets * 5 total tag values
        
        # Check specific calls
        expected_calls = []
        for asset_id in ["hash1", "hash2"]:
            expected_calls.extend([
                (asset_id, "style", "cyberpunk", "ai"),
                (asset_id, "style", "neon", "ai"),
                (asset_id, "mood", "dark", "ai"),
                (asset_id, "subject", "city", "ai"),
                (asset_id, "subject", "night", "ai")
            ])
        
        actual_calls = [
            (call[1]["content_hash"], call[1]["tag_type"], call[1]["tag_value"], call[1]["source"])
            for call in mock_repo.add_tag.call_args_list
        ]
        
        assert set(actual_calls) == set(expected_calls)
        assert response["success"] is True
        assert response["data"]["tagged_count"] == 2
    
    def test_backward_compatibility_flat_tags(self, mock_db_session):
        """Test that flat tag lists still work for backward compatibility."""
        asset = Asset(
            content_hash="hash1",
            file_path="/test/asset1.png",
            media_type="image",
            source_type="midjourney"
        )
        
        # Add tags without type specification
        tag1 = Tag(asset_id="hash1", tag_type="custom", tag_value="cyberpunk", source="user")
        tag2 = Tag(asset_id="hash1", tag_type="custom", tag_value="neon", source="user")
        
        mock_db_session.add(asset)
        mock_db_session.add_all([tag1, tag2])
        mock_db_session.commit()
        
        @contextmanager
        def mock_get_session():
            yield mock_db_session
            
        with patch('alicemultiverse.database.repository.get_session', mock_get_session):
            repo = AssetRepository()
            
            # Search with flat tag list
            results = repo.search(tags=["cyberpunk", "neon"])
            assert len(results) == 1
            assert results[0].content_hash == "hash1"


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from alicemultiverse.database.models import Base
    
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()