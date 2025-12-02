"""add poll visibility flags"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1c2a943a6e0d'
down_revision = '35db3a23b8ab'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('poll', sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('poll', sa.Column('show_results', sa.Boolean(), nullable=False, server_default='true'))


def downgrade():
    op.drop_column('poll', 'show_results')
    op.drop_column('poll', 'is_visible')