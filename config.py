# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    # Gebruik DATABASE_URL uit .env, anders lokaal SQLite-bestand app.db
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR/'app.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
