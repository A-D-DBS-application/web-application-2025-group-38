import os
import time
import requests
import urllib.parse

IMAGE_FOLDER = "app/static/images/artist_images"

ARTISTS = [
    "Arctic Monkeys", "Coldplay", "Imagine Dragons", "Muse", "The Killers",
    "Foo Fighters", "Red Hot Chili Peppers", "Ed Sheeran", "Dua Lipa",
    "Billie Eilish", "Post Malone", "The Weeknd", "Bruno Mars",
    "Calvin Harris", "David Guetta", "Kygo", "Avicii", "Bastille",
    "Sam Smith", "Shawn Mendes", "Harry Styles", "Adele", "Tame Impala",
    "Oasis", "Florence and the Machine",
    "Stromae", "Lost Frequencies",
    "Angèle", "Netsky", "Selah Sue", "Oscar and the Wolf", "Metallica",
    "Linkin Park", "Green Day", "Paramore", "Blink-182", "Twenty One Pilots",
    "Avenged Sevenfold", "The Chainsmokers", "Zedd", "Swedish House Mafia",
    "Maroon 5", "The Script", "Kings of Leon", "Kanye West", "Drake",
    "Eminem", "50 Cent", "Black Eyed Peas"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VicarisVillageBot/1.0)",
    "Referer": "https://en.wikipedia.org/"
}

# 🔹 Handmatige mapping naar de juiste Wikipedia-paginanaam
SPECIAL_TITLES = {
    "Muse": "Muse_(band)",
    "Oasis": "Oasis_(band)",
    "Angèle": "Angèle_(singer)",
    "Netsky": "Netsky_(musician)",
    "Selah Sue": "Selah_Sue",
    "The Chainsmokers": "The_Chainsmokers",
    "Drake": "Drake_(musician)",
    "Sam Smith": "Sam_Smith_(singer)",
    "Shawn Mendes": "Shawn_Mendes",
    "Adele": "Adele",
    "Kygo": "Kygo",
    "Avicii": "Avicii",
}


def wikipedia_image_url(artist):
    """Zoekt een thumbnail via Wikipedia API."""
    # Eerst kijken of we een speciale titel hebben
    if artist in SPECIAL_TITLES:
        wiki_title = SPECIAL_TITLES[artist]
    else:
        # fallback: oude gedrag
        wiki_title = artist.replace("+", " ").replace("&", "and")

    api_url = (
        "https://en.wikipedia.org/w/api.php?"
        f"action=query&titles={urllib.parse.quote(wiki_title)}"
        "&prop=pageimages&format=json&pithumbsize=600"
    )

    response = requests.get(api_url, headers=HEADERS)
    try:
        res = response.json()
    except:
        return None

    pages = res.get("query", {}).get("pages", {})
    for _, page_data in pages.items():
        if "thumbnail" in page_data:
            return page_data["thumbnail"]["source"]

    return None


def download_image(url, filename):
    """Download afbeelding met retry en fallback."""
    for attempt in range(3):
        try:
            img = requests.get(url, headers=HEADERS, timeout=10)
            img.raise_for_status()
            with open(filename, "wb") as f:
                f.write(img.content)

            print(f"✔️ Downloaded: {filename}")
            return
        except Exception as e:
            print(f"⚠️ Retry {attempt+1}/3 failed for {filename}: {e}")
            time.sleep(1)

    print(f"❌ Failed to download {filename}")


def main():
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    for artist in ARTISTS:
        print(f"\n🔍 Zoeken afbeelding voor: {artist}")

        url = wikipedia_image_url(artist)

        if url:
            filename = artist.lower().replace(" ", "_") + ".jpg"
            filepath = os.path.join(IMAGE_FOLDER, filename)
            download_image(url, filepath)
        else:
            print("⚠️ Geen afbeelding gevonden")

        time.sleep(1.2)  # anti rate limit


if __name__ == "__main__":
    main()

