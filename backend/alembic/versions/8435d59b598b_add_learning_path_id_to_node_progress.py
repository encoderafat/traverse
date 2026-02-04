"""Add learning_path_id to node_progress

Revision ID: 8435d59b598b
Revises: bd8e7738cbe4
Create Date: 2026-02-04 09:46:04.896355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8435d59b598b'
down_revision: Union[str, Sequence[str], None] = 'bd8e7738cbe4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('node_progress', sa.Column('learning_path_id', sa.Integer(), nullable=True, index=True))
    op.create_foreign_key('fk_node_progress_learning_path', 'node_progress', 'learning_paths', ['learning_path_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_node_progress_learning_path', 'node_progress', type_='foreignkey')
    op.drop_column('node_progress', 'learning_path_id')
