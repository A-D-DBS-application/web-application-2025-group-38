# recommendation_utils.py
import random
from typing import Dict
from sqlalchemy import func
from models import db, Genres, Artists, ArtistGenres, SuggestionFeedback


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

    rows = (
        db.session.query(
            Artists.id,
            Artists.Artist_name,
            Genres.name.label("genre"),
            func.count(SuggestionFeedback.id).label("popularity"),
        )
        .join(ArtistGenres, ArtistGenres.artist_id == Artists.id)
        .join(Genres, Genres.id == ArtistGenres.genre_id)
        .outerjoin(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .group_by(Artists.id, Artists.Artist_name, Genres.name)
        .all()
    )

    artist_data = {}
    for artist_id, artist_name, genre, popularity in rows:
        if artist_id not in artist_data:
            artist_data[artist_id] = {
                "artist": artist_name,
                "genres": [],
                "popularity": popularity,
            }
        artist_data[artist_id]["genres"].append(genre)

    scored = []
    for artist_id, data in artist_data.items():
        genre_score = sum(profile.get(g, 0) for g in data["genres"])

        # Did user suggest it?
        self_suggested = (
            SuggestionFeedback.query
            .filter_by(user_id=user_id, artist_id=artist_id)
            .first()
            is not None
        )
        score = 3 * int(self_suggested) + 2 * genre_score + data["popularity"]

        scored.append((score, artist_id, data["artist"]))

    scored.sort(reverse=True)

    top_n = max(1, int(num_options * 0.8))
    top = scored[:top_n]

    remaining = scored[top_n:]
    explore_count = num_options - top_n
    explore = random.sample(remaining, min(explore_count, len(remaining))) if remaining else []

    final_ids = [aid for _, aid, _ in top + explore]
    return Artists.query.filter(Artists.id.in_(final_ids)).all()

