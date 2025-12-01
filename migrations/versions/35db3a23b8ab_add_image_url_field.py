"""empty migration: image_url field no longer needed"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35db3a23b8ab'
down_revision = '898543470846'
branch_labels = None
depends_on = None


def upgrade():
    # Deze migratie deed vroeger iets met image_url,
    # maar we gebruiken nu een @property in het model.
    # Daarom laten we deze bewust leeg.
    pass


def downgrade():
    # Ook bij een downgrade niets doen.
    pass
