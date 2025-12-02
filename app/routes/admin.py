from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from models import db, Artists, SuggestionFeedback, Genres, ArtistGenres, FestivalEdition
from app.services.poll import get_or_create_active_poll
from app.utils.session import get_session_user

bp = Blueprint("admin", __name__)


@bp.get("/admin/seed-edition-2026")
def seed_edition_2026():
    existing = FestivalEdition.query.filter_by(Name="2026").first()
    if existing:
        flash("Editie 2026 bestond al.", "info")
        return redirect(url_for("admin.editions"))

    edition = FestivalEdition(
        Name="2026",
        Location="Dendermonde",
        Start_date=date(2026, 8, 21),
        End_date=date(2026, 8, 24),
    )
    db.session.add(edition)
    db.session.commit()

    flash("Editie 2026 aangemaakt!", "success")
    return redirect(url_for("admin.editions"))


@bp.get("/admin/results")
def admin_results():
    user = get_session_user()

    if not user or not getattr(user, "is_admin", False):
        flash("Je hebt geen toegang tot deze pagina.", "danger")
        return redirect(url_for("core.home"))

    poll = get_or_create_active_poll()

    global_rows = (
        db.session.query(Artists.Artist_name, func.count())
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .group_by(Artists.Artist_name)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    global_suggestions = [{"artist": artist, "count": count} for artist, count in global_rows]

    global_genres = (
        db.session.query(Genres.name, func.count())
        .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
        .join(Artists, Artists.id == ArtistGenres.artist_id)
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .group_by(Genres.name)
        .order_by(func.count().desc())
        .all()
    )
    global_genres = [{"genre": genre, "count": count} for genre, count in global_genres]

    return render_template(
        "admin_results.html",
        global_suggestions=global_suggestions,
        global_genres=global_genres,
        poll=poll,
    )


@bp.post("/admin/poll-settings")
def update_poll_settings():
    user = get_session_user()
    if not user or not getattr(user, "is_admin", False):
        flash("Je hebt geen toegang tot deze pagina.", "danger")
        return redirect(url_for("core.home"))

    poll = get_or_create_active_poll()
    poll.is_visible = bool(request.form.get("is_visible"))
    poll.show_results = bool(request.form.get("show_results"))
    db.session.commit()

    flash("Poll-instellingen opgeslagen.", "success")
    return redirect(url_for("admin.admin_results"))


@bp.get("/editions")
def editions():
    editions = FestivalEdition.query.order_by(FestivalEdition.Start_date.desc()).all()
    return render_template("editions.html", editions=editions)