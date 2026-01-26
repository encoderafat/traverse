"""switch user_id to uuid

Revision ID: 696eee02c3dd
Revises: 7a5eb326d9ee
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "696eee02c3dd"
down_revision = "7a5eb326d9ee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # We are switching from stub integer users to Supabase UUID users.
    # Old data is invalid and intentionally dropped.
    # ------------------------------------------------------------------

    # ---- challenge_attempts.user_id ----
    op.drop_column("challenge_attempts", "user_id")
    op.add_column(
        "challenge_attempts",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_challenge_attempts_user_id",
        "challenge_attempts",
        ["user_id"],
    )

    # ---- learning_paths.user_id ----
    op.drop_column("learning_paths", "user_id")
    op.add_column(
        "learning_paths",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_learning_paths_user_id",
        "learning_paths",
        ["user_id"],
    )

    # ---- node_progress.user_id ----
    op.drop_column("node_progress", "user_id")
    op.add_column(
        "node_progress",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_node_progress_user_id",
        "node_progress",
        ["user_id"],
    )

    # ---- DROP legacy users table (no longer used) ----
    op.drop_table("users")


def downgrade() -> None:
    # Downgrade intentionally omitted.
    # This migration represents a one-way auth model switch.
    pass
