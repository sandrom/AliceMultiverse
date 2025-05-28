"""Add PostgreSQL events table

Revision ID: 719e1c2e97ef
Revises: postgres_compat
Create Date: 2025-05-28 22:52:26.929344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '719e1c2e97ef'
down_revision: Union[str, None] = 'postgres_compat'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('type', sa.String(100), nullable=False, index=True),
        sa.Column('data', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )
    
    # Create index for event type pattern matching
    op.create_index('idx_events_type_created', 'events', ['type', 'created_at'])
    
    # Create trigger function for cleanup (optional - keeps last 10k events)
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_events() RETURNS trigger AS $$
        BEGIN
            DELETE FROM events 
            WHERE created_at < NOW() - INTERVAL '7 days'
            AND (SELECT COUNT(*) FROM events) > 10000;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to run cleanup occasionally
    op.execute("""
        CREATE TRIGGER cleanup_events_trigger
        AFTER INSERT ON events
        FOR EACH ROW
        WHEN (random() < 0.01)  -- Run cleanup 1% of the time
        EXECUTE FUNCTION cleanup_old_events();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS cleanup_events_trigger ON events")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_events()")
    
    # Drop indexes
    op.drop_index('idx_events_type_created', 'events')
    
    # Drop table
    op.drop_table('events')
