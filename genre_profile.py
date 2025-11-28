# recommendation_utils.py

from models import db, Genres, Artists, ArtistGenres, SuggestionFeedback
from sqlalchemy import func
import random


# -----------------------------
# STEP 2: User Genre Profile
# -----------------------------
def get_user_genre_profile(user_id):
    """
    Returns dict like:
    { 'Pop': 2, 'Electronic': 1 }
    """
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


# -----------------------------
# STEP 3: Artist Score Algorithm
# -----------------------------
def compute_artist_score(user_id, artist):
    """
    Score based on:
    - genre match
    - self-suggested
    - global popularity
    """

    # 1. Genre match
    profile = get_user_genre_profile(user_id)
    genre_score = sum(profile.get(g.name, 0) for g in artist.genres)

    # 2. Did user personally suggest this artist?
    self_suggested = (
        SuggestionFeedback.query
        .filter_by(user_id=user_id, artist_id=artist.id)
        .first() is not None
    )

    # 3. Global popularity: how many suggestions overall?
    popularity = (
        db.session.query(func.count())
        .filter(SuggestionFeedback.artist_id == artist.id)
        .scalar()
    )

    # final score (weights can be adjusted)
    score = (
        3 * int(self_suggested)
        + 2 * genre_score
        + 1 * popularity
    )

    return score


# -----------------------------
# STEP 4: Personalized Poll Generation
# -----------------------------
def generate_poll_for_user(user_id, num_options=5):
    # 1. Haal profiel maar 1 keer op
    profile = get_user_genre_profile(user_id)

    # 2. Haal ALLE artiesten + genres in 1 query
    rows = (
        db.session.query(
            Artists.id,
            Artists.Artist_name,
            Genres.name.label("genre"),
            func.count(SuggestionFeedback.id).label("popularity")
        )
        .join(ArtistGenres, ArtistGenres.artist_id == Artists.id)
        .join(Genres, Genres.id == ArtistGenres.genre_id)
        .outerjoin(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .group_by(Artists.id, Artists.Artist_name, Genres.name)
        .all()
    )

    # 3. Artiesten groeperen per artist_id
    artist_data = {}
    for artist_id, artist_name, genre, popularity in rows:
        if artist_id not in artist_data:
            artist_data[artist_id] = {
                "artist": artist_name,
                "genres": [],
                "popularity": popularity
            }
        artist_data[artist_id]["genres"].append(genre)

    # 4. Bereken score in PYTHON (zonder queries)
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

        score = (
            3 * int(self_suggested)
            + 2 * genre_score
            + data["popularity"]
        )

        scored.append((score, artist_id, data["artist"]))

    # 5. Sorteer
    scored.sort(reverse=True)

    # 6. Selecteer top-N
    top_n = max(1, int(num_options * 0.8))
    top = scored[:top_n]

    # 7. Exploratie
    remaining = scored[top_n:]
    explore_count = num_options - top_n

    if remaining:
        explore = random.sample(remaining, min(explore_count, len(remaining)))
    else:
        explore = []

    # 8. Haal Artists ORM objecten op
    final_ids = [aid for _, aid, _ in top + explore]
    return Artists.query.filter(Artists.id.in_(final_ids)).all()

