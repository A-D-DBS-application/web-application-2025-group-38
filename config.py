# config.py
import os

class Config:
    # Dit haalt de database-URL uit je .env-bestand
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
