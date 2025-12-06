from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from models import (
    db,
    Poll,
    Polloption,
    VotesFor,
    FestivalEdition,
    Artists,
    Genres,
    ArtistGenres,
    SuggestionFeedback,
)
from app.services.genre_profile import get_user_genre_profile, generate_poll_for_user
from app.services.poll import get_or_create_active_poll
from app.utils.session import get_session_user


bp = Blueprint("poll", __name__)


@bp.get("/poll_detail")
def poll_detail():
    user = get_session_user()
    poll = get_or_create_active_poll()

    if not poll.is_visible:
        flash("De poll is momenteel niet zichtbaar. Kom later terug!", "info")
        return redirect(url_for("core.home"))

    if not user:
        flash("Je moet ingelogd zijn om een stem uit te brengen.", "warning")
        return redirect(url_for("auth.register"))

    profile = get_user_genre_profile(user.id)
    poll_artists = generate_poll_for_user(user.id, num_options=5)

    # Oude opties wissen en nieuwe vullen
    db.session.query(Polloption).delete()
    db.session.commit()

    for artist in poll_artists:
        option = Polloption(
            text=artist.Artist_name,
            artist_id=artist.id,
            Count=0,
            poll_id=poll.id,
        )
        db.session.add(option)
    db.session.commit()

    options = Polloption.query.all()
    return render_template("poll_detail.html", options=options, profile=profile)


@bp.post("/vote")
def vote():
    polloption_id = request.form.get("artist_id", type=int)
    user = get_session_user()

    if not user:
        flash("Je moet ingelogd zijn om te stemmen.", "warning")
        return redirect(url_for("poll.poll_detail"))

    if not polloption_id:
        flash("Kies eerst een artiest om te stemmen.", "warning")
        return redirect(url_for("poll.poll_detail"))

    option = Polloption.query.get(polloption_id)
    if not option:
        flash("Ongeldige stemoptie.", "danger")
        return redirect(url_for("poll.poll_detail"))

    existing_vote = VotesFor.query.filter_by(user_id=user.id).first()
    if existing_vote:
        flash("Je hebt al gestemd.", "info")
        return redirect(url_for("poll.results"))

    try:
        vote_record = VotesFor(polloption_id=polloption_id, user_id=user.id)
        db.session.add(vote_record)
        db.session.commit()
        flash("Je stem is opgeslagen! 🎉", "success")
        return redirect(url_for("poll.results"))
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        flash(f"Er ging iets mis bij het opslaan van je stem: {exc}", "danger")
        return redirect(url_for("poll.poll_detail"))


@bp.get("/results")
def results():
    user = get_session_user()

    # --- Muziekprofiel (genres) ---
    genre_counts = {}
    genre_percentages = {}

    if user:
        rows = (
            db.session.query(Genres.name, func.count())
            .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
            .join(Artists, Artists.id == ArtistGenres.artist_id)
            .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
            .filter(SuggestionFeedback.user_id == user.id)
            .group_by(Genres.name)
            .all()
        )
        genre_counts = {g: c for g, c in rows}
        total = sum(genre_counts.values()) or 1
        genre_percentages = {
            g: round(c * 100 / total, 1) for g, c in genre_counts.items()
        }

    # --- Jouw stemmen per editie ---
    user_votes = []
    if user:
        user_votes = (
            db.session.query(VotesFor, Polloption, Poll, FestivalEdition, Artists)
            .join(Polloption, VotesFor.polloption_id == Polloption.id)
            .join(Poll, Polloption.poll_id == Poll.id)
            .join(FestivalEdition, Poll.festival_id == FestivalEdition.id)
            .join(Artists, Polloption.artist_id == Artists.id)
            .filter(VotesFor.user_id == user.id)
            .order_by(FestivalEdition.Start_date.desc())
            .all()
        )

    return render_template(
        "results.html",
        genre_counts=genre_counts,
        genre_percentages=genre_percentages,
        user_votes=user_votes,
    )
