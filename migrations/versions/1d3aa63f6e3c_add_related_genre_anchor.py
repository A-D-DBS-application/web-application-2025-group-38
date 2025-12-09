"""Add related_genre_id anchor to Genres

Revision ID: 1d3aa63f6e3c
Revises: 849540301ede
Create Date: 2025-12-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1d3aa63f6e3c'
down_revision = '849540301ede'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Genres', schema=None) as batch_op:
        batch_op.add_column(sa.Column('related_genre_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key(
            'fk_Genres_related_genre_id_Genres',
            'Genres',
            ['related_genre_id'],
            ['id'],
        )


def downgrade():
    with op.batch_alter_table('Genres', schema=None) as batch_op:
        batch_op.drop_constraint('fk_Genres_related_genre_id_Genres', type_='foreignkey')
        batch_op.drop_column('related_genre_id')