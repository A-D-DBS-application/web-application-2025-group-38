# recommendation_utils.py
import random
from typing import Dict

from sqlalchemy import func

from models import db, Genres, Artists, ArtistGenres, SuggestionFeedback
from app.services.genre_proximity import genre_proximity_scores


# -----------------------------
# STEP 2: User Genre Profile
# -----------------------------
def get_user_genre_profile(user_id: int, *, festival_id: int | None = None) -> Dict[str, int]:
    """Return the genre distribution for a user's suggestions."""
    query = (
        db.session.query(Genres.name, func.count())
        .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
        .join(Artists, Artists.id == ArtistGenres.artist_id)
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .filter(SuggestionFeedback.user_id == user_id)
    )
    
    if festival_id:
        query = query.filter(SuggestionFeedback.festival_id == festival_id)

    rows = query.group_by(Genres.name).all()

    return {genre: count for genre, count in rows}


def generate_poll_for_user(user_id: int, festival_id: int, num_options: int = 5):
    profile = get_user_genre_profile(user_id, festival_id=festival_id)
    proximity_scores = genre_proximity_scores(profile.keys())
    genre_id_lookup = {
        name: gid for gid, name in Genres.query.with_entities(Genres.id, Genres.name).all()
    }

    suggested_ids = {
            row.artist_id
            for row in SuggestionFeedback.query.filter_by(
                user_id=user_id, festival_id=festival_id
            ).all()
        }
    
    rows = (
        db.session.query(
            Artists.id,
            Artists.Artist_name,
            Genres.name.label("genre"),
        )
        .join(ArtistGenres, ArtistGenres.artist_id == Artists.id)
        .join(Genres, Genres.id == ArtistGenres.genre_id)
        .filter(Artists.edition_id == festival_id)
        .all()
    )

    artist_data = {}
    for artist_id, artist_name, genre in rows:
        if artist_id not in artist_data:
            artist_data[artist_id] = {
                "artist": artist_name,
                "genres": [],
            }
        artist_data[artist_id]["genres"].append(genre)

    scored = []
    for artist_id, data in artist_data.items():
        genre_score = sum(profile.get(g, 0) for g in data["genres"])

        # Calculate how close this artist's genres are to the user's favourites.
        proximity = max(
            (
                proximity_scores.get(genre_id_lookup.get(genre_name, -1), 0.0)
                for genre_name in data["genres"]
            ),
            default=0.0,
        )

        # Score purely on genre presence and proximity to avoid overfitting to suggestions
        score = 2 * genre_score + 5 * proximity

        scored.append((score, artist_id, data["artist"], artist_id in suggested_ids))

    scored.sort(reverse=True)

    top_n = max(1, int(num_options * 0.8))
    top = scored[:top_n]

    remaining = scored[top_n:]
    explore_count = num_options - top_n
    explore = random.sample(remaining, min(explore_count, len(remaining))) if remaining else []

    # Limit the number of suggested artists to two while preserving ranking order.
    # If the cap prevents reaching the desired count, backfill with remaining
    # candidates (even suggested ones) to guarantee the poll size.
    final_ids = []
    selected = set()
    suggested_used = 0

    ordered_candidates = top + explore + [row for row in remaining if row not in explore]

    for _, artist_id, _, is_suggested in ordered_candidates:
        if artist_id in selected:
            continue
        if is_suggested and suggested_used >= 2:
            continue

        final_ids.append(artist_id)
        selected.add(artist_id)
        suggested_used += int(is_suggested)

        if len(final_ids) >= num_options:
            break

    if len(final_ids) < num_options:
        for _, artist_id, _, _ in ordered_candidates:
            if artist_id in selected:
                continue
            final_ids.append(artist_id)
            selected.add(artist_id)
            if len(final_ids) >= num_options:
                break

    return Artists.query.filter(Artists.id.in_(final_ids)).all()