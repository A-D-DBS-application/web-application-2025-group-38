from flask import Flask
from flask_migrate import Migrate
from config import Config
from models import db, Poll
from app.routes import register_blueprints
from app.services.poll import get_or_create_active_poll
from app.utils.session import get_session_user

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    Migrate(app, db)

    register_context_processors(app)
    register_blueprints(app)
    return app

def register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_current_user():
        return {"current_user": get_session_user()}
    
    @app.context_processor
    def inject_poll_visibility():
        poll = Poll.query.order_by(Poll.id).first()
        return {
            "poll_visibility": poll.is_visible if poll else True,
            "results_visibility": poll.show_results if poll else True,
        }

    @app.before_request
    def ensure_poll_exists():
        get_or_create_active_poll()