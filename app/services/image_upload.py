import uuid
from app.services.supabase_client import supabase

def upload_artist_image(file):
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"

    path = f"artists/{filename}"

    supabase.storage.from_("artist-images").upload(
        path,
        file.read(),
        {"content-type": file.content_type}
    )

    return supabase.storage.from_("artist-images").get_public_url(path)
