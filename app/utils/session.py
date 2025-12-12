from __future__ import annotations

from flask import session

from models import db, User


def get_session_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_user(user: User):
    session["user_id"] = user.id
    session.permanent = False   # 👈 HIER



def logout_user():
    session.pop("user_id", None)