from flask import Blueprint

from app.routes import core, auth, suggestions, poll, admin


def register_blueprints(app):
    app.register_blueprint(core.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(suggestions.bp)
    app.register_blueprint(poll.bp)
    app.register_blueprint(admin.bp)


__all__ = [
    "register_blueprints",
    "core",
    "auth",
    "suggestions",
    "poll",
    "admin",
]