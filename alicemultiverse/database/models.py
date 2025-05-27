"""SQLAlchemy models for AliceMultiverse database."""

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Project(Base):
    """Project containing assets and creative context."""

    __tablename__ = "projects"

    # Use String for SQLite, will map to UUID in PostgreSQL
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # JSON fields for flexible data
    creative_context = Column(JSON, default={})  # Style preferences, characters, etc.
    settings = Column(JSON, default={})  # Project-specific settings
    extra_metadata = Column(JSON, default={})  # Additional metadata

    # Relationships
    assets = relationship("Asset", back_populates="project")

    __table_args__ = (
        Index("idx_projects_created", "created_at"),
        Index("idx_projects_name", "name"),
    )


class Asset(Base):
    """Asset tracked by content hash, independent of file location."""

    __tablename__ = "assets"

    # Content hash as primary identifier (SHA-256 of file content)
    content_hash = Column(String(64), primary_key=True)

    # File location (cached, can change)
    file_path = Column(String, nullable=True, index=True)
    file_path_verified = Column(DateTime, nullable=True)

    # Asset properties
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    media_type = Column(String(20))  # 'image', 'video', 'audio'
    file_size = Column(Integer)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # For video/audio

    # Creation info
    source_type = Column(String(50))  # 'fal.ai', 'comfyui', 'midjourney', etc.
    created_by = Column(String(50))  # 'ai', 'human', 'unknown'

    # Timestamps
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    generated_at = Column(DateTime, nullable=True)  # When the asset was created

    # Metadata storage
    generation_params = Column(JSON, default={})  # Prompt, model, settings
    embedded_metadata = Column(JSON, default={})  # Cache of file metadata
    analysis_results = Column(JSON, default={})  # Quality scores, etc.

    # Creative metadata
    role = Column(String(20))  # 'hero', 'b_roll', 'reference', 'test'
    rating = Column(Integer)  # User rating 1-5

    # Relationships
    project = relationship("Project", back_populates="assets")
    known_paths = relationship("AssetPath", back_populates="asset", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="asset", cascade="all, delete-orphan")

    # Relationships to other assets
    parent_relationships = relationship(
        "AssetRelationship",
        foreign_keys="AssetRelationship.child_id",
        back_populates="child",
        cascade="all, delete-orphan",
    )
    child_relationships = relationship(
        "AssetRelationship",
        foreign_keys="AssetRelationship.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_assets_project", "project_id"),
        Index("idx_assets_created", "first_seen"),
        Index("idx_assets_type", "media_type"),
        Index("idx_assets_source", "source_type"),
        Index("idx_assets_role", "role"),
    )


class AssetPath(Base):
    """Track where we've seen assets over time."""

    __tablename__ = "asset_paths"

    id = Column(Integer, primary_key=True)
    content_hash = Column(String(64), ForeignKey("assets.content_hash"))
    file_path = Column(String, nullable=False)

    # Timestamps
    discovered_at = Column(DateTime, server_default=func.now())
    last_verified = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationship
    asset = relationship("Asset", back_populates="known_paths")

    __table_args__ = (
        Index("idx_asset_paths_lookup", "file_path"),
        Index("idx_asset_paths_active", "is_active"),
        UniqueConstraint("content_hash", "file_path", name="uq_asset_path"),
    )


class AssetRelationship(Base):
    """Relationships between assets (variations, references, derivatives)."""

    __tablename__ = "asset_relationships"

    id = Column(Integer, primary_key=True)
    parent_id = Column(String(64), ForeignKey("assets.content_hash"))
    child_id = Column(String(64), ForeignKey("assets.content_hash"))

    relationship_type = Column(String(20))  # 'variation', 'reference', 'derivative', 'sequence'
    extra_data = Column(JSON, default={})  # Additional relationship data
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    parent = relationship("Asset", foreign_keys=[parent_id], back_populates="child_relationships")
    child = relationship("Asset", foreign_keys=[child_id], back_populates="parent_relationships")

    __table_args__ = (
        Index("idx_relationships_parent", "parent_id"),
        Index("idx_relationships_child", "child_id"),
        Index("idx_relationships_type", "relationship_type"),
        UniqueConstraint(
            "parent_id", "child_id", "relationship_type", name="uq_asset_relationship"
        ),
    )


class Tag(Base):
    """Semantic tags for assets."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    asset_id = Column(String(64), ForeignKey("assets.content_hash"))

    tag_type = Column(String(20))  # 'style', 'mood', 'subject', 'color', 'custom'
    tag_value = Column(String(100))
    confidence = Column(Float, default=1.0)  # For AI-generated tags
    source = Column(String(20))  # 'user', 'ai', 'auto'

    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    asset = relationship("Asset", back_populates="tags")

    __table_args__ = (
        Index("idx_tags_asset", "asset_id"),
        Index("idx_tags_type_value", "tag_type", "tag_value"),
        Index("idx_tags_value", "tag_value"),
        UniqueConstraint("asset_id", "tag_type", "tag_value", name="uq_asset_tag"),
    )
