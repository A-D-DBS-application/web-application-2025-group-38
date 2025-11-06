from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from sqlalchemy import text

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

    # ---------- sessie helpers (schema-vriendelijk) ----------
    def get_session_user():
        uid = session.get("user_id")
        return db.session.get(User, uid) if uid else None

    def login_user(user: User):
        session["user_id"] = user.id

    def logout_user():
        session.pop("user_id", None)

    # ---------- routes ----------
    # ---------- routes ----------

    @app.get("/", endpoint="home")
    def home():
        return render_template("index.html")

    @app.get("/polls", endpoint="editions")
    def editions():
        eds = (FestivalEdition.query
            .order_by(FestivalEdition.Start_date.desc().nullslast())
            .all())
        return render_template("editions.html", editions=eds)


    @app.get("/health")
    def health():
        db.session.execute(text("select 1"))
        return {"status": "ok"}, 200

    @app.route("/suggest", methods=["GET", "POST"])
    def suggest():
        if request.method == "POST":
            artist_name = (request.form.get("artist_name") or "").strip()
            if not artist_name:
                flash("Geef een artiestnaam op.", "warning")
                return redirect(url_for("suggest"))
            a = Artists(Artist_name=artist_name)
            db.session.add(a); db.session.commit()
            s = SuggestionFeedback(artist_id=a.id)
            db.session.add(s); db.session.commit()
            flash("Bedankt voor je suggestie!", "success")
            return redirect(url_for("editions"))
        return render_template("suggest.html")

    # --- eenvoudige registratie: maakt 1 rij in User en bewaart id in sessie ---
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if get_session_user():
            flash("Je bent al aangemeld.", "info")
            return redirect(url_for("editions"))

        if request.method == "POST":
            email = (request.form.get("email") or "").strip()
            user = User.query.filter_by(email=email).first() if email else None
            if not user:
                user = User(email=email or None)
                db.session.add(user); db.session.commit()
            login_user(user)
            flash(f"Aangemeld als user #{user.id}", "success")
            return redirect(url_for("editions"))

        return render_template("register.html")

    @app.get("/logout")
    def logout():
        if get_session_user():
            logout_user()
            flash("Je bent afgemeld.", "info")
        return redirect(url_for("editions"))

    # --- seed: maak één editie 2026 (tijdelijk simpel) ---
    # Wil je toch een mini-beveiliging? Voeg ?token=jouwcode toe en check die hier.
    @app.get("/admin/seed-edition-2026")
    def seed_edition_2026():
        existing = FestivalEdition.query.filter_by(Name="2026").first()
        if existing:
            flash("Editie 2026 bestond al.", "info")
            return redirect(url_for("editions"))

        ed = FestivalEdition(
            Name="2026", Location="Dendermonde",
            Start_date=date(2026, 8, 21), End_date=date(2026, 8, 24)
        )
        db.session.add(ed); db.session.commit()
        flash("Editie 2026 aangemaakt!", "success")
        return redirect(url_for("editions"))

    return app
