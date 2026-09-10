"""add enable_envelope_budgeting to workspaces

Revision ID: e2b76c4208cb
Revises: 089
Create Date: 2025-09-10

"""
import sqlalchemy as sa
from alembic import op


revision = "e2b76c4208cb"
down_revision = "089"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the envelope budgeting toggle column to workspaces."""
    op.add_column(
        "workspaces",
        sa.Column(
            "enable_envelope_budgeting",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Remove the column."""
    op.drop_column("workspaces", "enable_envelope_budgeting")
