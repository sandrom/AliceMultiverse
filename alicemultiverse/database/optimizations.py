"""Database query optimizations for search performance."""

import logging
from typing import Any

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Query, joinedload, selectinload

from .models import Asset, AssetRelationship, Project, Tag

logger = logging.getLogger(__name__)


class OptimizedAssetRepository:
    """Optimized repository with eager loading and query optimization."""
    
    @staticmethod
    def build_optimized_query(session, base_query: Query | None = None) -> Query:
        """Build an optimized query with eager loading.
        
        Args:
            session: Database session
            base_query: Optional base query to optimize
            
        Returns:
            Optimized query with eager loading
        """
        if base_query is None:
            base_query = session.query(Asset)
        
        # Use selectinload for collections to avoid cartesian product
        # Use joinedload for single relationships
        return base_query.options(
            selectinload(Asset.tags),  # Load all tags in a single query
            joinedload(Asset.project),  # Load project data
            selectinload(Asset.known_paths),  # Load known paths
            selectinload(Asset.parent_relationships),  # Load relationships
            selectinload(Asset.child_relationships)
        )
    
    @staticmethod
    def search_with_pagination(
        session,
        filters: dict[str, Any],
        offset: int = 0,
        limit: int = 50,
        order_by: str = "created"
    ) -> tuple[list[Asset], int]:
        """Search assets with proper pagination and count.
        
        Args:
            session: Database session
            filters: Search filters
            offset: Pagination offset
            limit: Result limit
            order_by: Sort field
            
        Returns:
            Tuple of (assets, total_count)
        """
        # Build base query
        query = session.query(Asset)
        
        # Apply filters
        query = OptimizedAssetRepository._apply_filters(query, filters)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply eager loading
        query = OptimizedAssetRepository.build_optimized_query(session, query)
        
        # Apply ordering
        if order_by == "quality":
            query = query.order_by(desc(Asset.rating))
        elif order_by == "created":
            query = query.order_by(desc(Asset.first_seen))
        elif order_by == "modified":
            query = query.order_by(desc(Asset.last_seen))
        
        # Apply pagination
        assets = query.offset(offset).limit(limit).all()
        
        return assets, total_count
    
    @staticmethod
    def _apply_filters(query: Query, filters: dict[str, Any]) -> Query:
        """Apply search filters to query.
        
        Args:
            query: Base query
            filters: Filter criteria
            
        Returns:
            Filtered query
        """
        # Media type filter
        if filters.get("media_type"):
            query = query.filter(Asset.media_type == filters["media_type"])
        
        # Project filter
        if filters.get("project_id"):
            query = query.filter(Asset.project_id == filters["project_id"])
        
        # Source type filter
        if filters.get("source_types"):
            query = query.filter(Asset.source_type.in_(filters["source_types"]))
        
        # Rating filter
        if filters.get("min_rating"):
            query = query.filter(Asset.rating >= filters["min_rating"])
        
        # Date range filter
        if filters.get("date_start"):
            query = query.filter(Asset.first_seen >= filters["date_start"])
        if filters.get("date_end"):
            query = query.filter(Asset.first_seen <= filters["date_end"])
        
        # Tag filters with optimized subqueries
        if filters.get("tags"):
            query = OptimizedAssetRepository._apply_tag_filters(query, filters["tags"])
        
        return query
    
    @staticmethod
    def _apply_tag_filters(query: Query, tag_filters: dict[str, list[str]] | list[str]) -> Query:
        """Apply tag filters efficiently using EXISTS subqueries.
        
        Args:
            query: Base query
            tag_filters: Tag filters (dict or list)
            
        Returns:
            Filtered query
        """
        if isinstance(tag_filters, dict):
            # New format: {"style": ["cyberpunk"], "mood": ["dark"]}
            # Use EXISTS subqueries to avoid joins
            for tag_type, tag_values in tag_filters.items():
                if tag_values:
                    query = query.filter(
                        session.query(Tag).filter(
                            and_(
                                Tag.asset_id == Asset.content_hash,
                                Tag.tag_type == tag_type,
                                Tag.tag_value.in_(tag_values)
                            )
                        ).exists()
                    )
        else:
            # Legacy format: ["cyberpunk", "dark"]
            query = query.filter(
                session.query(Tag).filter(
                    and_(
                        Tag.asset_id == Asset.content_hash,
                        Tag.tag_value.in_(tag_filters)
                    )
                ).exists()
            )
        
        return query
    
    @staticmethod
    def batch_load_relationships(session, assets: list[Asset]) -> None:
        """Batch load relationships for a list of assets.
        
        Args:
            session: Database session
            assets: List of assets to load relationships for
        """
        if not assets:
            return
        
        # Extract content hashes
        content_hashes = [asset.content_hash for asset in assets]
        
        # Batch load all relationships
        relationships = session.query(AssetRelationship).filter(
            or_(
                AssetRelationship.parent_id.in_(content_hashes),
                AssetRelationship.child_id.in_(content_hashes)
            )
        ).all()
        
        # Build relationship maps
        parent_map = {}
        child_map = {}
        
        for rel in relationships:
            if rel.parent_id in content_hashes:
                child_map.setdefault(rel.parent_id, []).append(rel)
            if rel.child_id in content_hashes:
                parent_map.setdefault(rel.child_id, []).append(rel)
        
        # Attach to assets (this would need model modifications)
        # For now, this demonstrates the pattern


class SearchIndexManager:
    """Manage database indexes for search performance."""
    
    @staticmethod
    def create_search_indexes(engine) -> None:
        """Create additional indexes for search performance.
        
        Args:
            engine: SQLAlchemy engine
        """
        from sqlalchemy import text
        
        indexes = [
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_assets_search ON assets(media_type, source_type, rating)",
            "CREATE INDEX IF NOT EXISTS idx_assets_date_type ON assets(first_seen DESC, media_type)",
            "CREATE INDEX IF NOT EXISTS idx_tags_search ON tags(tag_type, tag_value, asset_id)",
            "CREATE INDEX IF NOT EXISTS idx_tags_value_type ON tags(tag_value, tag_type)",
            
            # Partial indexes for common filters
            "CREATE INDEX IF NOT EXISTS idx_assets_high_rating ON assets(rating) WHERE rating >= 4",
            "CREATE INDEX IF NOT EXISTS idx_assets_images ON assets(first_seen DESC) WHERE media_type = 'image'",
            
            # Covering index for tag queries
            "CREATE INDEX IF NOT EXISTS idx_tags_covering ON tags(asset_id, tag_type, tag_value)",
        ]
        
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")


class QueryCache:
    """Simple query result cache using Redis."""
    
    def __init__(self, redis_client=None):
        """Initialize query cache.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.ttl = 300  # 5 minutes
    
    def get_cache_key(self, query_type: str, params: dict) -> str:
        """Generate cache key for query.
        
        Args:
            query_type: Type of query
            params: Query parameters
            
        Returns:
            Cache key
        """
        import hashlib
        import json
        
        # Sort params for consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        return f"alice:search:{query_type}:{param_hash}"
    
    def get(self, key: str) -> Any | None:
        """Get cached result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None
        """
        if not self.redis:
            return None
        
        try:
            import pickle
            data = self.redis.get(key)
            return pickle.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set cached result.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.redis:
            return
        
        try:
            import pickle
            self.redis.setex(key, self.ttl, pickle.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")