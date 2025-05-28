"""Add project budget tracking

Revision ID: 9720300ecc33
Revises: cbb2da6f61b1
Create Date: 2025-01-28 14:01:36.798927

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9720300ecc33"
down_revision: str = "cbb2da6f61b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add budget tracking to projects and create generations table."""
    # Add new columns to projects table
    op.add_column("projects", sa.Column("budget_total", sa.Float(), nullable=True))
    op.add_column("projects", sa.Column("budget_spent", sa.Float(), nullable=True))
    op.add_column("projects", sa.Column("budget_currency", sa.String(length=3), nullable=True))
    op.add_column("projects", sa.Column("status", sa.String(length=20), nullable=True))
    op.add_column("projects", sa.Column("cost_breakdown", sa.JSON(), nullable=True))
    
    # Set default values for existing rows
    op.execute("UPDATE projects SET budget_spent = 0.0 WHERE budget_spent IS NULL")
    op.execute("UPDATE projects SET budget_currency = 'USD' WHERE budget_currency IS NULL")
    op.execute("UPDATE projects SET status = 'active' WHERE status IS NULL")
    op.execute("UPDATE projects SET cost_breakdown = '{}' WHERE cost_breakdown IS NULL")
    
    # Create generations table
    op.create_table(
        "generations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("request_type", sa.String(length=20), nullable=True),
        sa.Column("prompt", sa.String(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("result_assets", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_generations_created", "generations", ["created_at"], unique=False)
    op.create_index("idx_generations_project", "generations", ["project_id"], unique=False)
    op.create_index("idx_generations_provider", "generations", ["provider"], unique=False)


def downgrade() -> None:
    """Remove budget tracking from projects and drop generations table."""
    # Drop generations table
    op.drop_index("idx_generations_provider", table_name="generations")
    op.drop_index("idx_generations_project", table_name="generations")
    op.drop_index("idx_generations_created", table_name="generations")
    op.drop_table("generations")
    
    # Remove columns from projects table
    op.drop_column("projects", "cost_breakdown")
    op.drop_column("projects", "status")
    op.drop_column("projects", "budget_currency")
    op.drop_column("projects", "budget_spent")
    op.drop_column("projects", "budget_total")