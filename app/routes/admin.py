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
    Poll,)
from app.services.poll import (
    get_active_festival,
    get_or_create_poll_for_edition,
)
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
    edition_id = request.args.get("edition_id", type=int)
    edition = None

    if edition_id:
        edition = FestivalEdition.query.get_or_404(edition_id)
    else:
        edition = get_active_festival()

    poll = get_or_create_poll_for_edition(edition)

    if not edition:
        flash("Er is nog geen editie om resultaten voor te tonen.", "warning")
        return redirect(url_for("admin.editions"))

    # Top 10 meest gesuggereerde artiesten in deze editie
    global_rows = (
        db.session.query(Artists.Artist_name, func.count())
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .filter(SuggestionFeedback.festival_id == edition.id)
        .group_by(Artists.Artist_name)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    global_suggestions = [
        {"artist": artist, "count": count} for artist, count in global_rows
    ]

    # Genres van alle suggesties in deze editie
    global_genres_rows = (
        db.session.query(Genres.name, func.count())
        .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
        .join(Artists, Artists.id == ArtistGenres.artist_id)
        .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
        .filter(SuggestionFeedback.festival_id == edition.id)
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
        edition=edition,
    )


@bp.post("/admin/poll-settings")
@require_admin
def update_poll_settings():
    edition_id = request.form.get("edition_id", type=int)
    edition = (
        FestivalEdition.query.get_or_404(edition_id)
        if edition_id
        else get_active_festival()
    )
    poll = get_or_create_poll_for_edition(edition)

    if not poll:
        flash("Er is geen poll gevonden voor deze editie.", "danger")
        return redirect(url_for("admin.editions"))
    
    poll.is_visible = bool(request.form.get("is_visible"))
    poll.show_results = bool(request.form.get("show_results"))
    db.session.commit()

    flash("Poll-instellingen opgeslagen.", "success")
    return redirect(url_for("admin.admin_results", edition_id=edition.id))


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
        active = FestivalEdition.query.filter_by(is_active=True).first()
        edition = FestivalEdition.query.filter_by(is_active=True).first()
        if not edition:
            flash("Geen actieve editie ingesteld.", "warning")
            return redirect(url_for("admin.admin_artists"))

        artists = (
         db.session.query(Artists) \
            .filter(Artists.edition_id == active.id)

        )

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
    active = FestivalEdition.query.filter_by(is_active=True).first()
    if not active:
        flash("Geen actieve editie ingesteld.", "danger")
        return redirect(url_for("admin.admin_artists"))

    artist = Artists(
        Artist_name=name,
        image_url=image_path,
        edition_id=active.id
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

    # ----------- FOTO VERWIJDEREN (BELANGRIJK!) -----------
    if artist.image_url:
        file_path = os.path.join(current_app.root_path, "static", artist.image_url)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print("Fout bij verwijderen afbeelding:", e)

    # ----------- ARTIEST VERWIJDEREN -----------
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
    related_genre_id = None

    raw_related = request.form.get("related_genre_id")
    if raw_related:
        try:
            related_genre_id = int(raw_related)
        except ValueError:
            flash("Ongeldig verwant genre gekozen.", "warning")
            return redirect(url_for("admin.admin_artists"))

        anchor_genre = db.session.get(Genres, related_genre_id)
        if not anchor_genre:
            flash("Het gekozen verwante genre bestaat niet.", "warning")
            return redirect(url_for("admin.admin_artists"))
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

    db.session.add(Genres(name=name, related_genre_id=related_genre_id))
    db.session.commit()

    flash(f"Genre '{name}' is toegevoegd.", "success")
    return redirect(url_for("admin.admin_artists"))

@bp.post("/admin/artists/<int:artist_id>/image/delete")
@require_admin
def admin_delete_artist_image(artist_id):
    artist = Artists.query.get_or_404(artist_id)

    # Staat er geen foto in de database?
    if not artist.image_url:
        flash("Deze artiest heeft geen opgeslagen foto.", "warning")
        return redirect(url_for("admin.admin_artist_detail", artist_id=artist_id))

    # Volledig pad naar bestand
    file_path = os.path.join(current_app.root_path, "static", artist.image_url)

    # Verwijder bestand als het bestaat
    if os.path.exists(file_path):
        os.remove(file_path)

    # Leeg de image_url
    artist.image_url = None
    db.session.commit()

    flash("Foto succesvol verwijderd.", "success")
    return redirect(url_for("admin.admin_artist_detail", artist_id=artist_id))

@bp.post("/admin/artists/<int:artist_id>/image/upload")
@require_admin
def admin_upload_artist_image(artist_id):
    artist = Artists.query.get_or_404(artist_id)
    upload = request.files.get("artist_image")

    if not upload or not upload.filename.strip():
        flash("Geen geldige afbeelding gekozen.", "warning")
        return redirect(url_for("admin.admin_artist_detail", artist_id=artist_id))

    upload_folder = os.path.join(
        current_app.root_path, "static", "images", "artist_images"
    )
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(artist.Artist_name.lower().replace(" ", "_") + ".jpg")
    filepath = os.path.join(upload_folder, filename)

    img = Image.open(upload)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(filepath, format="JPEG", quality=90)

    artist.image_url = f"images/artist_images/{filename}"
    db.session.commit()

    flash("Foto succesvol geüpload!", "success")
    return redirect(url_for("admin.admin_artist_detail", artist_id=artist_id))

@bp.get("/admin/artists/<int:artist_id>/delete/confirm")
@require_admin
def admin_confirm_delete_artist(artist_id):
    artist = Artists.query.get_or_404(artist_id)

    # Check of artiest gebruikt wordt
    in_poll = Polloption.query.filter_by(artist_id=artist.id).first()
    in_suggestions = SuggestionFeedback.query.filter_by(artist_id=artist.id).first()

    blocked = bool(in_poll or in_suggestions)

    return render_template(
        "admin_confirm_delete_artist.html",
        artist=artist,
        blocked=blocked
    )
@bp.post("/admin/artists/<int:artist_id>/delete/confirm")
@require_admin
def admin_delete_artist_confirmed(artist_id):

    artist = Artists.query.get_or_404(artist_id)

    in_poll = Polloption.query.filter_by(artist_id=artist.id).first()
    in_suggestions = SuggestionFeedback.query.filter_by(artist_id=artist.id).first()

    # Artiest gebruikt → blokkeren
    if in_poll or in_suggestions:
        flash(
            "Je kan deze artiest niet verwijderen: hij wordt nog gebruikt in polls of suggesties.",
            "warning"
        )
        return redirect(url_for("admin.admin_confirm_delete_artist", artist_id=artist.id))

    db.session.delete(artist)
    db.session.commit()

    flash(f"Artiest '{artist.Artist_name}' werd verwijderd.", "success")
    return redirect(url_for("admin.admin_artists"))

@bp.post("/admin/artists/<int:artist_id>/delete/force")
@require_admin
def admin_force_delete_artist(artist_id):

    artist = Artists.query.get_or_404(artist_id)

    # 1. Verwijder suggesties
    SuggestionFeedback.query.filter_by(artist_id=artist.id).delete()

    # 2. Verwijder poll opties
    Polloption.query.filter_by(artist_id=artist.id).delete()

    # 3. Verwijder genres-koppelingen
    ArtistGenres.query.filter_by(artist_id=artist.id).delete()

    # 4. Verwijder artiest zelf
    db.session.delete(artist)
    db.session.commit()

    flash(
        f"Artiest '{artist.Artist_name}' en alle verwijzingen zijn definitief verwijderd.",
        "success"
    )
    return redirect(url_for("admin.admin_artists"))

@bp.get("/admin/editions/new")
@require_admin
def admin_new_edition():
    editions = FestivalEdition.query.order_by(FestivalEdition.Start_date.desc()).all()
    return render_template("admin_new_edition.html", editions=editions)
from models import Poll, Polloption, Artists, ArtistGenres

@bp.post("/admin/editions/create")
@require_admin
def admin_create_edition():
    name = request.form.get("name")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    location = request.form.get("location")
    import_from = request.form.get("import_from")

    edition = FestivalEdition(
        Name=name,
        Start_date=start_date,
        End_date=end_date,
        Location=location,
        is_active=False
    )
    db.session.add(edition)
    db.session.commit()

    # Importeren = artiesten kopiëren
    if import_from:
        old_poll = Poll.query.filter_by(festival_id=int(import_from)).first()

        if old_poll:
            old_options = Polloption.query.filter_by(poll_id=old_poll.id).all()

            for opt in old_options:
                old_artist = opt.artist

                new_artist = Artists(
                    Artist_name=old_artist.Artist_name,
                    image_url=old_artist.image_url
                )
                db.session.add(new_artist)
                db.session.flush()

                for genre in old_artist.genres:
                    db.session.add(ArtistGenres(
                        artist_id=new_artist.id,
                        genre_id=genre.id
                    ))

            db.session.commit()

    flash("Nieuwe editie succesvol aangemaakt!", "success")
    return redirect(url_for("admin.editions"))

@bp.get("/admin/artists")
@require_admin
def admin_artists():
    active = FestivalEdition.query.filter_by(is_active=True).first()
    import_from = request.args.get("import_from", type=int)

    # Artiesten van actieve editie
    artists = (
        db.session.query(Artists)
        .filter(Artists.edition_id == active.id)
        .order_by(Artists.Artist_name)
        .all()
    )

    # Voor dropdown
    editions = FestivalEdition.query.order_by(FestivalEdition.Start_date.desc()).all()
    edition = FestivalEdition.query.filter_by(is_active=True).first()
    artists = Artists.query.filter_by(edition_id=edition.id).order_by(Artists.Artist_name).all()


    # Indien gebruiker een editie gekozen heeft → laad artiesten daarvan
    import_artists = None
    if import_from:
        import_artists = (
            db.session.query(Artists)
            .filter(Artists.edition_id == active.id)
            .order_by(Artists.Artist_name)
            .all()
        )

    return render_template(
        "admin_artists.html",
        artists=artists,
        genres=Genres.query.order_by(Genres.name).all(),
        editions=editions,
        import_artists=import_artists,
        selected_edition_id=import_from
    )

@bp.get("/admin/artists/import")
@require_admin
def admin_show_import():
    from_id = request.args.get("from_edition", type=int)

    active = FestivalEdition.query.filter_by(is_active=True).first()
    editions = FestivalEdition.query.order_by(FestivalEdition.Start_date.desc()).all()

    import_artists = []

    if from_id:
        import_artists = (
            db.session.query(Artists)
            .filter(Artists.edition_id == active.id)
            .order_by(Artists.Artist_name)
            .all()
        )

    return render_template(
        "admin_import_artists.html",
        editions=editions,
        selected_edition=from_id,
        artists=import_artists,
        active_edition=active,
    )

@bp.post("/admin/artists/import")
@require_admin
def admin_import_artists():
    artist_ids = request.form.getlist("artist_ids", type=int)
    from_edition = request.form.get("from_edition", type=int)

    active = FestivalEdition.query.filter_by(is_active=True).first()

    if not artist_ids or not from_edition or not active:
        flash("Ongeldige import.", "warning")
        return redirect(url_for("admin.admin_show_import", from_edition=from_edition))

    for old_artist in Artists.query.filter(Artists.id.in_(artist_ids)).all():

        # artiest KOPIËREN
        new_artist = Artists(
            Artist_name=old_artist.Artist_name,
            image_url=old_artist.image_url
        )
        db.session.add(new_artist)
        db.session.flush()

        # genres kopiëren
        for genre in old_artist.genres:
            new_artist.genres.append(genre)

    db.session.commit()

    flash(f"{len(artist_ids)} artiest(en) geïmporteerd naar editie {active.Name}.", "success")
    return redirect(url_for("admin.admin_artists"))

@bp.get("/admin/editions/<int:edition_id>/delete/confirm")
@require_admin
def admin_confirm_delete_edition(edition_id):
    """Bevestigingspagina voor het verwijderen van een editie."""
    edition = FestivalEdition.query.get_or_404(edition_id)

    # Tel hoeveel polls er nog aan deze editie hangen
    poll_count = Poll.query.filter_by(festival_id=edition.id).count()
    blocked = poll_count > 0

    return render_template(
        "admin_confirm_delete_edition.html",
        edition=edition,
        poll_count=poll_count,
        blocked=blocked,
    )

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


@bp.post("/admin/editions/<int:edition_id>/delete/force")
@require_admin
def admin_force_delete_edition(edition_id):
    """Editie verwijderen, maar alle gekoppelde data verhuizen naar ARCHIVE."""
    edition = FestivalEdition.query.get_or_404(edition_id)

    # ❗ Vul hier het ID in van jouw ARCHIVE-editie
    ARCHIVE_ID = 1   # bv. 1 of 5, wat het bij jou is

    if edition.id == ARCHIVE_ID:
        flash("De ARCHIVE-editie kan niet verwijderd worden.", "danger")
        return redirect(url_for("admin.editions"))

    # 1. Verhuis alle polls van deze editie naar ARCHIVE
    Poll.query.filter_by(festival_id=edition.id).update(
        {"festival_id": ARCHIVE_ID}
    )

    # 2. Verhuis alle artiest-koppelingen naar ARCHIVE
    Artists.query.filter_by(edition_id=edition.id).delete()


    # 3. Verhuis alle suggestion feedback naar ARCHIVE,
    #    maar vermijd dubbele (user, artist, festival)-combinaties
    feedbacks = SuggestionFeedback.query.filter_by(festival_id=edition.id).all()

    for fb in feedbacks:
        # Bestaat er al feedback voor deze user + artist in ARCHIVE?
        existing = SuggestionFeedback.query.filter_by(
            user_id=fb.user_id,
            artist_id=fb.artist_id,
            festival_id=ARCHIVE_ID,
        ).first()

        if existing:
            # Er is al zo'n record in ARCHIVE -> deze oude rij kunnen we veilig verwijderen
            db.session.delete(fb)
        else:
            # Nog geen record in ARCHIVE -> we verhuizen deze
            fb.festival_id = ARCHIVE_ID

    # 4. Nu kan de editie zelf veilig weg
    db.session.delete(edition)
    db.session.commit()

    flash(
        "De editie is verwijderd. Polls, stemmen, artiesten en feedback zijn bewaard in de ARCHIVE-editie.",
        "success",
    )
    return redirect(url_for("admin.editions"))

