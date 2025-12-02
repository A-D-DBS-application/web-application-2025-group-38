from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models import db, User

from app.utils.session import get_session_user, login_user, logout_user

ADMIN_EMAILS = {"louis@ugent.be", "judith@ugent.be"}

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if get_session_user():
        session.pop("_flashes", None)
        flash("Je bent al ingelogd.", "info")
        return render_template("register.html")

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        user = User.query.filter_by(email=email).first() if email else None

        if not user:
            user = User(email=email or None)
            user.is_admin = email in ADMIN_EMAILS
            db.session.add(user)
            db.session.commit()
        else:
            if email in ADMIN_EMAILS and not user.is_admin:
                user.is_admin = True
                db.session.commit()

        login_user(user)

        session.pop("_flashes", None)
        flash("Succesvol ingelogd!", "info")

        return render_template("register.html")

    return render_template("register.html")


@bp.get("/logout")
def logout():
    if get_session_user():
        logout_user()
        flash("Je bent afgemeld.", "info")
    return redirect(url_for("core.home"))
