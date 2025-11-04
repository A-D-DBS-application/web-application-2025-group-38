import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres:Team_38_Maspoe@db.pwvyxvgwntypsbyuhkwa.supabase.co:5432/postgres?sslmode=require"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
