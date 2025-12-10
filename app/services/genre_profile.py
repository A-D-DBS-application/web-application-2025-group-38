# recommendation_utils.py
import random
from typing import Dict

from sqlalchemy import func

from models import db, Genres, Artists, ArtistGenres, SuggestionFeedback
from app.services.genre_proximity import genre_proximity_scores


# -----------------------------
# STEP 2: User Genre Profile
# -----------------------------
def get_user_genre_profile(user_id: int) -> Dict[str, int]:
    """Return the genre distribution for a user's suggestions."""
    rows = (
        db.session.query(Genres.name, func.count())
        .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
        .join(Artists, Artists.id == ArtistGenres.artist_id)
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .filter(SuggestionFeedback.user_id == user_id)
        .group_by(Genres.name)
        .all()
    )

    return {genre: count for genre, count in rows}


def generate_poll_for_user(user_id: int, num_options: int = 5):
    """Generate a personalized set of poll options for a user."""
    profile = get_user_genre_profile(user_id)
    proximity_scores = genre_proximity_scores(profile.keys())
    genre_id_lookup = {
        name: gid for gid, name in Genres.query.with_entities(Genres.id, Genres.name).all()
    }

    rows = (
        db.session.query(
            Artists.id,
            Artists.Artist_name,
            Genres.name.label("genre"),
        )
        .join(ArtistGenres, ArtistGenres.artist_id == Artists.id)
        .join(Genres, Genres.id == ArtistGenres.genre_id)
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

        # Did user suggest it?
        self_suggested = (
            SuggestionFeedback.query
            .filter_by(user_id=user_id, artist_id=artist_id)
            .first()
            is not None
        )

        score = 3 * int(self_suggested) + 2 * genre_score + 5 * proximity

        scored.append((score, artist_id, data["artist"]))

    scored.sort(reverse=True)

    top_n = max(1, int(num_options * 0.8))
    top = scored[:top_n]

    remaining = scored[top_n:]
    explore_count = num_options - top_n
    explore = random.sample(remaining, min(explore_count, len(remaining))) if remaining else []

    final_ids = [aid for _, aid, _ in top + explore]
    return Artists.query.filter(Artists.id.in_(final_ids)).all()