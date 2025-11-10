import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = (
        "postgresql+psycopg2://postgres.pwvyxvgwntypsbyuhkwa:Team_38_Maspoe@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
