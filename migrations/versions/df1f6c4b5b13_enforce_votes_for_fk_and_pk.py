"""Enforce Votes_for foreign keys and composite PK

Revision ID: df1f6c4b5b13
Revises: 1d3aa63f6e3c
Create Date: 2025-01-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'df1f6c4b5b13'
down_revision = '1d3aa63f6e3c'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {col['name'] for col in inspector.get_columns('Votes_for')}
    existing_pk = inspector.get_pk_constraint('Votes_for').get('name')
    existing_fks = [fk for fk in inspector.get_foreign_keys('Votes_for') if fk.get('name')]

    with op.batch_alter_table('Votes_for', recreate='always') as batch_op:
        if existing_pk:
            batch_op.drop_constraint(existing_pk, type_='primary')

        for fk in existing_fks:
            batch_op.drop_constraint(fk['name'], type_='foreignkey')

        if 'id' in existing_columns:
            batch_op.drop_column('id')

        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('polloption_id', existing_type=sa.Integer(), nullable=False)

        batch_op.create_primary_key(
            'pk_votes_for_user_polloption', ['user_id', 'polloption_id']
        )
        batch_op.create_foreign_key(
            'fk_votes_for_user', 'User', ['user_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'fk_votes_for_polloption', 'Polloption', ['polloption_id'], ['id'], ondelete='CASCADE'
        )


def downgrade():
    with op.batch_alter_table('Votes_for', recreate='always') as batch_op:
        batch_op.drop_constraint('fk_votes_for_user', type_='foreignkey')
        batch_op.drop_constraint('fk_votes_for_polloption', type_='foreignkey')
        batch_op.drop_constraint('pk_votes_for_user_polloption', type_='primary')
        batch_op.create_primary_key('Votes_for_pkey', ['user_id', 'polloption_id'])