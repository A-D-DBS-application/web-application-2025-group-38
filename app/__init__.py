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

    # ---------- sessie helpers ----------
    def get_session_user():
        uid = session.get("user_id")
        return db.session.get(User, uid) if uid else None

    def login_user(user: User):
        session["user_id"] = user.id

    def logout_user():
        session.pop("user_id", None)

    # ---------- basisroutes ----------
    @app.get("/", endpoint="home")
    def home():
        return render_template("index.html")

    @app.get("/polls", endpoint="editions")
    def editions():
        eds = (
            FestivalEdition.query
            .order_by(FestivalEdition.Start_date.desc().nullslast())
            .all()
        )
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
            db.session.add(a)
            db.session.commit()

            s = SuggestionFeedback(artist_id=a.id)
            db.session.add(s)
            db.session.commit()

            flash("Bedankt voor je suggestie!", "success")
            return redirect(url_for("editions"))

        return render_template("suggest.html")

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
                db.session.add(user)
                db.session.commit()
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

    # ---------- Seed editie 2026 ----------
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
            End_date=date(2026, 8, 24)
        )
        db.session.add(ed)
        db.session.commit()

        flash("Editie 2026 aangemaakt!", "success")
        return redirect(url_for("editions"))

    # ======================================================
    # 🎵 POLL SYSTEEM
    # ======================================================

    # Helperfunctie: bereken top 3 artiesten uit suggesties en link aan Polloption
    def _top3_polloptions():
        top = (
            db.session.query(
                Artists.id.label("artist_id"),
                Artists.Artist_name.label("name"),
                func.count(SuggestionFeedback.id).label("cnt"),
            )
            .join(SuggestionFeedback, SuggestionFeedback.artist_id == Artists.id)
            .group_by(Artists.id, Artists.Artist_name)
            .order_by(desc("cnt"))
            .limit(3)
            .all()
        )

        options = []
        for row in top:
            po = Polloption.query.filter_by(text=row.name).first()
            if not po:
                po = Polloption(text=row.name)
                db.session.add(po)
                db.session.commit()
            options.append({"id": po.id, "name": row.name})
        return options

    # --- Pollpagina ---
    @app.get("/poll_detail", endpoint="poll_detail")
    def poll_detail():
        return render_template("poll_detail.html")

    # --- API: alleen top-3 artiesten ---
    @app.get("/api/artists")
    def api_artists():
        top3 = _top3_polloptions()
        return [{"id": x["id"], "Artist_name": x["name"]} for x in top3]

    # --- Stem opslaan ---
    @app.post("/vote")
    def vote():
        polloption_id = request.form.get("artist_id", type=int)
        if not polloption_id:
            flash("Kies eerst een artiest om te stemmen.", "warning")
            return redirect(url_for("poll_detail"))

        allowed_ids = {x["id"] for x in _top3_polloptions()}
        if polloption_id not in allowed_ids:
            flash("Deze optie hoort niet bij de huidige poll.", "danger")
            return redirect(url_for("poll_detail"))

        v = VotesFor(polloption_id=polloption_id, user_id=None)
        db.session.add(v)
        db.session.commit()

        flash("Je stem is opgeslagen! 🎉", "success")
        return redirect(url_for("results"))

    # --- Resultatenpagina ---
    @app.get("/results", endpoint="results")
    def results():
        top3 = _top3_polloptions()
        ids = [x["id"] for x in top3]
        name_map = {x["id"]: x["name"] for x in top3}

        if not ids:
            return render_template("results.html", results=[])

        counts_rows = (
            db.session.query(VotesFor.polloption_id, func.count(VotesFor.polloption_id))
            .filter(VotesFor.polloption_id.in_(ids))
            .group_by(VotesFor.polloption_id)
            .all()
        )

        counts = {pid: cnt for pid, cnt in counts_rows}
        total = sum(counts.values()) or 1

        results_data = []
        for pid in ids:
            c = counts.get(pid, 0)
            results_data.append({
                "artist": name_map.get(pid, "Onbekend"),
                "votes": c,
                "percentage": round((c / total) * 100, 1),
            })

        results_data.sort(key=lambda r: r["votes"], reverse=True)
        return render_template("results.html", results=results_data)

    # ======================================================

    return app
