from flask import Blueprint, render_template, redirect, url_for, flash
from models import db, FestivalEdition
from app.utils.session import get_session_user

bp = Blueprint("admin_editions", __name__, url_prefix="/admin/editions")


def require_admin():
    """Heel simpele check: alleen ingelogde gebruiker laten doorgaan.
    Als je later een echte admin-flag hebt, kan je dat hier toevoegen."""
    user = get_session_user()
    if not user:
        flash("Je moet ingelogd zijn om deze pagina te bekijken.", "warning")
        return None
    # 👉 hier zou je bv. user.is_admin kunnen checken als je zoiets hebt
    return user


@bp.get("/")
def list_editions():
    user = require_admin()
    if user is None:
        return redirect(url_for("auth.register"))

    editions = FestivalEdition.query.order_by(FestivalEdition.Start_date.desc()).all()
    return render_template("admin_editions.html", editions=editions)


@bp.post("/set-active/<int:edition_id>")
def set_active_edition(edition_id):
    user = require_admin()
    if user is None:
        return redirect(url_for("auth.register"))

    # Alle edities op inactive zetten
    FestivalEdition.query.update({FestivalEdition.is_active: False})

    # De gekozen editie actief maken
    edition = FestivalEdition.query.get_or_404(edition_id)
    edition.is_active = True

    db.session.commit()
    flash(f"Actieve editie is nu: {edition.Name}", "success")
    return redirect(url_for("admin_editions.list_editions"))
