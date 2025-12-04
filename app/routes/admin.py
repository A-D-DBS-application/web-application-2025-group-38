from datetime import date
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from models import (
    db,
    Artists,
    SuggestionFeedback,
    Genres,
    ArtistGenres,
    FestivalEdition,
    User,
    Polloption,
)
from app.services.poll import get_or_create_active_poll
from app.utils.session import get_session_user

bp = Blueprint("admin", __name__)


def require_admin(view_func):
    """Decorator om te checken of de huidige gebruiker admin is."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_session_user()
        if not user or not getattr(user, "is_admin", False):
            flash("Je hebt geen toegang tot deze pagina.", "danger")
            return redirect(url_for("core.home"))
        return view_func(*args, **kwargs)
    return wrapper


# -------------------------------------------------------------------
# Festival edities
# -------------------------------------------------------------------
@bp.get("/admin/seed-edition-2026")
@require_admin
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


@bp.get("/editions")
@require_admin
def editions():
    editions = FestivalEdition.query.order_by(FestivalEdition.Start_date.desc()).all()
    return render_template("editions.html", editions=editions)


# -------------------------------------------------------------------
# Admin – globale resultaten + poll-instellingen
# -------------------------------------------------------------------
@bp.get("/admin/results")
@require_admin
def admin_results():
    poll = get_or_create_active_poll()

    # Top 10 meest gesuggereerde artiesten
    global_rows = (
        db.session.query(Artists.Artist_name, func.count())
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .group_by(Artists.Artist_name)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    global_suggestions = [
        {"artist": artist, "count": count} for artist, count in global_rows
    ]

    # Genres van alle suggesties
    global_genres_rows = (
        db.session.query(Genres.name, func.count())
        .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
        .join(Artists, Artists.id == ArtistGenres.artist_id)
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .group_by(Genres.name)
        .order_by(func.count().desc())
        .all()
    )
    global_genres = [
        {"genre": genre, "count": count} for genre, count in global_genres_rows
    ]

    return render_template(
        "admin_results.html",
        global_suggestions=global_suggestions,
        global_genres=global_genres,
        poll=poll,
    )


@bp.post("/admin/poll-settings")
@require_admin
def update_poll_settings():
    poll = get_or_create_active_poll()
    poll.is_visible = bool(request.form.get("is_visible"))
    poll.show_results = bool(request.form.get("show_results"))
    db.session.commit()

    flash("Poll-instellingen opgeslagen.", "success")
    return redirect(url_for("admin.admin_results"))


# -------------------------------------------------------------------
# Admin – gebruikers / admins
# -------------------------------------------------------------------
@bp.get("/admin/users")
@require_admin
def admin_users():
    admins = User.query.filter_by(is_admin=True).order_by(User.email).all()
    return render_template("admin_users.html", admins=admins)


@bp.post("/admin/users/make_admin")
@require_admin
def make_admin():
    email = (request.form.get("email") or "").strip()

    if not email:
        flash("Geef een e-mailadres in.", "warning")
        return redirect(url_for("admin.admin_users"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("Er bestaat nog geen gebruiker met dit e-mailadres.", "danger")
        return redirect(url_for("admin.admin_users"))

    if user.is_admin:
        flash("Deze gebruiker is al admin.", "info")
        return redirect(url_for("admin.admin_users"))

    user.is_admin = True
    db.session.commit()
    flash(f"{email} is nu admin.", "success")
    return redirect(url_for("admin.admin_users"))


@bp.post("/admin/users/<int:user_id>/remove_admin")
@require_admin
def remove_admin(user_id):
    current = get_session_user()
    user = db.session.get(User, user_id)

    if not user:
        flash("Gebruiker niet gevonden.", "danger")
        return redirect(url_for("admin.admin_users"))

    # Je mag jezelf niet demoten
    if current.id == user.id:
        flash("Je kan je eigen admin-rechten niet verwijderen.", "warning")
        return redirect(url_for("admin.admin_users"))

    if not user.is_admin:
        flash("Deze gebruiker is geen admin.", "info")
        return redirect(url_for("admin.admin_users"))

    user.is_admin = False
    db.session.commit()
    flash(
        f"Admin-rechten van {user.email or 'deze gebruiker'} zijn verwijderd.",
        "success",
    )
    return redirect(url_for("admin.admin_users"))


# -------------------------------------------------------------------
# Admin – artiestenbeheer
# -------------------------------------------------------------------
@bp.get("/admin/artists")
@require_admin
def admin_artists():
    artists = Artists.query.order_by(Artists.Artist_name).all()
    return render_template("admin_artists.html", artists=artists)


@bp.post("/admin/artists/add")
@require_admin
def admin_add_artist():
    name = (request.form.get("artist_name") or "").strip()

    if not name:
        flash("Geef een artiestnaam in.", "warning")
        return redirect(url_for("admin.admin_artists"))

    existing = (
        Artists.query
        .filter(func.lower(Artists.Artist_name) == name.lower())
        .first()
    )
    if existing:
        flash("Deze artiest bestaat al.", "info")
        return redirect(url_for("admin.admin_artists"))

    artist = Artists(Artist_name=name)
    db.session.add(artist)
    db.session.commit()

    flash(f"Artiest '{name}' is toegevoegd.", "success")
    return redirect(url_for("admin.admin_artists"))


@bp.post("/admin/artists/<int:artist_id>/delete")
@require_admin
def admin_delete_artist(artist_id):
    artist = db.session.get(Artists, artist_id)
    if not artist:
        flash("Artiest niet gevonden.", "danger")
        return redirect(url_for("admin.admin_artists"))

    # check of de artiest nog gebruikt wordt
    in_poll = Polloption.query.filter_by(artist_id=artist.id).first()
    in_suggestions = SuggestionFeedback.query.filter_by(artist_id=artist.id).first()

    if in_poll or in_suggestions:
        flash(
            "Je kan deze artiest niet verwijderen: "
            "hij wordt nog gebruikt in polls of suggesties.",
            "warning",
        )
        return redirect(url_for("admin.admin_artists"))

    db.session.delete(artist)
    db.session.commit()
    flash("Artiest verwijderd.", "success")
    return redirect(url_for("admin.admin_artists"))
