from genre_profile import get_user_genre_profile, generate_poll_for_user

from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from sqlalchemy import text, func, desc

from config import Config
from models import (
    db, User, Artists, SuggestionFeedback,
    FestivalEdition, Poll, Polloption, VotesFor,
    Genres, ArtistGenres  
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    # ======================================================
    # Sessie helpers

    def get_session_user():
        uid = session.get("user_id")
        return db.session.get(User, uid) if uid else None

    def login_user(user: User):
        session["user_id"] = user.id

    def logout_user():
        session.pop("user_id", None)

    # ======================================================
    # Basisroutes

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/health")
    def health():
        db.session.execute(text("select 1"))
        return {"status": "ok"}, 200

    # ======================================================
    # Suggesties

    @app.route("/suggest", methods=["GET", "POST"])
    def suggest():
        user = get_session_user()

        # 1. Alleen ingelogde gebruikers mogen suggesties doen
        if not user:
            flash("Je moet ingelogd zijn om een suggestie te doen.", "warning")
            return render_template(
                "suggest.html",
                user=None,
                suggestions=[],
                remaining=0,
            )

        MAX_SUGGESTIONS = 5

        # 2. Hoeveel suggesties heeft deze user al?
        existing_count = (
            db.session.query(func.count(SuggestionFeedback.id))
            .filter(SuggestionFeedback.user_id == user.id)
            .scalar()
        )

        # Als hij aan de limiet zit → blokkeer extra
        if existing_count >= MAX_SUGGESTIONS:
            flash(f"Je hebt al {MAX_SUGGESTIONS} artiesten voorgesteld.", "info")
            return redirect(url_for("poll_detail"))

        # 3. POST: nieuwe suggestie
        if request.method == "POST":
            artist_name = (request.form.get("artist_name") or "").strip()

            if not artist_name:
                flash("Geef een artiestnaam op.", "warning")
                return redirect(url_for("suggest"))

            # 3a. Zoek of artiest al bestaat
            artist = (
                Artists.query
                .filter(func.lower(Artists.Artist_name) == artist_name.lower())
                .first()
            )

            # Bestaat hij nog niet? -> maak hem
            if not artist:
                artist = Artists(Artist_name=artist_name)
                db.session.add(artist)
                db.session.commit()

            # 3b. Check of deze user deze artiest al gesuggereerd heeft
            already = (
                SuggestionFeedback.query
                .filter_by(user_id=user.id, artist_id=artist.id)
                .first()
            )
            if already:
                flash("Je hebt deze artiest al voorgesteld.", "info")
                return redirect(url_for("suggest"))

            # 3c. Suggestie opslaan
            s = SuggestionFeedback(artist_id=artist.id, user_id=user.id)
            db.session.add(s)
            db.session.commit()

            flash(
                f"Bedankt voor je suggestie! "
                f"Je hebt nu {existing_count + 1} van de {MAX_SUGGESTIONS} artiesten voorgesteld.",
                "success",
            )
            return redirect(url_for("suggest"))

        # 4. GET: toon pagina + bestaande suggesties van deze user
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

    # ======================================================
    # Login & Logout

    @app.route("/register", methods=["GET", "POST"])
    def register():
        
        if get_session_user():
            session.pop('_flashes', None)  # oude meldingen wissen
            flash("Je bent al ingelogd.", "info")
            return render_template("register.html")

        if request.method == "POST":
            email = (request.form.get("email") or "").strip()
            user = User.query.filter_by(email=email).first() if email else None

            if not user:
                user = User(email=email or None)
                db.session.add(user)
                db.session.commit()

            login_user(user)

            # verwijder oude meldingen, toon enkel deze
            session.pop('_flashes', None)
            flash("Succesvol ingelogd!", "info")

            # blijf gewoon op loginpagina
            return render_template("register.html")

        return render_template("register.html")

    @app.get("/logout")
    def logout():
        if get_session_user():
            logout_user()
            flash("Je bent afgemeld.", "info")
        return redirect(url_for("home"))

    # ======================================================
    # Seed: voorbeeld-editie

    @app.get("/admin/seed-edition-2026")
    def seed_edition_2026():
        existing = FestivalEdition.query.filter_by(Name="2026").first()
        if existing:
            flash("Editie 2026 bestond al.", "info")
            return redirect(url_for("editions"))

        ed = FestivalEdition(
            Name="2026",
            Location="Dendermonde",
            Start_date=date(2026, 8, 21),
            End_date=date(2026, 8, 24),
        )
        db.session.add(ed)
        db.session.commit()

        flash("Editie 2026 aangemaakt!", "success")
        return redirect(url_for("editions"))

    # ======================================================
    # POLL SYSTEEM

    def _top3_polloptions():
        """
        Bereken de top-3 artiesten uit suggesties en bewaar ze in Polloption.
        Deze functie wordt enkel uitgevoerd wanneer de pollpagina geopend wordt.
        """
        top = (
            db.session.query(
                Artists.id.label("artist_id"),
                Artists.Artist_name.label("name"),
                func.count(SuggestionFeedback.id).label("cnt"),
            )
            .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
            .group_by(Artists.Artist_name)
            .order_by(desc("cnt"))
            .limit(3)
            .all()
        )

        # Oude pollopties wissen en top-3 toevoegen
        db.session.query(Polloption).delete()
        db.session.commit()

        for row in top:
            po = Polloption(text=row.name, artist_id=row.artist_id)
            db.session.add(po)
        db.session.commit()

    # ---------- Pollpagina ----------
    @app.get("/poll_detail")
    def poll_detail():
        user = get_session_user()

        if not user:
            flash("Je moet ingelogd zijn om een stem uit te brengen.", "warning")
            return redirect(url_for("register"))

        # 1️⃣ Slim profiel & gepersonaliseerde artiestenselectie
        profile = get_user_genre_profile(user.id)
        print("User genre profile:", profile)

        poll_artists = generate_poll_for_user(user.id, num_options=5)
        print("Generated poll:", [a.Artist_name for a in poll_artists])

        # 2️⃣ Oude pollopties verwijderen
        db.session.query(Polloption).delete()
        db.session.commit()

        # 3️⃣ Nieuwe pollopties invoegen
        for artist in poll_artists:
            option = Polloption(
                text=artist.Artist_name,
                artist_id=artist.id,
                Count=0,
                poll_id=None       # je gebruikt geen Poll entity
            )
            db.session.add(option)

        db.session.commit()

        # 4️⃣ Pollopties ophalen & renderen
        options = Polloption.query.all()
        return render_template("poll_detail.html", options=options)

    # ---------- Stem opslaan ----------
    @app.post("/vote")
    def vote():
        polloption_id = request.form.get("artist_id", type=int)
        user = get_session_user()

        # 1. Als niet ingelogd → niet stemmen
        if not user:
            flash("Je moet ingelogd zijn om te stemmen.", "warning")
            return redirect(url_for("poll_detail"))

        # 2. Geen artiest gekozen
        if not polloption_id:
            flash("Kies eerst een artiest om te stemmen.", "warning")
            return redirect(url_for("poll_detail"))

        # 3. Controleer of de artiest geldig is
        option = Polloption.query.get(polloption_id)
        if not option:
            flash("Ongeldige stemoptie.", "danger")
            return redirect(url_for("poll_detail"))

        #  4. Controleer of user al gestemd heeft
        existing_vote = VotesFor.query.filter_by(user_id=user.id).first()
        if existing_vote:
            flash("Je hebt al gestemd.", "info")
            return redirect(url_for("results"))

        # 5. Nieuwe stem opslaan
        try:
            v = VotesFor(polloption_id=polloption_id, user_id=user.id)
            db.session.add(v)
            db.session.commit()
            flash("Je stem is opgeslagen! 🎉", "success")
            return redirect(url_for("results"))
        except Exception as e:
            db.session.rollback()
            flash(f"Er ging iets mis bij het opslaan van je stem: {e}", "danger")
            return redirect(url_for("poll_detail"))

    # ---------- Resultaten ----------
    @app.get("/results")
    def results():
        user = get_session_user()
        if not user:
            flash("Je moet ingelogd zijn.", "warning")
            return redirect(url_for("register"))

        # ----------- 1. JOUW GENRE PROFIEL ------------
        genre_rows = (
            db.session.query(Genres.name, func.count())
            .join(ArtistGenres, ArtistGenres.genre_id == Genres.id)
            .join(Artists, Artists.id == ArtistGenres.artist_id)
            .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
            .filter(SuggestionFeedback.user_id == user.id)
            .group_by(Genres.name)
            .all()
        )

        user_profile = {genre: count for genre, count in genre_rows}

        # ----------- 2. GLOBAL SUGGESTIES (top 10) ------------
        global_rows = (
            db.session.query(Artists.Artist_name, func.count())
            .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
            .group_by(Artists.Artist_name)
            .order_by(func.count().desc())
            .limit(10)
            .all()
        )

        global_suggestions = [{"artist": a, "count": c} for a, c in global_rows]

        return render_template(
            "results.html",
            user_profile=user_profile,
            global_suggestions=global_suggestions
        )

    # ======================================================
    return app




