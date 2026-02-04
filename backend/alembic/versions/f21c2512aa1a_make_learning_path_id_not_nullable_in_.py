"""Make learning_path_id not nullable in node_progress

Revision ID: f21c2512aa1a
Revises: 1f6733bacdc6
Create Date: 2026-02-04 09:50:46.641375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f21c2512aa1a'
down_revision: Union[str, Sequence[str], None] = '1f6733bacdc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('node_progress', 'learning_path_id',
               existing_type=sa.Integer(),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('node_progress', 'learning_path_id',
               existing_type=sa.Integer(),
               nullable=True)
