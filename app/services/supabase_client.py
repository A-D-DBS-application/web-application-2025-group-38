import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("SUPABASE_URL =", SUPABASE_URL)
    print("SUPABASE_SERVICE_KEY =", SUPABASE_SERVICE_KEY)
    raise RuntimeError("Supabase environment variables are not set")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

