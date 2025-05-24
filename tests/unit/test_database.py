"""Tests for database components."""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alicemultiverse.database.models import Base, Asset, Project, AssetPath, Tag, AssetRelationship
from alicemultiverse.database.repository import AssetRepository, ProjectRepository
from alicemultiverse.assets.hashing import calculate_content_hash


class TestDatabaseModels:
    """Test SQLAlchemy models."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_project_model(self, db_session):
        """Test Project model."""
        project = Project(
            name="Test Project",
            description="A test project",
            creative_context={'style': 'cyberpunk'},
            settings={'quality': 'high'}
        )
        
        db_session.add(project)
        db_session.commit()
        
        # Query back
        loaded = db_session.query(Project).filter_by(name="Test Project").first()
        assert loaded is not None
        assert loaded.name == "Test Project"
        assert loaded.creative_context['style'] == 'cyberpunk'
        assert loaded.id is not None
    
    def test_asset_model(self, db_session):
        """Test Asset model."""
        # Create project first
        project = Project(name="Test Project")
        db_session.add(project)
        db_session.commit()
        
        # Create asset
        asset = Asset(
            content_hash="abc123def456",
            file_path="/test/image.png",
            project_id=project.id,
            media_type="image",
            file_size=1000000,
            width=1920,
            height=1080,
            source_type="midjourney",
            created_by="ai",
            generation_params={'prompt': 'test image'},
            rating=5
        )
        
        db_session.add(asset)
        db_session.commit()
        
        # Query back
        loaded = db_session.query(Asset).filter_by(content_hash="abc123def456").first()
        assert loaded is not None
        assert loaded.media_type == "image"
        assert loaded.source_type == "midjourney"
        assert loaded.generation_params['prompt'] == 'test image'
        assert loaded.project.name == "Test Project"
    
    def test_asset_paths(self, db_session):
        """Test AssetPath tracking."""
        # Create asset
        asset = Asset(
            content_hash="abc123",
            file_path="/original/path.png",
            media_type="image",
            file_size=1000
        )
        db_session.add(asset)
        db_session.commit()
        
        # Add path history
        path1 = AssetPath(
            content_hash="abc123",
            file_path="/original/path.png",
            is_active=False
        )
        path2 = AssetPath(
            content_hash="abc123",
            file_path="/new/location/path.png",
            is_active=True
        )
        
        db_session.add_all([path1, path2])
        db_session.commit()
        
        # Check relationships
        asset = db_session.query(Asset).filter_by(content_hash="abc123").first()
        assert len(asset.known_paths) == 2
        active_paths = [p for p in asset.known_paths if p.is_active]
        assert len(active_paths) == 1
        assert active_paths[0].file_path == "/new/location/path.png"
    
    def test_tags(self, db_session):
        """Test Tag model."""
        # Create asset
        asset = Asset(
            content_hash="abc123",
            file_path="/test.png",
            media_type="image",
            file_size=1000
        )
        db_session.add(asset)
        db_session.commit()
        
        # Add tags
        tags = [
            Tag(asset_id="abc123", tag_type="style", tag_value="cyberpunk", source="user"),
            Tag(asset_id="abc123", tag_type="mood", tag_value="dark", source="ai", confidence=0.85),
            Tag(asset_id="abc123", tag_type="color", tag_value="neon", source="auto")
        ]
        
        db_session.add_all(tags)
        db_session.commit()
        
        # Query back
        asset = db_session.query(Asset).filter_by(content_hash="abc123").first()
        assert len(asset.tags) == 3
        
        style_tags = [t for t in asset.tags if t.tag_type == "style"]
        assert len(style_tags) == 1
        assert style_tags[0].tag_value == "cyberpunk"
    
    def test_asset_relationships(self, db_session):
        """Test AssetRelationship model."""
        # Create parent and child assets
        parent = Asset(content_hash="parent123", file_path="/parent.png", 
                      media_type="image", file_size=1000)
        child = Asset(content_hash="child456", file_path="/child.png",
                     media_type="image", file_size=1000)
        
        db_session.add_all([parent, child])
        db_session.commit()
        
        # Create relationship
        rel = AssetRelationship(
            parent_id="parent123",
            child_id="child456",
            relationship_type="variation",
            extra_data={'variation_type': 'color'}
        )
        
        db_session.add(rel)
        db_session.commit()
        
        # Check relationships
        parent = db_session.query(Asset).filter_by(content_hash="parent123").first()
        assert len(parent.child_relationships) == 1
        assert parent.child_relationships[0].child.content_hash == "child456"
        
        child = db_session.query(Asset).filter_by(content_hash="child456").first()
        assert len(child.parent_relationships) == 1
        assert child.parent_relationships[0].parent.content_hash == "parent123"


class TestAssetRepository:
    """Test AssetRepository functionality."""
    
    @pytest.fixture
    def repo(self, db_session):
        """Create repository with session."""
        return AssetRepository(db_session)
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_create_asset(self, repo, db_session):
        """Test creating an asset."""
        asset = repo.create_or_update_asset(
            content_hash="test123",
            file_path="/test/image.png",
            media_type="image",
            file_size=1000,
            source_type="midjourney"
        )
        
        assert asset is not None
        assert asset.content_hash == "test123"
        assert asset.source_type == "midjourney"
        
        # Verify in database
        loaded = db_session.query(Asset).filter_by(content_hash="test123").first()
        assert loaded is not None
    
    def test_update_asset(self, repo, db_session):
        """Test updating an existing asset."""
        # Create initial
        asset1 = repo.create_or_update_asset(
            content_hash="test123",
            file_path="/old/path.png",
            media_type="image",
            file_size=1000
        )
        
        # Update with new path
        asset2 = repo.create_or_update_asset(
            content_hash="test123",
            file_path="/new/path.png",
            media_type="image",
            file_size=1000
        )
        
        assert asset1.content_hash == asset2.content_hash
        assert asset2.file_path == "/new/path.png"
        
        # Should only be one asset
        count = db_session.query(Asset).filter_by(content_hash="test123").count()
        assert count == 1
    
    def test_search_by_tags(self, repo, db_session):
        """Test searching by tags."""
        # Create assets with tags
        asset1 = Asset(
            content_hash="asset1",
            file_path="/1.png",
            media_type="image",
            file_size=1000
        )
        asset2 = Asset(
            content_hash="asset2",
            file_path="/2.png",
            media_type="image",
            file_size=1000
        )
        
        db_session.add_all([asset1, asset2])
        db_session.commit()
        
        # Add tags
        db_session.add_all([
            Tag(asset_id="asset1", tag_type="style", tag_value="cyberpunk"),
            Tag(asset_id="asset1", tag_type="mood", tag_value="dark"),
            Tag(asset_id="asset2", tag_type="style", tag_value="fantasy"),
            Tag(asset_id="asset2", tag_type="mood", tag_value="bright")
        ])
        db_session.commit()
        
        # Search by style
        results = repo.search_by_tags(style_tags=["cyberpunk"])
        assert len(results) == 1
        assert results[0].content_hash == "asset1"
        
        # Search by mood
        results = repo.search_by_tags(mood_tags=["dark"])
        assert len(results) == 1
        assert results[0].content_hash == "asset1"
        
        # Search by multiple tags (OR logic)
        results = repo.search_by_tags(style_tags=["cyberpunk", "fantasy"])
        assert len(results) == 2


class TestContentHashing:
    """Test content hashing functionality."""
    
    def test_hash_text_file(self, tmp_path):
        """Test hashing a text file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Calculate hash
        hash1 = calculate_content_hash(test_file)
        assert len(hash1) == 64  # SHA-256 hex string
        
        # Same content = same hash
        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("Hello, World!")
        hash2 = calculate_content_hash(test_file2)
        assert hash1 == hash2
        
        # Different content = different hash
        test_file3 = tmp_path / "test3.txt"
        test_file3.write_text("Different content")
        hash3 = calculate_content_hash(test_file3)
        assert hash1 != hash3
    
    def test_hash_binary_file(self, tmp_path):
        """Test hashing a binary file."""
        # Create test binary file
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03\x04')
        
        # Calculate hash
        hash_val = calculate_content_hash(test_file)
        assert len(hash_val) == 64
        
        # Verify it's deterministic
        hash_val2 = calculate_content_hash(test_file)
        assert hash_val == hash_val2


class TestProjectRepository:
    """Test ProjectRepository functionality."""
    
    @pytest.fixture
    def repo(self, db_session):
        """Create repository with session."""
        return ProjectRepository(db_session)
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_create_project(self, repo):
        """Test creating a project."""
        project = repo.create_project(
            name="Test Project",
            description="A test",
            creative_context={'style': 'modern'}
        )
        
        assert project is not None
        assert project.name == "Test Project"
        assert project.creative_context['style'] == 'modern'
        assert project.id is not None
    
    def test_get_project(self, repo):
        """Test getting a project."""
        # Create
        project = repo.create_project(name="Test")
        project_id = project.id
        
        # Get
        loaded = repo.get_project(project_id)
        assert loaded is not None
        assert loaded.id == project_id
        assert loaded.name == "Test"
    
    def test_list_projects(self, repo):
        """Test listing projects."""
        # Create multiple
        repo.create_project(name="Project 1")
        repo.create_project(name="Project 2")
        repo.create_project(name="Project 3")
        
        # List all
        projects = repo.list_projects()
        assert len(projects) == 3
        
        # List with limit
        projects = repo.list_projects(limit=2)
        assert len(projects) == 2