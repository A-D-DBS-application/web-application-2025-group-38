from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, User, Artists, FestivalEdition, Poll, Polloption, VotesFor, SuggestionFeedback
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    migrate = Migrate(app, db)  
    # 1) Lokaal: maak app.db als hij nog niet bestaat
    #    In Supabase (Postgres) bestaan de tabellen al; create_all() doet dan niets extra.
    with app.app_context():
        db.create_all()

    # 2) "Anonieme user": we geven elke bezoeker een user_id in de sessie
    def get_or_create_session_user():
        uid = session.get("user_id")
        if uid is None:
            u = User()               # lege user aanmaken
            db.session.add(u)
            db.session.commit()
            session["user_id"] = u.id
            return u
        return db.session.get(User, uid)

    # 3) Home: toon edities met hun polls
    @app.route("/")
    def editions():
        eds = FestivalEdition.query.order_by(FestivalEdition.Start_date.desc().nullslast()).all()
        return render_template("editions.html", editions=eds)

    # 4) Poll-detail: toon opties, registreer stem (1 stem per user per poll)
    @app.route("/poll/<int:poll_id>", methods=["GET", "POST"])
    def poll_detail(poll_id):
        poll = db.session.get(Poll, poll_id)
        if not poll:
            flash("Poll niet gevonden", "warning")
            return redirect(url_for("editions"))
        user = get_or_create_session_user()

        if request.method == "POST":
            option_id = int(request.form.get("option_id", "0"))
            option = db.session.get(Polloption, option_id)
            # Veiligheidscheck: optie moet bij deze poll horen
            if not option or option.poll_id != poll.id:
                flash("Ongeldige optie", "danger")
                return redirect(url_for("poll_detail", poll_id=poll.id))

            # Check of user al gestemd heeft in deze poll
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

    # 5) Resultaten: tel stemmen per optie met GROUP BY
    @app.route("/poll/<int:poll_id>/results")
    def poll_results(poll_id):
        poll = db.session.get(Poll, poll_id)
        if not poll:
            flash("Poll niet gevonden", "warning")
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
        return render_template("poll_results.html", poll=poll, total=total, count_map=count_map)

    # 6) Suggesties: simpele form om artiestnamen binnen te sturen
    @app.route("/suggest", methods=["GET", "POST"])
    def suggest():
        if request.method == "POST":
            artist_name = request.form.get("artist_name", "").strip()
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

    return app

# 7) Dit maakt runnen met "python app.py" mogelijk tijdens ontwikkeling
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
