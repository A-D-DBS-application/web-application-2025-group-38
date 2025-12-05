"""Add default to Artists.created_at"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7b75691cbeaa'
down_revision = '35db3a23b8ab'
branch_labels = None
depends_on = None



def upgrade():
    op.alter_column(
        'Artists',
        'created_at',
        server_default=sa.func.now(),
        existing_type=sa.DateTime(),
        nullable=False
    )


def downgrade():
    op.alter_column(
        'Artists',
        'created_at',
        server_default=None,
        existing_type=sa.DateTime(),
        nullable=False
    )

