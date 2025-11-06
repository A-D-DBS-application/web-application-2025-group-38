from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, User, Artists, FestivalEdition, Poll, Polloption, VotesFor, SuggestionFeedback
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    migrate = Migrate(app, db)

    # 1️⃣ Maak lokale database als die nog niet bestaat
    with app.app_context():
        db.create_all()

    # 2️⃣ "Anonieme gebruiker": geef elke bezoeker een user_id in de sessie
    def get_or_create_session_user():
        uid = session.get("user_id")
        if uid is None:
            u = User()
            db.session.add(u)
            db.session.commit()
            session["user_id"] = u.id
            return u
        return db.session.get(User, uid)

    # 3️⃣ HOME – landingspagina met hero-afbeelding
    @app.route("/")
    def home():
        """
        Hoofdpagina van Vicaris Village met hero en sfeerbeelden.
        """
        return render_template("index.html")

    # 4️⃣ EDITIONS – toon edities met hun polls
    @app.route("/editions")
    def editions():
        """
        Lijst van festivaledities met beschikbare polls.
        """
        eds = FestivalEdition.query.order_by(
            FestivalEdition.Start_date.desc().nullslast()
        ).all()
        return render_template("editions.html", editions=eds)

    # 5️⃣ POLL DETAIL – stem op een artiest binnen een poll
    @app.route("/poll/<int:poll_id>", methods=["GET", "POST"])
    def poll_detail(poll_id):
        poll = db.session.get(Poll, poll_id)
        if not poll:
            flash("Poll niet gevonden.", "warning")
            return redirect(url_for("editions"))

        user = get_or_create_session_user()

        if request.method == "POST":
            option_id = int(request.form.get("option_id", "0"))
            option = db.session.get(Polloption, option_id)

            # Veiligheidscheck: optie moet bij deze poll horen
            if not option or option.poll_id != poll.id:
                flash("Ongeldige optie.", "danger")
                return redirect(url_for("poll_detail", poll_id=poll.id))

            # Check of gebruiker al gestemd heeft
            already = (
                db.session.query(VotesFor)
                .join(Polloption, VotesFor.polloption_id == Polloption.id)
                .filter(VotesFor.user_id == user.id, Polloption.poll_id == poll.id)
                .first()
            )

            if already:
                flash("Je hebt al gestemd voor deze poll.", "info")
            else:
                db.session.add(VotesFor(user_id=user.id, polloption_id=option.id))
                db.session.commit()
                flash("Stem geregistreerd!", "success")

            return redirect(url_for("poll_results", poll_id=poll.id))

        return render_template("poll_detail.html", poll=poll, options=poll.options)

    # 6️⃣ POLL RESULTATEN – toon resultaten van een poll
    @app.route("/poll/<int:poll_id>/results")
    def poll_results(poll_id):
        poll = db.session.get(Poll, poll_id)
        if not poll:
            flash("Poll niet gevonden.", "warning")
            return redirect(url_for("editions"))

        counts = (
            db.session.query(Polloption.id, db.func.count(VotesFor.user_id))
            .outerjoin(VotesFor, VotesFor.polloption_id == Polloption.id)
            .filter(Polloption.poll_id == poll.id)
            .group_by(Polloption.id)
            .all()
        )

        count_map = {oid: c for oid, c in counts}
        total = sum(count_map.values())

        return render_template(
            "poll_results.html", poll=poll, total=total, count_map=count_map
        )

    # 7️⃣ SUGGESTIE – bestaande of nieuwe artiest insturen
    @app.route("/suggest", methods=["GET", "POST"])
    def suggest():
        all_artists = Artists.query.order_by(Artists.Artist_name.asc()).all()

        if request.method == "POST":
            selected_id = request.form.get("artist_id")
            new_name = request.form.get("artist_name", "").strip()

            # Bestaande artiest
            if selected_id and selected_id != "none":
                artist = db.session.get(Artists, int(selected_id))

            # Nieuwe artiest
            elif new_name:
                artist = Artists(Artist_name=new_name)
                db.session.add(artist)
                db.session.commit()
            else:
                flash("Kies of vul een artiest in.", "warning")
                return redirect(url_for("suggest"))

            # Suggestie opslaan
            feedback = SuggestionFeedback(artist_id=artist.id)
            db.session.add(feedback)
            db.session.commit()

            flash(f"Bedankt voor je suggestie voor {artist.Artist_name}!", "success")
            return redirect(url_for("editions"))

        return render_template("suggest.html", artists=all_artists)

    return app


# 8️⃣ Zorg dat je lokaal kan runnen met: python run.py
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
