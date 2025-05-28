"""PostgreSQL compatibility migration

Revision ID: postgres_compat
Revises: 9720300ecc33
Create Date: 2025-01-28 16:00:00.000000

This migration ensures all tables use PostgreSQL-compatible syntax.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "postgres_compat"
down_revision: str = "9720300ecc33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Ensure PostgreSQL compatibility."""
    # PostgreSQL uses JSONB for better performance
    # Update JSON columns to JSONB if on PostgreSQL
    connection = op.get_bind()
    
    if connection.dialect.name == 'postgresql':
        # Convert JSON columns to JSONB for better performance
        op.alter_column('projects', 'creative_context',
                       type_=postgresql.JSONB,
                       postgresql_using='creative_context::jsonb')
        op.alter_column('projects', 'settings',
                       type_=postgresql.JSONB,
                       postgresql_using='settings::jsonb')
        op.alter_column('projects', 'extra_metadata',
                       type_=postgresql.JSONB,
                       postgresql_using='extra_metadata::jsonb')
        op.alter_column('projects', 'cost_breakdown',
                       type_=postgresql.JSONB,
                       postgresql_using='cost_breakdown::jsonb')
        
        op.alter_column('assets', 'generation_params',
                       type_=postgresql.JSONB,
                       postgresql_using='generation_params::jsonb')
        op.alter_column('assets', 'embedded_metadata',
                       type_=postgresql.JSONB,
                       postgresql_using='embedded_metadata::jsonb')
        op.alter_column('assets', 'analysis_results',
                       type_=postgresql.JSONB,
                       postgresql_using='analysis_results::jsonb')
        
        op.alter_column('asset_relationships', 'extra_data',
                       type_=postgresql.JSONB,
                       postgresql_using='extra_data::jsonb')
        
        op.alter_column('generations', 'parameters',
                       type_=postgresql.JSONB,
                       postgresql_using='parameters::jsonb')
        op.alter_column('generations', 'result_assets',
                       type_=postgresql.JSONB,
                       postgresql_using='result_assets::jsonb')
        
        # Add GIN indexes for JSONB columns for better query performance
        op.create_index('idx_projects_creative_context_gin', 'projects', ['creative_context'],
                       postgresql_using='gin')
        op.create_index('idx_assets_tags_gin', 'assets', ['embedded_metadata'],
                       postgresql_using='gin')
        op.create_index('idx_assets_analysis_gin', 'assets', ['analysis_results'],
                       postgresql_using='gin')


def downgrade() -> None:
    """Downgrade is not supported - PostgreSQL is required."""
    raise NotImplementedError("Downgrade not supported - PostgreSQL is required")