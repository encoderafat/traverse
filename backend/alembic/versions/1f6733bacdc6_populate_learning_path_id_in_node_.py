"""populate learning_path_id in node_progress

Revision ID: 1f6733bacdc6
Revises: 8435d59b598b
Create Date: 2026-02-04 09:48:41.024838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f6733bacdc6'
down_revision: Union[str, Sequence[str], None] = '8435d59b598b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    UPDATE node_progress
    SET learning_path_id = path_nodes.path_id
    FROM path_nodes
    WHERE node_progress.node_id = path_nodes.id;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
