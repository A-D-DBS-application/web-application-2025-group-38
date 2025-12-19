import os
from dotenv import load_dotenv
from supabase import create_client

# Laad .env bestand
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # <-- juiste naam

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase environment variables are not set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
