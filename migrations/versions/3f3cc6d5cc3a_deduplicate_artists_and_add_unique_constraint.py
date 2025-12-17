"""Deduplicate artists and add unique constraint

Revision ID: 3f3cc6d5cc3a
Revises: 24d614bbf74d
Create Date: 2025-12-30 00:00:00.000000
"""

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "3f3cc6d5cc3a"
down_revision = "24d614bbf74d"
branch_labels = None
depends_on = None


def _merge_artist_group(conn, keep_id: int, duplicate_id: int) -> None:
    poll_options = conn.execute(
        text(
            'SELECT id, poll_id, COALESCE("Count", 0) AS count '  # noqa: Q000
            'FROM "Polloption" WHERE artist_id = :dup_id'
        ),
        {"dup_id": duplicate_id},
    ).mappings()

    for option in poll_options:
        existing_option = conn.execute(
            text(
                'SELECT id, COALESCE("Count", 0) AS count '  # noqa: Q000
                'FROM "Polloption" WHERE poll_id = :poll_id AND artist_id = :keep_id'
            ),
            {"poll_id": option["poll_id"], "keep_id": keep_id},
        ).mappings().first()

        if existing_option:
            conn.execute(
                text(
                    'DELETE FROM "Votes_for" '  # noqa: Q000
                    'WHERE polloption_id = :existing_id AND user_id IN ('
                    '   SELECT user_id FROM "Votes_for" WHERE polloption_id = :old_option'
                    ')'
                ),
                {"existing_id": existing_option["id"], "old_option": option["id"]},
            )

            conn.execute(
                text(
                    'UPDATE "Votes_for" SET polloption_id = :existing_id '  # noqa: Q000
                    'WHERE polloption_id = :old_option'
                ),
                {"existing_id": existing_option["id"], "old_option": option["id"]},
            )

            conn.execute(
                text(
                    'UPDATE "Polloption" '  # noqa: Q000
                    'SET "Count" = COALESCE("Count", 0) + :add_count '
                    'WHERE id = :existing_id'
                ),
                {
                    "existing_id": existing_option["id"],
                    "add_count": option["count"],
                },
            )

            conn.execute(
                text('DELETE FROM "Polloption" WHERE id = :old_id'),  # noqa: Q000
                {"old_id": option["id"]},
            )
        else:
            conn.execute(
                text(
                    'UPDATE "Polloption" SET artist_id = :keep_id WHERE id = :old_id'  # noqa: Q000
                ),
                {"keep_id": keep_id, "old_id": option["id"]},
            )

    conn.execute(
        text(
            'DELETE FROM "ArtistGenres" ag USING "ArtistGenres" existing '  # noqa: Q000
            'WHERE ag.artist_id = :dup_id AND existing.artist_id = :keep_id '
            'AND ag.genre_id = existing.genre_id'
        ),
        {"dup_id": duplicate_id, "keep_id": keep_id},
    )

    conn.execute(
        text(
            'UPDATE "ArtistGenres" SET artist_id = :keep_id WHERE artist_id = :dup_id'  # noqa: Q000
        ),
        {"dup_id": duplicate_id, "keep_id": keep_id},
    )

    conn.execute(
        text(
            'UPDATE "Suggestion_feedback" SET artist_id = :keep_id '  # noqa: Q000
            'WHERE artist_id = :dup_id'
        ),
        {"dup_id": duplicate_id, "keep_id": keep_id},
    )

    conn.execute(
        text('DELETE FROM "Artists" WHERE id = :dup_id'),  # noqa: Q000
        {"dup_id": duplicate_id},
    )


def upgrade():
    conn = op.get_bind()

    duplicate_groups = conn.execute(
        text(
            'SELECT "Artist_name", "edition_id", array_agg(id ORDER BY id) AS ids '  # noqa: Q000
            'FROM "Artists" GROUP BY "Artist_name", "edition_id" HAVING COUNT(*) > 1'
        )
    ).mappings()

    for group in duplicate_groups:
        keep_id = group["ids"][0]
        for dup_id in group["ids"][1:]:
            _merge_artist_group(conn, keep_id, dup_id)

    conn.execute(
        text(
            'DELETE FROM "Suggestion_feedback" sf USING ('  # noqa: Q000
            '   SELECT MIN(id) AS keep_id, user_id, artist_id, festival_id '
            '   FROM "Suggestion_feedback" '
            '   GROUP BY user_id, artist_id, festival_id HAVING COUNT(*) > 1'  # noqa: E501
            ') dup '
            'WHERE sf.user_id = dup.user_id '
            '  AND sf.artist_id = dup.artist_id '
            '  AND sf.festival_id = dup.festival_id '
            '  AND sf.id <> dup.keep_id'
        )
    )

    op.create_unique_constraint(
        "uq_artists_name_edition",
        "Artists",
        ["Artist_name", "edition_id"],
    )


def downgrade():
    op.drop_constraint("uq_artists_name_edition", "Artists", type_="unique")