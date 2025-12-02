from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from models import db, Artists, SuggestionFeedback
from app.utils.session import get_session_user

bp = Blueprint("suggestions", __name__)

MAX_SUGGESTIONS = 5


@bp.route("/suggest", methods=["GET", "POST"])
def suggest():
    user = get_session_user()

    if not user:
        flash("Je moet ingelogd zijn om een suggestie te doen.", "warning")
        return render_template(
            "suggest.html",
            user=None,
            suggestions=[],
            remaining=0,
        )

    existing_count = (
        db.session.query(func.count(SuggestionFeedback.id))
        .filter(SuggestionFeedback.user_id == user.id)
        .scalar()
    )

    if existing_count >= MAX_SUGGESTIONS:
        flash(f"Je hebt al {MAX_SUGGESTIONS} artiesten voorgesteld.", "info")
        return redirect(url_for("poll.poll_detail"))

    if request.method == "POST":
        artist_name = (request.form.get("artist_name") or "").strip()

        if not artist_name:
            flash("Geef een artiestnaam op.", "warning")
            return redirect(url_for("suggestions.suggest"))

        artist = (
            Artists.query
            .filter(func.lower(Artists.Artist_name) == artist_name.lower())
            .first()
        )

        if not artist:
            artist = Artists(Artist_name=artist_name)
            db.session.add(artist)
            db.session.commit()

        already = (
            SuggestionFeedback.query
            .filter_by(user_id=user.id, artist_id=artist.id)
            .first()
        )
        if already:
            flash("Je hebt deze artiest al voorgesteld.", "info")
            return redirect(url_for("suggestions.suggest"))

        suggestion = SuggestionFeedback(artist_id=artist.id, user_id=user.id)
        db.session.add(suggestion)
        db.session.commit()

        flash(
            f"Bedankt voor je suggestie! "
            f"Je hebt nu {existing_count + 1} van de {MAX_SUGGESTIONS} artiesten voorgesteld.",
            "success",
        )
        return redirect(url_for("suggestions.suggest"))

    user_suggestions = (
        db.session.query(Artists.Artist_name)
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .filter(SuggestionFeedback.user_id == user.id)
        .all()
    )

    return render_template(
        "suggest.html",
        user=user,
        suggestions=[row.Artist_name for row in user_suggestions],
        remaining=MAX_SUGGESTIONS - existing_count,
    )