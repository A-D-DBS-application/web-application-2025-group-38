from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from sqlalchemy import text, func, desc

from config import Config
from models import (
    db, User, Artists, SuggestionFeedback,
    FestivalEdition, Poll, Polloption, VotesFor
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
            # Stuur NIET meteen door, toon gewoon de suggestiepagina (met lege velden)
            return render_template("suggest.html", user=None)

        # 2. Controleer of gebruiker al iets gesuggereerd heeft
        existing_suggestion = (
            db.session.query(SuggestionFeedback)
            .filter(SuggestionFeedback.user_id == user.id)
            .first()
        )
        if existing_suggestion:
            flash("Je hebt al een suggestie ingediend.", "info")
            return redirect(url_for("poll_detail"))

        # 3. Verwerk de POST (nieuwe suggestie)
        if request.method == "POST":
            artist_name = (request.form.get("artist_name") or "").strip()
            if not artist_name:
                flash("Geef een artiestnaam op.", "warning")
                return redirect(url_for("suggest"))

            # Nieuwe artiest aanmaken
            a = Artists(Artist_name=artist_name)
            db.session.add(a)
            db.session.commit()

            # Suggestie koppelen aan gebruiker
            s = SuggestionFeedback(artist_id=a.id, user_id=user.id)
            db.session.add(s)
            db.session.commit()

            flash("Bedankt voor je suggestie! 🎵 Je kunt nu stemmen op de poll.", "success")
            return redirect(url_for("poll_detail"))

        return render_template("suggest.html", user=user)



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
            po = Polloption(text=row.name)
            db.session.add(po)
        db.session.commit()

    # ---------- Pollpagina ----------
    @app.get("/poll_detail")
    def poll_detail():
        """
        Toon de poll met top-3 artiesten.
        Genereer pollopties enkel als ze nog niet bestaan.
        """
        if Polloption.query.count() == 0:
            _top3_polloptions()

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
        """
        Toon resultaten van de huidige poll (alleen de drie artiesten uit de poll).
        """
        # Haal enkel de 3 huidige pollopties op
        options = Polloption.query.limit(3).all()
        if not options:
            return render_template("results.html", results=[])

        option_ids = [o.id for o in options]

        # Tel enkel stemmen voor deze 3 pollopties
        counts_rows = (
            db.session.query(VotesFor.polloption_id, func.count())
            .filter(VotesFor.polloption_id.in_(option_ids))
            .group_by(VotesFor.polloption_id)
            .all()
        )

        # Maak mapping polloption_id → aantal stemmen
        total_votes = sum(c for _, c in counts_rows) or 1
        counts_map = {pid: c for pid, c in counts_rows}

        # Bouw resultaatlijst met artiestnaam en percentage
        results_data = []
        for o in options:
            count = counts_map.get(o.id, 0)
            percentage = round((count / total_votes) * 100, 1)
            results_data.append({
                "artist": o.text,
                "percentage": percentage
            })

        # Sorteer op hoogste percentage
        results_data.sort(key=lambda x: x["percentage"], reverse=True)

        return render_template("results.html", results=results_data)

    # ======================================================
    return app



