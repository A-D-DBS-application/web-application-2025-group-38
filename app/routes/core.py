from flask import Blueprint, render_template
from sqlalchemy import text

from models import db

bp = Blueprint("core", __name__)


@bp.get("/")
def home():
    return render_template("index.html")


@bp.get("/health")
def health():
    db.session.execute(text("select 1"))
    return {"status": "ok"}, 200