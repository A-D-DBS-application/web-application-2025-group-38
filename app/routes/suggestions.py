from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from models import db, Artists, SuggestionFeedback, FestivalEdition
from app.utils.session import get_session_user

bp = Blueprint("suggestions", __name__)

MAX_SUGGESTIONS = 5


def get_current_edition():
    """Haalt de actieve festivaleditie op."""
    return FestivalEdition.query.filter_by(is_active=True).first()


@bp.route("/suggest", methods=["GET", "POST"])
def suggest():
    user = get_session_user()
    edition = get_current_edition()

    # geen user → gewoon lege pagina met waarschuwing
    if not user:
        flash("Je moet ingelogd zijn om een suggestie te doen.", "warning")
        return render_template(
            "suggest.html",
            user=None,
            suggestions=[],
            remaining=0,
            artists=[],
        )

    # geen actieve editie → niets te doen
    if not edition:
        flash("Er is momenteel geen actieve editie ingesteld door de admin.", "info")
        return render_template(
            "suggest.html",
            user=user,
            suggestions=[],
            remaining=0,
            artists=[],
        )

    # Hoeveel suggesties heeft deze user al gedaan IN DEZE EDITIE?
    existing_count = (
        db.session.query(func.count(SuggestionFeedback.id))
        .filter(
            SuggestionFeedback.user_id == user.id,
            SuggestionFeedback.festival_id == edition.id,
        )
        .scalar()
    )

    # Limiet bereikt? → direct naar poll
    if existing_count >= MAX_SUGGESTIONS:
        flash(
            f"Je hebt al {MAX_SUGGESTIONS} artiesten voorgesteld "
            f"voor de editie '{edition.Name}'.",
            "info",
        )
        return redirect(url_for("poll.poll_detail"))

    # -------------------  POST: nieuwe suggestie  -------------------
    if request.method == "POST":
        artist_name = (request.form.get("artist_name") or "").strip()

        if not artist_name:
            flash("Geef een artiestnaam op.", "warning")
            return redirect(url_for("suggestions.suggest"))

        # artiest opzoeken in lijst (case-insensitive)
        artist = (
            Artists.query
            .filter(func.lower(Artists.Artist_name) == artist_name.lower())
            .first()
        )

        if not artist:
            flash(
                "Kies een artiest uit de lijst. "
                "Je kan geen nieuwe artiest intypen.",
                "warning",
            )
            return redirect(url_for("suggestions.suggest"))

        # Heeft deze user deze artiest in DEZE EDITIE al voorgesteld?
        already = (
            SuggestionFeedback.query
            .filter_by(
                user_id=user.id,
                artist_id=artist.id,
                festival_id=edition.id,
            )
            .first()
        )

        if already:
            flash(
                "Je hebt deze artiest in deze editie al voorgesteld.",
                "info",
            )
            return redirect(url_for("suggestions.suggest"))

        # Nieuwe suggestie opslaan (hier komt festival_id mee!)
        suggestion = SuggestionFeedback(
            artist_id=artist.id,
            user_id=user.id,
            festival_id=edition.id,
        )
        db.session.add(suggestion)
        db.session.commit()

        existing_count += 1

        if existing_count >= MAX_SUGGESTIONS:
            flash(
                f"Bedankt! Je hebt nu {existing_count} artiesten voorgesteld "
                f"voor de editie '{edition.Name}'.",
                "success",
            )
            return redirect(url_for("poll.poll_detail"))

        flash(
            f"Bedankt voor je suggestie! "
            f"({existing_count}/{MAX_SUGGESTIONS} voor deze editie)",
            "success",
        )
        return redirect(url_for("suggestions.suggest"))

    # -------------------  GET: pagina tonen  -------------------
    # Alle artiesten voor de dropdown
    artists = Artists.query.order_by(Artists.Artist_name).all()

    # Jouw eigen suggesties in deze editie, met artiestnamen
    user_suggestions = (
        db.session.query(Artists.Artist_name)
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .filter(
            SuggestionFeedback.user_id == user.id,
            SuggestionFeedback.festival_id == edition.id,
        )
        .order_by(Artists.Artist_name)
        .all()
    )

    return render_template(
        "suggest.html",
        user=user,
        suggestions=[row.Artist_name for row in user_suggestions],
        remaining=MAX_SUGGESTIONS - existing_count,
        artists=artists,
    )
