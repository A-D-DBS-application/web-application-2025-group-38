from datetime import date
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func
from PIL import Image
import os
from flask import current_app
from werkzeug.utils import secure_filename


from models import (
    db,
    Artists,
    SuggestionFeedback,
    Genres,
    ArtistGenres,
    FestivalEdition,
    User,
    Polloption,
    Poll,
)
from app.services.poll import get_or_create_active_poll
from app.utils.session import get_session_user


bp = Blueprint("admin", __name__)  # blueprint-naam = "admin"


# -------------------------------------------------------------------
# Decorator: enkel admins toelaten
# -------------------------------------------------------------------
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
    """Kleine helper om snel een voorbeeld-editie te maken (optioneel)."""
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


@bp.route("/admin/editions", methods=["GET", "POST"])
@require_admin
def editions():
    """Overzicht van alle edities + formulier om nieuwe toe te voegen."""
    # ➤ POST: nieuwe editie opslaan
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        location = (request.form.get("location") or "").strip()
        start_raw = request.form.get("start_date")
        end_raw = request.form.get("end_date")
        make_active = bool(request.form.get("is_active"))

        # eenvoudige validatie
        if not name:
            flash("Geef minstens een naam voor de editie.", "warning")
            return redirect(url_for("admin.editions"))

        # datums parsen (optioneel)
        start_date = date.fromisoformat(start_raw) if start_raw else None
        end_date = date.fromisoformat(end_raw) if end_raw else None

        # als deze nieuwe editie actief moet zijn → eerst alle andere deactiveren
        if make_active:
            FestivalEdition.query.update({FestivalEdition.is_active: False})

        # nieuwe editie aanmaken
        edition = FestivalEdition(
            Name=name,
            Location=location,
            Start_date=start_date,
            End_date=end_date,
            is_active=make_active,
        )
        db.session.add(edition)
        db.session.commit()

        flash("Nieuwe festivaleditie toegevoegd.", "success")
        return redirect(url_for("admin.editions"))

    # ➤ GET: lijst tonen
    editions = (
        FestivalEdition.query
        .order_by(FestivalEdition.Start_date.desc().nullslast())
        .all()
    )
    return render_template("editions.html", editions=editions)


@bp.post("/admin/editions/<int:edition_id>/set-active")
@require_admin
def set_active_edition(edition_id):
    """Maak een bestaande editie actief (alle andere worden inactief)."""
    # Alle edities eerst inactief
    FestivalEdition.query.update({FestivalEdition.is_active: False})

    # Gekozen editie actief maken
    edition = FestivalEdition.query.get_or_404(edition_id)
    edition.is_active = True

    db.session.commit()
    flash(f"Actieve editie gewijzigd naar: {edition.Name}", "success")
    return redirect(url_for("admin.editions"))


@bp.post("/admin/editions/<int:edition_id>/delete")
@require_admin
def delete_edition(edition_id):
    """Editie verwijderen, tenzij er nog polls aan gekoppeld zijn."""
    edition = FestivalEdition.query.get_or_404(edition_id)

    # Kijk of er polls aan deze editie hangen
    poll_count = Poll.query.filter_by(festival_id=edition.id).count()
    if poll_count > 0:
        flash(
            "Je kunt deze editie niet verwijderen omdat er nog polls aan gekoppeld zijn.",
            "warning",
        )
        return redirect(url_for("admin.editions"))

    # Alles oké → editie verwijderen
    db.session.delete(edition)
    db.session.commit()
    flash("De editie is verwijderd.", "success")
    return redirect(url_for("admin.editions"))


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
    genres = Genres.query.order_by(Genres.name).all()

    return render_template(
        "admin_artists.html",
        artists=artists,
        genres=genres,
        new_artist_name="",  # default leeg
    )


@bp.post("/admin/artists/add")
@require_admin
def admin_add_artist():
    name = (request.form.get("artist_name") or "").strip()
    genre_ids = request.form.getlist("genre_ids")
    upload = request.files.get("artist_image")

    # Validatie: naam verplicht
    if not name:
        flash("Geef een artiestnaam in.", "warning")
        return redirect(url_for("admin.admin_artists"))

    # Validatie: minstens 1 genre verplicht
    if not genre_ids:
        flash("Duid minstens één genre aan.", "warning")
        artists = Artists.query.order_by(Artists.Artist_name).all()
        genres = Genres.query.order_by(Genres.name).all()
        return render_template(
            "admin_artists.html",
            artists=artists,
            genres=genres,
            new_artist_name=name,
        )

    # Bestaat artiest al?
    existing = Artists.query.filter(
        func.lower(Artists.Artist_name) == name.lower()
    ).first()
    if existing:
        flash("Deze artiest bestaat al.", "info")
        return redirect(url_for("admin.admin_artists"))

    # ----------------------------------------
    # FOTO OPSLAAN (forceer altijd JPG)
    # ----------------------------------------
    image_path = None

    if upload and upload.filename.strip():
        upload_folder = os.path.join(
            current_app.root_path, "static", "images", "artist_images"
        )
        os.makedirs(upload_folder, exist_ok=True)

        # Forceer .jpg
        filename = secure_filename(name.lower().replace(" ", "_") + ".jpg")
        filepath = os.path.join(upload_folder, filename)

        img = Image.open(upload)

        # PNG → JPG conversie
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(filepath, format="JPEG", quality=90)

        # Correct pad opslaan (JUIST!)
        image_path = f"images/artist_images/{filename}"

    # ----------------------------------------
    # ARTIEST OPSLAAN
    # ----------------------------------------
    artist = Artists(
        Artist_name=name,
        image_url=image_path
    )
    db.session.add(artist)
    db.session.flush()

    # Genres koppelen
    for gid in genre_ids:
        db.session.add(
            ArtistGenres(artist_id=artist.id, genre_id=int(gid))
        )

    db.session.commit()

    flash(f"Artiest '{name}' is toegevoegd!", "success")
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


@bp.get("/admin/artists/<int:artist_id>")
@require_admin
def admin_artist_detail(artist_id):
    artist = Artists.query.get_or_404(artist_id)

    genres = Genres.query.order_by(Genres.name).all()

    linked_genres = (
        db.session.query(Genres)
        .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
        .filter(ArtistGenres.artist_id == artist_id)
        .all()
    )

    return render_template(
        "admin_artist_detail.html",
        artist=artist,
        genres=genres,
        linked_genres=linked_genres,
    )


@bp.post("/admin/artists/<int:artist_id>/genres/add")
@require_admin
def admin_add_genre(artist_id):
    genre_id = int(request.form.get("genre_id"))

    existing = ArtistGenres.query.filter_by(
        artist_id=artist_id,
        genre_id=genre_id,
    ).first()

    if not existing:
        db.session.add(ArtistGenres(
            artist_id=artist_id,
            genre_id=genre_id
        ))
        db.session.commit()
        flash("Genre gekoppeld!", "success")
    else:
        flash("Genre was al gekoppeld.", "info")

    return redirect(url_for("admin.admin_artist_detail", artist_id=artist_id))


@bp.post("/admin/artists/<int:artist_id>/genres/<int:genre_id>/remove")
@require_admin
def admin_remove_genre(artist_id, genre_id):
    # Zoek de koppeling tussen deze artiest en dit genre
    link = ArtistGenres.query.filter_by(
        artist_id=artist_id,
        genre_id=genre_id,
    ).first()

    if not link:
        flash("Dit genre is niet (meer) gekoppeld aan deze artiest.", "warning")
    else:
        db.session.delete(link)
        db.session.commit()
        flash("Genre verwijderd uit deze artiest.", "success")

    return redirect(url_for("admin.admin_artist_detail", artist_id=artist_id))


@bp.post("/admin/genres/add")
@require_admin
def admin_add_new_genre():
    name = (request.form.get("genre_name") or "").strip()

    if not name:
        flash("Geef een genrenaam in.", "warning")
        return redirect(url_for("admin.admin_artists"))

    existing = (
        Genres.query
        .filter(func.lower(Genres.name) == name.lower())
        .first()
    )
    if existing:
        flash("Dit genre bestaat al.", "info")
        return redirect(url_for("admin.admin_artists"))

    db.session.add(Genres(name=name))
    db.session.commit()

    flash(f"Genre '{name}' is toegevoegd.", "success")
    return redirect(url_for("admin.admin_artists"))
