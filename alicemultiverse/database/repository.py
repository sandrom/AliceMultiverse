"""Repository pattern for database access."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import desc

from .config import get_session
from .models import Asset, AssetRelationship, Project, Tag

logger = logging.getLogger(__name__)


class AssetRepository:
    """Repository for asset-related database operations."""
    
    def create_or_update_asset(
        self,
        content_hash: str,
        file_path: str,
        media_type: str,
        metadata: dict[str, Any],
        project_id: str | None = None,
    ) -> Asset:
        """Create or update an asset.
        
        Args:
            content_hash: Content hash of the asset
            file_path: Current file path
            media_type: Type of media (image, video)
            metadata: Full metadata from analysis
            project_id: Optional project ID
            
        Returns:
            Created or updated asset
        """
        with get_session() as session:
            # Check if asset exists
            asset = session.query(Asset).filter_by(content_hash=content_hash).first()
            
            if asset:
                # Update existing asset
                asset.file_path = file_path
                asset.last_seen = datetime.now()
                if metadata:
                    asset.embedded_metadata = metadata
                    asset.file_size = metadata.get("file_size", asset.file_size)
                    # Update dimensions
                    dimensions = metadata.get("dimensions")
                    if dimensions:
                        if isinstance(dimensions, dict):
                            asset.width = dimensions.get("width", asset.width)
                            asset.height = dimensions.get("height", asset.height)
                        elif isinstance(dimensions, (list, tuple)) and len(dimensions) >= 2:
                            asset.width, asset.height = dimensions[0], dimensions[1]
                    asset.source_type = metadata.get("ai_source", asset.source_type)
                    asset.rating = metadata.get("quality_star", asset.rating)
            else:
                # Create new asset
                # Extract dimensions if available
                dimensions = metadata.get("dimensions")
                width = height = None
                if dimensions:
                    if isinstance(dimensions, dict):
                        width = dimensions.get("width")
                        height = dimensions.get("height")
                    elif isinstance(dimensions, (list, tuple)) and len(dimensions) >= 2:
                        width, height = dimensions[0], dimensions[1]
                
                asset = Asset(
                    content_hash=content_hash,
                    file_path=file_path,
                    media_type=media_type,
                    file_size=metadata.get("file_size", 0),
                    width=width,
                    height=height,
                    source_type=metadata.get("ai_source", "unknown"),
                    project_id=project_id or metadata.get("project"),
                    rating=metadata.get("quality_star"),
                    generation_params=metadata.get("generation_params", {}),
                    embedded_metadata=metadata,
                    analysis_results=metadata.get("analysis_results", {}),
                )
                session.add(asset)
            
            session.commit()
            session.refresh(asset)
            return asset

    def get_by_hash(self, content_hash: str) -> Asset | None:
        """Get asset by content hash.

        Args:
            content_hash: Content hash of the asset

        Returns:
            Asset if found, None otherwise
        """
        with get_session() as session:
            return session.query(Asset).filter_by(content_hash=content_hash).first()

    def get_by_path(self, file_path: str) -> Asset | None:
        """Get asset by file path.

        Args:
            file_path: Current file path

        Returns:
            Asset if found, None otherwise
        """
        with get_session() as session:
            return session.query(Asset).filter_by(file_path=file_path).first()

    def search(
        self,
        project_id: str | None = None,
        media_type: str | None = None,
        tags: list[str] | None = None,
        role: str | None = None,
        source_type: str | None = None,
        min_rating: int | None = None,
        limit: int = 100,
    ) -> list[Asset]:
        """Search for assets with various filters.

        Args:
            project_id: Filter by project
            media_type: Filter by media type (image, video)
            tags: Filter by tags (any match)
            role: Filter by role (hero, b_roll, etc.)
            source_type: Filter by source (fal.ai, comfyui, etc.)
            min_rating: Minimum rating
            limit: Maximum results to return

        Returns:
            List of matching assets
        """
        with get_session() as session:
            query = session.query(Asset)

            if project_id:
                query = query.filter(Asset.project_id == project_id)

            if media_type:
                query = query.filter(Asset.media_type == media_type)

            if role:
                query = query.filter(Asset.role == role)

            if source_type:
                query = query.filter(Asset.source_type == source_type)

            if min_rating:
                query = query.filter(Asset.rating >= min_rating)

            if tags:
                # Find assets with any of the specified tags
                query = query.join(Tag).filter(Tag.tag_value.in_(tags))

            return query.order_by(desc(Asset.first_seen)).limit(limit).all()

    def add_tag(
        self,
        content_hash: str,
        tag_type: str,
        tag_value: str,
        confidence: float = 1.0,
        source: str = "user",
    ) -> bool:
        """Add a tag to an asset.

        Args:
            content_hash: Asset content hash
            tag_type: Type of tag (style, mood, subject, etc.)
            tag_value: Tag value
            confidence: Confidence score (0-1)
            source: Source of tag (user, ai, auto)

        Returns:
            True if successful
        """
        with get_session() as session:
            asset = session.query(Asset).filter_by(content_hash=content_hash).first()
            if not asset:
                logger.error(f"Asset not found: {content_hash}")
                return False

            # Check if tag already exists
            existing = (
                session.query(Tag)
                .filter_by(asset_id=content_hash, tag_type=tag_type, tag_value=tag_value)
                .first()
            )

            if existing:
                # Update confidence if higher
                if confidence > existing.confidence:
                    existing.confidence = confidence
                    existing.source = source
            else:
                # Create new tag
                tag = Tag(
                    asset_id=content_hash,
                    tag_type=tag_type,
                    tag_value=tag_value,
                    confidence=confidence,
                    source=source,
                )
                session.add(tag)

            session.commit()
            return True

    def add_relationship(
        self,
        parent_hash: str,
        child_hash: str,
        relationship_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Add a relationship between assets.

        Args:
            parent_hash: Parent asset content hash
            child_hash: Child asset content hash
            relationship_type: Type of relationship
            metadata: Additional relationship data

        Returns:
            True if successful
        """
        with get_session() as session:
            # Verify both assets exist
            parent = session.query(Asset).filter_by(content_hash=parent_hash).first()
            child = session.query(Asset).filter_by(content_hash=child_hash).first()

            if not parent or not child:
                logger.error(f"Assets not found: parent={parent_hash}, child={child_hash}")
                return False

            # Check if relationship exists
            existing = (
                session.query(AssetRelationship)
                .filter_by(
                    parent_id=parent_hash, child_id=child_hash, relationship_type=relationship_type
                )
                .first()
            )

            if existing:
                # Update metadata
                if metadata:
                    existing.metadata = metadata
            else:
                # Create new relationship
                relationship = AssetRelationship(
                    parent_id=parent_hash,
                    child_id=child_hash,
                    relationship_type=relationship_type,
                    metadata=metadata or {},
                )
                session.add(relationship)

            session.commit()
            return True

    def get_related_assets(
        self, content_hash: str, relationship_type: str | None = None, direction: str = "both"
    ) -> list[Asset]:
        """Get assets related to a given asset.

        Args:
            content_hash: Asset content hash
            relationship_type: Filter by relationship type
            direction: 'parent', 'child', or 'both'

        Returns:
            List of related assets
        """
        with get_session() as session:
            related_assets = []

            if direction in ["parent", "both"]:
                # Get parent assets
                query = (
                    session.query(Asset)
                    .join(AssetRelationship, Asset.content_hash == AssetRelationship.parent_id)
                    .filter(AssetRelationship.child_id == content_hash)
                )

                if relationship_type:
                    query = query.filter(AssetRelationship.relationship_type == relationship_type)

                related_assets.extend(query.all())

            if direction in ["child", "both"]:
                # Get child assets
                query = (
                    session.query(Asset)
                    .join(AssetRelationship, Asset.content_hash == AssetRelationship.child_id)
                    .filter(AssetRelationship.parent_id == content_hash)
                )

                if relationship_type:
                    query = query.filter(AssetRelationship.relationship_type == relationship_type)

                related_assets.extend(query.all())

            return related_assets

    def update_metadata(
        self,
        content_hash: str,
        generation_params: dict | None = None,
        embedded_metadata: dict | None = None,
        analysis_results: dict | None = None,
    ) -> bool:
        """Update asset metadata.

        Args:
            content_hash: Asset content hash
            generation_params: Generation parameters to update
            embedded_metadata: Embedded metadata cache to update
            analysis_results: Analysis results to update

        Returns:
            True if successful
        """
        with get_session() as session:
            asset = session.query(Asset).filter_by(content_hash=content_hash).first()
            if not asset:
                logger.error(f"Asset not found: {content_hash}")
                return False

            if generation_params is not None:
                asset.generation_params = generation_params

            if embedded_metadata is not None:
                asset.embedded_metadata = embedded_metadata

            if analysis_results is not None:
                asset.analysis_results = analysis_results

            asset.last_seen = datetime.now()
            session.commit()
            return True


class ProjectRepository:
    """Repository for project-related database operations."""

    def create(
        self, name: str, description: str | None = None, creative_context: dict | None = None
    ) -> Project:
        """Create a new project.

        Args:
            name: Project name
            description: Project description
            creative_context: Initial creative context

        Returns:
            Created project
        """
        with get_session() as session:
            project = Project(
                name=name, description=description, creative_context=creative_context or {}
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            return project

    def get(self, project_id: str) -> Project | None:
        """Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project if found
        """
        with get_session() as session:
            return session.query(Project).filter_by(id=project_id).first()

    def list_all(self, limit: int = 100) -> list[Project]:
        """List all projects.

        Args:
            limit: Maximum projects to return

        Returns:
            List of projects
        """
        with get_session() as session:
            return session.query(Project).order_by(desc(Project.created_at)).limit(limit).all()

    def update_context(self, project_id: str, creative_context: dict) -> bool:
        """Update project creative context.

        Args:
            project_id: Project ID
            creative_context: New creative context

        Returns:
            True if successful
        """
        with get_session() as session:
            project = session.query(Project).filter_by(id=project_id).first()
            if not project:
                logger.error(f"Project not found: {project_id}")
                return False

            project.creative_context = creative_context
            project.updated_at = datetime.now()
            session.commit()
            return True

    def add_asset(self, project_id: str, content_hash: str) -> bool:
        """Add an asset to a project.

        Args:
            project_id: Project ID
            content_hash: Asset content hash

        Returns:
            True if successful
        """
        with get_session() as session:
            asset = session.query(Asset).filter_by(content_hash=content_hash).first()
            if not asset:
                logger.error(f"Asset not found: {content_hash}")
                return False

            asset.project_id = project_id
            session.commit()
            return True
