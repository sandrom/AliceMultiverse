"""Add search performance indexes

Revision ID: ab0645bf664b
Revises: cbb2da6f61b1
Create Date: 2025-05-30 17:26:28.615677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab0645bf664b'
down_revision: Union[str, None] = 'cbb2da6f61b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for search operations."""
    # Composite indexes for common search patterns
    op.create_index(
        'idx_assets_search',
        'assets',
        ['media_type', 'source_type', 'rating'],
        if_not_exists=True
    )
    
    op.create_index(
        'idx_assets_date_type',
        'assets',
        [sa.text('first_seen DESC'), 'media_type'],
        if_not_exists=True
    )
    
    op.create_index(
        'idx_tags_search',
        'tags',
        ['tag_type', 'tag_value', 'asset_id'],
        if_not_exists=True
    )
    
    op.create_index(
        'idx_tags_value_type',
        'tags',
        ['tag_value', 'tag_type'],
        if_not_exists=True
    )
    
    # Partial indexes for common filters (PostgreSQL specific)
    # These will be no-ops on SQLite
    with op.get_context().autocommit_block():
        conn = op.get_bind()
        
        # Check if we're using PostgreSQL
        if conn.dialect.name == 'postgresql':
            conn.execute(sa.text(
                "CREATE INDEX IF NOT EXISTS idx_assets_high_rating "
                "ON assets(rating) WHERE rating >= 4"
            ))
            
            conn.execute(sa.text(
                "CREATE INDEX IF NOT EXISTS idx_assets_images "
                "ON assets(first_seen DESC) WHERE media_type = 'image'"
            ))
    
    # Covering index for tag queries
    op.create_index(
        'idx_tags_covering',
        'tags',
        ['asset_id', 'tag_type', 'tag_value'],
        if_not_exists=True
    )
    
    # Index for relationship queries
    op.create_index(
        'idx_relationships_composite',
        'asset_relationships',
        ['parent_id', 'relationship_type'],
        if_not_exists=True
    )
    
    op.create_index(
        'idx_relationships_child_type',
        'asset_relationships',
        ['child_id', 'relationship_type'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_relationships_child_type', 'asset_relationships')
    op.drop_index('idx_relationships_composite', 'asset_relationships')
    op.drop_index('idx_tags_covering', 'tags')
    op.drop_index('idx_tags_value_type', 'tags')
    op.drop_index('idx_tags_search', 'tags')
    op.drop_index('idx_assets_date_type', 'assets')
    op.drop_index('idx_assets_search', 'assets')
    
    # Drop partial indexes if PostgreSQL
    with op.get_context().autocommit_block():
        conn = op.get_bind()
        if conn.dialect.name == 'postgresql':
            conn.execute(sa.text("DROP INDEX IF EXISTS idx_assets_high_rating"))
            conn.execute(sa.text("DROP INDEX IF EXISTS idx_assets_images"))